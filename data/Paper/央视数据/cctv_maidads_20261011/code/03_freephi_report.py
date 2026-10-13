"""Render only aggregate Stata outputs; no estimation or household exports."""
from pathlib import Path
import csv
import math

ROOT = Path("/root/data/Paper/央视数据/cctv_maidads_20261011")
OUT = ROOT / "outputs" / "corner_freephi"
FOOD = {1: "主食及加工品", 2: "油脂", 3: "蔬菜", 4: "水果", 5: "猪肉", 6: "其他肉", 7: "水产品", 8: "奶类"}
FAMILY = {1: "年轻家庭", 2: "成年家庭", 3: "老年家庭", 4: "青少年家庭"}


def read(name):
    with (OUT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value):
    if value is None or value == "":
        return math.nan
    return float(value)


def fmt(value, digits=4):
    value = number(value) if isinstance(value, str) else value
    return f"{value:.{digits}f}" if math.isfinite(value) else "未定义"


def table(headers, rows):
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
        *["| " + " | ".join(map(str, row)) + " |" for row in rows],
    ])


def build():
    status = read("fit_status.csv")[0]
    converged = int(number(status["converged"]))
    scale = number(status["budget_scale"])
    lines = [
        "# 有限域、可变预算份额角点扩展：独立试验结果",
        "",
        "## 研究定位",
        "",
        "本结果使用央视购买记录，不使用农户调查。保留各类别零购买，条件于覆盖食品总购买预算为正、季度有三个月记录。数量为参考价格购买量当量，不是实物公斤或摄入量。",
        "",
        "这是单独的 MAIDADS-type 扩展，不覆盖或替换主目录的原始 MAIDADS、AIDADS 或 alpha=beta 角点结果。alpha 与 beta 可不同；共同递减位移、有限数量域及显式端点比率上限保障效用排序。没有 Cholesky 处理、观察值加小常数、逐食品符号筛选或 bootstrap。",
        "",
        "**本候选尚未通过优化收敛，以下是诊断点，不能当作正式主结果或用来宣称模型优胜。**" if not converged else "优化器满足当前停止条件，但仍是消费支持点估计；数值停止不等于全局最优或充分识别。",
        "",
        f"原始参数数 {int(number(status['parameter_count']))}；训练支持点 {int(number(status['training_support_rows']))}；时间外支持点 {int(number(status['holdout_support_rows']))}；拟合使用 {int(number(status['draws']))} 个固定积分抽样。不是全样本估计。目标函数 {fmt(status['objective'], 8)}。",
        "",
        "未计算最终弹性的标准误、p 值或置信区间；没有把它们填为零。模拟积分不是 bootstrap。",
        "",
        "## 支持点误差",
        "",
    ]
    full = {int(number(row["train"])): row for row in read("full_eligible_sample_moments.csv")}
    support = {int(number(row["train"])): row for row in read("support_sample_moments.csv")}
    lines.append(table(["样本", "实际家庭季度", "支持点", "实际预算均值", "支持点加权预算均值", "相对偏差"], [
        ["2020-2021 训练" if train else "2022 时间外", int(number(full[train]["n"])), int(number(support[train]["support_rows"])),
         fmt(full[train]["m"], 2), fmt(support[train]["m"], 2),
         f"{100 * (number(support[train]['m']) / number(full[train]['m']) - 1):.2f}%"]
        for train in (1, 0)
    ]))
    lines += ["", "支持点来自每个省份、家庭类型、收入档的 8 个实际预算分位点；权重恢复各层人数，但并不完整恢复预算和参与分布。", "", "## 全部 2022 记录检验", ""]
    metrics = read("full_holdout_prediction_metrics.csv")
    names = {0: "本扩展诊断点", -1: "训练全样本常数均值", -2: "训练省份及季度历史均值"}
    lines.append(table(["预测器", "2022 家庭季度", "成功预测", "份额 RMSE", "参与 Brier"], [
        [names[int(number(row["model_code"]))], int(number(row["household_quarters"])), int(number(row["covered_household_quarters"])),
         fmt(math.sqrt(sum(number(row[f"share_rmse{j}"]) ** 2 for j in range(1, 8)) / 7)),
         fmt(sum(number(row[f"participation_brier{j}"]) for j in range(1, 9)) / 8)]
        for row in metrics
    ]))
    lines += ["", "该诊断点的份额 RMSE 和参与 Brier 均未优于训练均值及省份季度历史基线。因此不能把端点放松或支持点增加解释为已解决经验预测问题。", "", "此处对所有符合条件的 2022 家庭季度预测，不是只检验支持点。预算和价格作为给定输入；这是条件需求预测，不是预测未来总食物预算。份额损失是相同 7 个独立方程的等权合并。", ""]
    fit = read("full_holdout_fit.csv")
    lines.append(table(["食品", "实际购买率", "模型购买率"], [
        [FOOD[j], f"{100 * number(fit[0][f'positive{j}']):.2f}%", f"{100 * number(fit[1][f'positive{j}']):.2f}%"]
        for j in range(1, 9)
    ]))
    lines += ["", "## 完整自价格及支出响应", "", f"共同参考预算 {scale:.4f} 元/月/人口区间代理；价格是训练支持点的加权参考价格。不同类型在相同预算和价格下比较。积分使用 4096 个匹配的固定偏好抽样，价格和预算为 +/-2.5% 有限扰动响应，不冒称精确导数。", ""]
    prices = read("price_response_all_4_families.csv")
    own = {(int(number(row["type"])), int(number(row["good"]))): row for row in prices if number(row["good"]) == number(row["price_good"])}
    budgets = read("budget_response_curve_all_4_families.csv")
    atbase = {(int(number(row["type"])), int(number(row["good"]))): row for row in budgets if abs(number(row["budget_percap_proxy_month"]) - scale) < 1e-8 * max(1, scale)}
    for family in range(1, 5):
        lines += [f"### {FAMILY[family]}", "", table(["食品", "Marshallian 自价格", "Hicksian 自价格", "总购买量支出", "购买概率支出", "正购买均量支出"], [
            [FOOD[j], fmt(own[family, j]["marshall_total"]), fmt(own[family, j]["hicks_total"]), fmt(atbase[family, j]["budget_total"]),
             fmt(atbase[family, j]["budget_participation"]), fmt(atbase[family, j]["budget_conditional"])]
            for j in range(1, 9)
        ]), ""]
    lines += [
        "补偿响应对每一个偏好抽样分别保持效用不变，之后再平均数量。不是把平均数量代入 Slutsky 公式。全 4 类家庭的 8x8 价格响应及其参与/条件正购买分解在对应 CSV 中。预算曲线覆盖参考预算的 0.25、0.5、1、2、4 倍；不是收入增长曲线，不得混称收入弹性。",
        "",
        "Hicksian 自价格非正来自所声明有限域内的效用及预算结构，不是独立的原始数据检验。固定效用的位移对数形式也保留补偿总替代限制，不能宣称允许任意食品互补关系。不同家庭是调查的年龄形态分类，不是核家庭/扩展家庭。",
        "",
        "## 数学与识别诊断",
        "",
    ]
    certificates = read("regularity_certificate.csv")
    lines.append(table(["家庭类型", "所有偏好抽样的 F_u 上界", "负 0.1 裕量通过"], [
        [FAMILY[int(number(row["family_type"]))], fmt(row["Fu_uniform_upper_bound"]), int(number(row["margin_certified"]))]
        for row in certificates
    ]))
    rank = read("moment_rank_diagnostic.csv")[0]
    lines += ["", f"有限积分、有限扰动的矩条件雅可比秩 {int(number(rank['numerical_rank']))}/{int(number(rank['parameter_count']))}；条件数 {number(rank['condition_number']):.6g}。这是模拟目标函数的局部敏感度，不是总体识别证明或可直接使用的 Wald 推断。", "", "消费集合检验包含全部 255 个非空集合；边界之外不宣称排序或理论有效。数量域、最低价格和最大预算见 regularity_domain.csv。效用位移是参数，不是把正数加到原始零购买数据中。", "", "支出外生性仍为条件假设，没有声称解决无工具变量下的内生性。外部价格代理、人口区间代理、支持点误差和有限积分误差均未因此消失。未证明首次创新。", "", "证明与复现命令见 docs/FREEPHI_FINITE_DOMAIN.md。"]
    (OUT / "RESULTS_FREEPHI_CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
