#!/usr/bin/env python3
"""
Create publication-quality choropleth maps of out-of-home consumption coefficients.

This script is intentionally standalone because this environment cannot run the
full pipeline. Run it locally after you have the prediction outputs.

Expected inputs:
  1) A China provinces GeoJSON/Shapefile with a province code field matching GB/T 2260
     (e.g., 11, 12, ..., 65). You must supply this file.
  2) Model predictions at province-year level, e.g.:
       - predictions_tabpfn.csv  (baseline point estimates)
       - predictions_tabpfn_bootstrap.csv (optional; uncertainty bands)

Outputs:
  - figures/map_rice_pork_2024.pdf (two-panel map used by the LaTeX draft)

Usage (example):
  python plot_choropleth_maps.py --geo china_provinces.geojson --pred predictions_tabpfn.csv --year 2024
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--geo", required=True, help="Path to China provinces GeoJSON/Shapefile")
    p.add_argument("--pred", required=True, help="Path to predictions_*.csv (province-year coefficients)")
    p.add_argument("--year", type=int, default=2024, help="Year to map (default: 2024)")
    p.add_argument("--out", default="figures/map_rice_pork_2024.pdf", help="Output PDF path")
    p.add_argument("--province_field", default="Province", help="Province code field name in predictions CSV")
    p.add_argument("--geo_province_field", default="adcode", help="Province code field name in Geo file")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    try:
        import geopandas as gpd
    except Exception as e:
        raise SystemExit(
            "This script requires geopandas. Install with: pip install geopandas pyogrio matplotlib seaborn"
        ) from e

    geo_path = Path(args.geo)
    pred_path = Path(args.pred)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(geo_path)
    df = pd.read_csv(pred_path)

    df = df.copy()
    df[args.province_field] = df[args.province_field].astype(int)
    df["Year"] = df["Year"].astype(int)
    df = df[df["Year"] == args.year]

    # Column names follow the project convention in predictions_*.csv
    needed = {args.province_field, "q_daogu", "q_zhurou"}
    missing = needed - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns in {pred_path.name}: {sorted(missing)}")

    gdf = gdf.copy()
    gdf[args.geo_province_field] = gdf[args.geo_province_field].astype(int)
    gdf = gdf.merge(
        df[[args.province_field, "q_daogu", "q_zhurou"]].rename(columns={args.province_field: args.geo_province_field}),
        on=args.geo_province_field,
        how="left",
    )

    import matplotlib.pyplot as plt
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.0))
    cmap = "viridis"

    # Use the same scale across panels for readability
    vmin = float(pd.concat([gdf["q_daogu"], gdf["q_zhurou"]]).min(skipna=True))
    vmax = float(pd.concat([gdf["q_daogu"], gdf["q_zhurou"]]).max(skipna=True))

    gdf.plot(column="q_daogu", ax=axes[0], cmap=cmap, vmin=vmin, vmax=vmax, linewidth=0.2, edgecolor="white")
    axes[0].set_title(f"Rice coefficient ({args.year})")
    axes[0].axis("off")

    gdf.plot(column="q_zhurou", ax=axes[1], cmap=cmap, vmin=vmin, vmax=vmax, linewidth=0.2, edgecolor="white")
    axes[1].set_title(f"Pork coefficient ({args.year})")
    axes[1].axis("off")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm._A = []
    cbar = fig.colorbar(sm, ax=axes, fraction=0.035, pad=0.02)
    cbar.set_label("Out-of-home consumption coefficient")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()

