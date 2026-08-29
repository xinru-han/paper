"""Build the executable linked market system from the balanced benchmark."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from casm_world.linked_equilibrium import ProcessSpec


PROCESS_OUTPUT_PRODUCTS = frozenset(
    {
        "SBO", "SBM", "NBO", "NBM", "RBO", "RBM", "SUG", "CTN",
        "ETH", "DDG", "BUT", "CHE", "NDM", "FMK", "WDM", "ODA",
    }
)


@dataclass(frozen=True)
class ModelSystem:
    regions: tuple[str, ...]
    products: tuple[str, ...]
    base_primary_supply: np.ndarray
    base_final_demand: np.ndarray
    processes: tuple[ProcessSpec, ...]


def _matrix(
    benchmark: pd.DataFrame,
    regions: tuple[str, ...],
    products: tuple[str, ...],
    column: str,
) -> np.ndarray:
    table = benchmark.pivot(index="economy_id", columns="commodity", values=column)
    table = table.reindex(index=regions, columns=products)
    if table.isna().any().any():
        raise ValueError(f"Benchmark matrix {column} is incomplete")
    values = table.to_numpy(float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError(f"Benchmark matrix {column} has invalid values")
    return values


def build_model_system(
    benchmark: pd.DataFrame,
    activities: pd.DataFrame,
    commodity_config: dict,
    *,
    process_elasticity: float = 0.8,
) -> ModelSystem:
    """Create process technologies that reproduce the balanced 2023 flows."""

    required_benchmark = {
        "economy_id", "commodity", "supply_2023", "final_demand_2023",
        "processing_demand_2023", "demand_2023",
    }
    required_activities = {"economy_id", "process", "balanced_activity_2023"}
    if not required_benchmark <= set(benchmark):
        raise ValueError(f"Missing benchmark fields: {sorted(required_benchmark-set(benchmark))}")
    if not required_activities <= set(activities):
        raise ValueError(f"Missing activity fields: {sorted(required_activities-set(activities))}")
    regions = tuple(sorted(benchmark["economy_id"].astype(str).unique()))
    products = tuple(commodity_config["commodities"].keys())
    if len(benchmark) != len(regions) * len(products):
        raise ValueError("Benchmark must contain one row per region-product")
    product_index = {product: index for index, product in enumerate(products)}
    region_index = {region: index for index, region in enumerate(regions)}
    total_supply = _matrix(benchmark, regions, products, "supply_2023")
    final_demand = _matrix(benchmark, regions, products, "final_demand_2023")
    primary = total_supply.copy()
    for product in PROCESS_OUTPUT_PRODUCTS:
        primary[:, product_index[product]] = 0.0

    activity_table = activities.pivot_table(
        index="economy_id", columns="process", values="balanced_activity_2023", aggfunc="sum"
    ).reindex(index=regions, fill_value=0.0)

    specs: list[ProcessSpec] = []

    def add_fixed_process(
        name: str,
        activity_name: str,
        inputs: dict[str, float],
        outputs: dict[str, float],
    ) -> None:
        base = (
            activity_table[activity_name].fillna(0.0).to_numpy(float)
            if activity_name in activity_table
            else np.zeros(len(regions))
        )
        input_coefficients = np.zeros((len(regions), len(products)))
        output_coefficients = np.zeros_like(input_coefficients)
        for product, coefficient in inputs.items():
            input_coefficients[:, product_index[product]] = float(coefficient)
        for product, coefficient in outputs.items():
            output_coefficients[:, product_index[product]] = float(coefficient)
        specs.append(
            ProcessSpec(
                name=name,
                base_activity=base,
                input_coefficients=input_coefficients,
                output_coefficients=output_coefficients,
                elasticity=np.full(len(regions), float(process_elasticity)),
            )
        )

    systems = commodity_config["processing_systems"]
    for process in ("soybean_crush", "sunflower_crush", "rapeseed_crush"):
        definition = systems[process]
        add_fixed_process(
            process,
            process,
            {definition["input"]: 1.0},
            {key: float(value) for key, value in definition["outputs"].items()},
        )
    sugar = systems["sugar_refining"]
    for input_product, coefficient in sugar["inputs"].items():
        add_fixed_process(
            f"sugar_{input_product}",
            f"sugar_{input_product}",
            {input_product: 1.0},
            {sugar["output"]: float(coefficient)},
        )
    cotton_yield = float(systems["cotton_ginning"]["outputs"]["CTN"])
    add_fixed_process("cotton_ginning", "cotton_ginning", {}, {"CTN": cotton_yield})

    # Biofuel production is an activity without a modelled feedstock in the
    # current 31-product boundary. DDG is nevertheless an exact coproduct.
    ethanol_base = total_supply[:, product_index["ETH"]]
    ethanol_outputs = np.zeros_like(total_supply)
    ethanol_outputs[:, product_index["ETH"]] = 1.0
    ethanol_outputs[:, product_index["DDG"]] = float(
        systems.get("ethanol", {}).get("ddg_output_mass_per_mass_ethanol", 0.75)
    )
    # The coefficient is frozen in balancing.yaml; infer it from the exact
    # balanced quantities so this constructor cannot introduce a second value.
    positive_ethanol = ethanol_base > 0
    ethanol_outputs[positive_ethanol, product_index["DDG"]] = (
        total_supply[positive_ethanol, product_index["DDG"]]
        / ethanol_base[positive_ethanol]
    )
    specs.append(
        ProcessSpec(
            name="ethanol",
            base_activity=ethanol_base,
            input_coefficients=np.zeros_like(total_supply),
            output_coefficients=ethanol_outputs,
            elasticity=np.full(len(regions), float(process_elasticity)),
        )
    )

    # One joint dairy activity consumes raw milk and supplies the observed
    # country-specific product mix. This avoids summing dairy product tonnes as
    # if they were raw-milk tonnes and preserves both solids identities frozen
    # during benchmark balancing.
    dairy_base = (
        activity_table["dairy_milk"].fillna(0.0).to_numpy(float)
        if "dairy_milk" in activity_table
        else np.zeros(len(regions))
    )
    dairy_inputs = np.zeros_like(total_supply)
    dairy_inputs[:, product_index["MLK"]] = 1.0
    dairy_outputs = np.zeros_like(total_supply)
    modelled_dairy_output = total_supply[:, [
        product_index[product] for product in ("BUT", "CHE", "NDM", "FMK", "WDM", "ODA")
    ]].sum(axis=1)
    active_dairy = (dairy_base > 0) & (modelled_dairy_output > 0)
    for product in ("BUT", "CHE", "NDM", "FMK", "WDM", "ODA"):
        dairy_outputs[active_dairy, product_index[product]] = (
            total_supply[active_dairy, product_index[product]] / dairy_base[active_dairy]
        )
    specs.append(
        ProcessSpec(
            name="dairy_solids",
            base_activity=np.where(active_dairy, dairy_base, 0.0),
            input_coefficients=dairy_inputs,
            output_coefficients=dairy_outputs,
            elasticity=np.full(len(regions), float(process_elasticity)),
        )
    )
    # A few small accounts report raw milk but none of the six modelled dairy
    # outputs. Preserve that explicitly as fixed unmodelled dairy use rather
    # than fabricating an output or dropping the milk demand.
    unmodelled_dairy = np.where(active_dairy, 0.0, dairy_base)
    specs.append(
        ProcessSpec(
            name="dairy_unmodelled_use",
            base_activity=unmodelled_dairy,
            input_coefficients=dairy_inputs,
            output_coefficients=np.zeros_like(total_supply),
            elasticity=np.zeros(len(regions)),
        )
    )

    # Exact reproduction is a hard constructor gate.
    process_supply = sum(
        (spec.base_activity[:, None] * spec.output_coefficients for spec in specs),
        start=np.zeros_like(total_supply),
    )
    process_demand = sum(
        (spec.base_activity[:, None] * spec.input_coefficients for spec in specs),
        start=np.zeros_like(total_supply),
    )
    benchmark_process_demand = _matrix(
        benchmark, regions, products, "processing_demand_2023"
    )
    if np.max(np.abs(primary + process_supply - total_supply)) > 1.0e-8:
        raise AssertionError("Process technologies do not reproduce balanced supply")
    if np.max(np.abs(process_demand - benchmark_process_demand)) > 1.0e-8:
        raise AssertionError("Process technologies do not reproduce balanced process demand")
    return ModelSystem(regions, products, primary, final_demand, tuple(specs))
