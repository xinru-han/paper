"""Exact hurdle integration, household-based province forecasts and elasticities."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import norm

from maidads_hurdle import ConditionalMAIDADS
from test_maidads_hurdle import conditional_monotonicity_bound
from importlib import import_module

fit_module = import_module("03_fit_second_stage")
ROOT = Path(__file__).resolve().parents[1]


class FirstStage:
    def __init__(self, k):
        self.k = k
        self.folder = ROOT / "outputs" / f"stata_stage1_{k}"
        self.df = pd.read_csv(self.folder / "household_predictions.csv", dtype={"household_id": str})
        self.df = self.df.loc[self.df.sample_model.eq(1)].copy().reset_index(drop=True)
        self.df["family_type"] = pd.to_numeric(self.df.family_type).astype(int)
        self.coefs = pd.read_csv(self.folder / "coefficients.csv")
        shape_path = ROOT / "outputs" / f"budget_shape_{k}" / "coefficients.csv"
        if shape_path.exists():
            self.coefs = pd.concat([self.coefs, pd.read_csv(shape_path)], ignore_index=True)
        self.price_weights = self.df[[f"s{i}" for i in range(1, k+1)]].mean().to_numpy()

    def evaluate(self, growth, specification="main", price_log_change=None):
        d = self.df.copy()
        log_growth = np.log(growth)
        dp = np.zeros(self.k) if price_log_change is None else np.asarray(price_log_change)
        d["fs_ln_foodprice"] += self.price_weights @ dp
        for prefix in ("fs", "fr"):
            x = d[f"{prefix}_lninc"].to_numpy() + log_growth
            if prefix == "fr":
                x -= self.price_weights @ dp
            d[f"{prefix}_lninc"] = x
            d[f"{prefix}_lninc2"] = x*x
            for name in list(d.columns):
                if name.startswith(f"{prefix}_family_") and name.endswith("_lninc"):
                    level = int(name.split("_")[2])
                    dummy = d.family_type.eq(level).to_numpy()
                    d[name] = dummy*x
                    d[name+"2"] = dummy*x*x
        for j in range(1, self.k):
            d[f"fs_relp_{j}"] += dp[j-1]-dp[-1]
        n = len(d)

        def xb_and_derivatives(name):
            coef = self.coefs.loc[self.coefs.model.eq(name)]
            xb, dy, prices = np.zeros(n), np.zeros(n), np.zeros((n, self.k))
            for row in coef.itertuples():
                term, b = row.term, row.coefficient
                if term == "_cons":
                    xb += b
                    continue
                xb += b*d[term].to_numpy()
                if term in ("fs_lninc", "fr_lninc"):
                    dy += b
                    if term.startswith("fr"):
                        prices -= b*self.price_weights
                elif term in ("fs_lninc2", "fr_lninc2"):
                    dx = 2*b*d[term[:-1]].to_numpy()
                    dy += dx
                    if term.startswith("fr"):
                        prices -= dx[:, None]*self.price_weights
                elif term.endswith("_lninc") and "_family_" in term:
                    level = int(term.split("_")[2])
                    dx = b*d.family_type.eq(level).to_numpy()
                    dy += dx
                    if term.startswith("fr"):
                        prices -= dx[:, None]*self.price_weights
                elif term.endswith("_lninc2") and "_family_" in term:
                    level = int(term.split("_")[2])
                    prefix = term.split("_")[0]
                    dx = 2*b*d.family_type.eq(level).to_numpy()*d[f"{prefix}_lninc"].to_numpy()
                    dy += dx
                    if term.startswith("fr"):
                        prices -= dx[:, None]*self.price_weights
                elif term == "fs_ln_foodprice":
                    prices += b*self.price_weights
                elif term.startswith("fs_relp_"):
                    j = int(term.split("_")[-1])-1
                    prices[:, j] += b
                    prices[:, -1] -= b
            return xb, dy, prices

        bxb, budget_income, budget_price = xb_and_derivatives("food_budget_"+specification)
        probs, prob_income, prob_price, xbs, xb_ys, xb_prices = [], [], [], [], [], []
        for i in range(1, self.k+1):
            xb, dy, price = xb_and_derivatives(f"participation_g{i}")
            probs.append(ndtr(xb))
            prob_income.append(norm.pdf(xb)*dy)
            prob_price.append(norm.pdf(xb)[:, None]*price)
            xbs.append(xb)
            xb_ys.append(dy)
            xb_prices.append(price)
        p = self.df[[f"p{i}" for i in range(1, self.k+1)]].to_numpy()*np.exp(dp)[None, :]/100.
        return (p, np.exp(bxb)/100., budget_income, budget_price,
                np.clip(np.column_stack(probs), 1e-9, 1-1e-9),
                np.column_stack(prob_income), np.stack(prob_price, axis=1),
                np.column_stack(xbs), np.column_stack(xb_ys), np.stack(xb_prices, axis=1))


def integrate(model, theta, z, first, batch=48, with_prices=True, loadings=None, audit_global=False):
    p, m, emy, emp, prob, prob_y, prob_price, xb, xb_y, xb_price = first
    n, k = p.shape
    sets = ((np.arange(1, 2**k)[:, None] >> np.arange(k)) & 1).astype(bool)
    patterns = len(sets)
    result = {key: np.zeros((n, k)) for key in ("q", "income_intensive", "income_extensive", "food_expenditure", "hicksian_own_fixed_set")}
    result["price_total"] = np.zeros((n, k, k))
    audit = {"patterns": patterns, "households": n, "budget_max_relative_error": 0.,
             "probability_sum_max_error": 0., "income_budget_max_relative_error": 0.,
             "price_budget_max_relative_error": 0., "min_root_eu": float("inf"),
             "participation": "one-factor correlated probit" if loadings is not None else "independent probit",
             "global_monotonicity_bound_max": 0., "global_monotonicity_uncertified_combinations": 0}
    for start in range(0, n, batch):
        stop = min(start+batch, n)
        nb = stop-start
        pp, mm, zz = np.repeat(p[start:stop], patterns, axis=0), np.repeat(m[start:stop], patterns), np.repeat(z[start:stop], patterns, axis=0)
        active = np.tile(sets, (nb, 1))
        pred = model.predict(theta, pp, mm, active, zz)
        q = pred.q.reshape(nb, patterns, k)
        qm = (pred.qu/pred.eu[:, None]).reshape(nb, patterns, k)
        phi = pred.phi.reshape(nb, patterns, k)
        disc = pred.discretionary.reshape(nb, patterns)
        pr = prob[start:stop]
        zero_prob = np.prod(1-pr, axis=1)
        nonempty = 1-zero_prob
        logprob = np.sum(np.where(sets[None, :, :], np.log(pr)[:, None, :], np.log1p(-pr)[:, None, :]), axis=2)
        weights = np.exp(logprob)/nonempty[:, None]
        factor = (sets[None, :, :]-pr[:, None, :])/(pr*(1-pr))[:, None, :]
        normalization_y = zero_prob/nonempty*np.sum(prob_y[start:stop]/(1-pr), axis=1)
        derivative_y_weights = weights*(np.sum(factor*prob_y[start:stop, None, :], axis=2)-normalization_y[:, None])
        derivative_price_weights = None
        if loadings is not None:
            helper = import_module("06_fit_correlated_hurdle")
            weights, derivative_y_weights, derivative_price_weights = helper.joint_pattern_weights(
                xb[start:stop], loadings, sets, dy_xb=xb_y[start:stop],
                price_xb=xb_price[start:stop] if with_prices else None, nodes=32)
        if audit_global:
            certificate = conditional_monotonicity_bound(model, theta, pp, active, zz)
            audit["global_monotonicity_bound_max"] = max(audit["global_monotonicity_bound_max"], float(certificate["bound"].max()))
            audit["global_monotonicity_uncertified_combinations"] += int((~certificate["certified_positive_slope"]).sum())
        expected = np.einsum("nr,nri->ni", weights, q)
        intensity = qm*m[start:stop, None, None]
        extensive = np.einsum("nr,nri->ni", derivative_y_weights, q)
        result["q"][start:stop] = expected
        result["food_expenditure"][start:stop] = np.einsum("nr,nri->ni", weights, intensity)
        result["income_intensive"][start:stop] = result["food_expenditure"][start:stop]*emy[start:stop, None]
        result["income_extensive"][start:stop] = extensive
        hown = disc[:, :, None]*(phi*phi-phi)/p[start:stop, None, :]
        result["hicksian_own_fixed_set"][start:stop] = np.einsum("nr,nri->ni", weights, hown)
        if with_prices:
            normal_price = zero_prob[:, None]/nonempty[:, None]*np.sum(prob_price[start:stop]/(1-pr)[:, :, None], axis=1)
            for j in range(k):
                hresponse = disc[:, :, None]*phi*phi[:, :, j, None]/p[start:stop, None, :]
                hresponse[:, :, j] -= disc*phi[:, :, j]/p[start:stop, j, None]
                mresponse = hresponse-qm*(p[start:stop, j, None]*q[:, :, j])[:, :, None]
                mresponse += intensity*emp[start:stop, j, None, None]
                dw = (weights*(np.sum(factor*prob_price[start:stop, None, :, j], axis=2)-normal_price[:, j, None])
                      if derivative_price_weights is None else derivative_price_weights[:, :, j])
                result["price_total"][start:stop, :, j] = np.einsum("nr,nri->ni", weights, mresponse)+np.einsum("nr,nri->ni", dw, q)
        err = np.max(np.abs(np.sum(p[start:stop]*expected, axis=1)-m[start:stop])/m[start:stop])
        audit["budget_max_relative_error"] = max(audit["budget_max_relative_error"], float(err))
        audit["probability_sum_max_error"] = max(audit["probability_sum_max_error"], float(np.max(np.abs(weights.sum(1)-1))))
        audit["min_root_eu"] = min(audit["min_root_eu"], float(pred.eu.min()))
        dy = result["income_intensive"][start:stop]+extensive
        audit["income_budget_max_relative_error"] = max(audit["income_budget_max_relative_error"], float(np.max(np.abs(np.sum(p[start:stop]*dy, axis=1)-m[start:stop]*emy[start:stop])/m[start:stop])))
        if with_prices:
            paid_derivative = np.einsum("ni,nij->nj", p[start:stop], result["price_total"][start:stop])+p[start:stop]*expected
            audit["price_budget_max_relative_error"] = max(audit["price_budget_max_relative_error"], float(np.max(np.abs(paid_derivative-m[start:stop, None]*emp[start:stop])/m[start:stop, None])))
    return result, audit


def aggregate(df, result, k, growth, spec, names):
    rows = []
    subsets = [("all", "全样本", np.ones(len(df), bool))]
    subsets += [("province", str(name), df.province_name.eq(name).to_numpy()) for name in sorted(df.province_name.unique())]
    subsets += [("family", str(code), df.family_type.eq(code).to_numpy()) for code in sorted(df.family_type.unique())]
    weights = df.hhsize.to_numpy()
    for dimension, name, mask in subsets:
        wt = weights[mask]
        qsum = np.sum(wt[:, None]*result["q"][mask], axis=0)
        total_income = result["income_intensive"]+result["income_extensive"]
        totals = {key: np.sum(wt[:, None]*result[key][mask], axis=0)/qsum
                  for key in ("income_intensive", "income_extensive", "food_expenditure", "hicksian_own_fixed_set")}
        price = np.sum(wt[:, None, None]*result["price_total"][mask], axis=0)/qsum[:, None]
        for i in range(k):
            lo, hi = np.quantile(df.income_pc_month, [.01, .99])
            predicted_value = np.sum(wt*result["q"][mask, i]*df[f"p{i+1}"].to_numpy()[mask])/wt.sum()
            rows.append(dict(goods=k, specification=spec, growth_multiplier=growth, dimension=dimension, stratum=name,
                             group=i+1, group_name=names[i], households=int(mask.sum()), sample_population=float(wt.sum()),
                             mean_income_pc_month=float(np.average(df.income_pc_month.to_numpy()[mask]*growth, weights=wt)),
                             predicted_quantity_pc_month=float(qsum[i]/wt.sum()),
                             predicted_value_pc_month=float(predicted_value),
                             income_outside_baseline_p01_p99_share=float(np.mean((df.income_pc_month.to_numpy()[mask]*growth<lo)|(df.income_pc_month.to_numpy()[mask]*growth>hi))),
                             income_elasticity=float(totals["income_intensive"][i]+totals["income_extensive"][i]),
                             income_intensive=float(totals["income_intensive"][i]),
                             income_extensive=float(totals["income_extensive"][i]),
                             food_expenditure_elasticity=float(totals["food_expenditure"][i]),
                             hicksian_own_fixed_set_average=float(totals["hicksian_own_fixed_set"][i]),
                             total_own_price_response=float(price[i, i]) if np.any(result["price_total"]) else np.nan,
                             inferential_p_value=np.nan, p_value_status="point estimates; full two-stage cluster bootstrap not run"))
    return pd.DataFrame(rows)


def run(k, batch=48):
    first = FirstStage(k)
    df = first.df
    folder = ROOT / "outputs" / f"maidads_{k}"
    fit = json.loads((folder / "maidads_fit.json").read_text())
    model = ConditionalMAIDADS(k, len(fit["family_shift_levels"]), True,
                              expanded_guards=fit.get("expanded_guards",False))
    z = np.column_stack([df.family_type.eq(j).astype(float) for j in fit["family_shift_levels"]])
    theta = np.asarray(fit["theta"])
    descriptives = pd.read_csv(ROOT / "outputs" / "food_group_descriptives.csv")
    names = descriptives.loc[descriptives.system_goods.eq(k)&descriptives["sample"].eq("model")].sort_values("group").group_name.tolist()
    loadings = np.asarray(json.loads((first.folder / "correlated_hurdle_fit.json").read_text())["loadings"])
    tables, audits = [], []
    baseline = None
    for spec, growth in [("main", g) for g in (1., 1.1, 1.25, 1.5, 2.)]+[("income_trim", 1.), ("fooddeflated", 1.), ("loglinear", 1.), ("independent_hurdle", 1.)]:
        print(f"EXACT integration K={k} {spec} income multiplier={growth}", flush=True)
        values = first.evaluate(growth, "main" if spec == "independent_hurdle" else spec)
        result, audit = integrate(model, theta, z, values, batch=batch, with_prices=growth==1.,
                                  loadings=None if spec == "independent_hurdle" else loadings,
                                  audit_global=spec == "main" and growth == 1.)
        audit.update(specification=spec, growth_multiplier=growth)
        audits.append(audit)
        table = aggregate(df, result, k, growth, spec, names)
        tables.append(table)
        if spec == "main" and growth == 1.:
            baseline = result
            cross = np.sum(df.hhsize.to_numpy()[:, None, None]*result["price_total"], axis=0)/np.sum(df.hhsize.to_numpy()[:, None]*result["q"], axis=0)[:, None]
            pd.DataFrame(cross, index=names, columns=names).to_csv(folder / "unconditional_total_price_response_matrix.csv", encoding="utf-8-sig")
        print(f"K={k} scenario done; max budget error={audit['budget_max_relative_error']:.2e}", flush=True)
        pd.concat(tables, ignore_index=True).to_csv(folder / "income_growth_scenarios.csv", index=False, encoding="utf-8-sig")
        (folder / "hurdle_integration_audit.json").write_text(json.dumps(audits, indent=2), encoding="utf-8")
    table = pd.concat(tables, ignore_index=True)
    table.loc[table.specification.eq("main")&table.growth_multiplier.eq(1)].to_csv(folder / "baseline_elasticities.csv", index=False, encoding="utf-8-sig")
    table.loc[table.dimension.eq("province")&table.specification.eq("main")].to_csv(folder / "province_income_growth_predictions.csv", index=False, encoding="utf-8-sig")
    table.loc[table.dimension.eq("family")&table.specification.eq("main")].to_csv(folder / "family_income_growth_elasticities.csv", index=False, encoding="utf-8-sig")
    p = df[[f"p{i}" for i in range(1,k+1)]].to_numpy()/100.
    m = df.food_budget_pc_month.to_numpy()/100.
    active = df[[f"d{i}" for i in range(1,k+1)]].to_numpy().astype(bool)
    pred, eta, mar, h = model.responses(theta, p, m, active, z)
    weightedq = pred.q*df.hhsize.to_numpy()[:, None]
    denominator = weightedq.sum(0)
    fixed = pd.DataFrame(dict(group=np.arange(1,k+1), group_name=names,
                              food_expenditure_elasticity=np.nansum(weightedq*eta, axis=0)/denominator,
                              marshallian_own=np.nansum(weightedq*np.diagonal(mar, axis1=1, axis2=2), axis=0)/denominator,
                              hicksian_own=np.nansum(weightedq*np.diagonal(h, axis1=1, axis2=2), axis=0)/denominator))
    fixed.to_csv(folder / "conditional_fixed_set_elasticities.csv", index=False, encoding="utf-8-sig")
    for label, matrix in (("marshallian", mar), ("hicksian", h)):
        averaged = np.nansum(weightedq[:, :, None]*matrix, axis=0)/denominator[:, None]
        pd.DataFrame(averaged, index=names, columns=names).to_csv(folder / f"conditional_{label}_matrix.csv", encoding="utf-8-sig")
    distribution = []
    for j in range(k):
        ey = (baseline["income_intensive"][:, j]+baseline["income_extensive"][:, j])/baseline["q"][:, j]
        for name, vals in (("unconditional_income", ey), ("conditional_food_expenditure", eta[:, j]),
                           ("conditional_hicksian_own", h[:, j, j])):
            vals = vals[np.isfinite(vals)]
            for percentile, value in zip((1, 10, 25, 50, 75, 90, 99), np.percentile(vals, (1,10,25,50,75,90,99))):
                distribution.append(dict(group=j+1, group_name=names[j], elasticity=name, percentile=percentile, value=float(value), N=len(vals)))
    pd.DataFrame(distribution).to_csv(folder / "household_elasticity_distribution.csv", index=False, encoding="utf-8-sig")
    # Validate the complete two-margin income derivative, not only the kernel.
    small = np.arange(min(12,len(df)))
    selected_z = z[small]
    def sub(x):
        return tuple(v[small] for v in x)
    minus, _ = integrate(model, theta, selected_z, sub(first.evaluate(np.exp(-1e-4))), batch=12, with_prices=False, loadings=loadings)
    plus, _ = integrate(model, theta, selected_z, sub(first.evaluate(np.exp(1e-4))), batch=12, with_prices=False, loadings=loadings)
    fd = (plus["q"]-minus["q"])/2e-4
    analytic = baseline["income_intensive"][small]+baseline["income_extensive"][small]
    derivative_audit = {"income_derivative_max_scaled_error":float(np.max(np.abs(fd-analytic)/np.maximum(baseline["q"][small],1e-8))),
                        "households_tested":len(small), "step":1e-4, "integration":"all 2^K-1 nonempty sets, no simulation"}
    price_errors = []
    for j in range(k):
        change = np.zeros(k)
        change[j] = 1e-4
        minus, _ = integrate(model, theta, selected_z[:3], tuple(v[:3] for v in first.evaluate(1.,price_log_change=-change)),
                             batch=3,with_prices=False,loadings=loadings)
        plus, _ = integrate(model, theta, selected_z[:3], tuple(v[:3] for v in first.evaluate(1.,price_log_change=change)),
                            batch=3,with_prices=False,loadings=loadings)
        fdprice = (plus["q"]-minus["q"])/2e-4
        price_errors.append(float(np.max(np.abs(fdprice-baseline["price_total"][:3,:,j])/np.maximum(baseline["q"][:3],1e-8))))
    derivative_audit["price_derivative_max_scaled_error"] = max(price_errors)
    derivative_audit["price_derivative_errors_by_price"] = price_errors
    if max(derivative_audit["income_derivative_max_scaled_error"], max(price_errors)) > 1e-6:
        raise RuntimeError("Full hurdle income or price derivative failed finite differences")
    (folder / "forecast_derivative_validation.json").write_text(json.dumps(derivative_audit, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--goods", type=int, choices=[8,10], required=True)
    parser.add_argument("--batch", type=int, default=48)
    args = parser.parse_args()
    run(args.goods, args.batch)
