from pathlib import Path

from casm_world.concordance import load_concordance, validate_concordance


ROOT = Path(__file__).resolve().parents[1]
FAOSTAT = Path("/root/data/CASM/casm_world_2050/data/raw/fao")


def test_all_31_commodity_codes_match_model_config():
    concordance = load_concordance(ROOT / "config/commodities.yaml")
    model = __import__("yaml").safe_load(
        (ROOT / "config/model.yaml").read_text(encoding="utf-8")
    )
    assert set(concordance["commodities"]) == set(model["commodities"])


def test_faostat_item_codes_and_processing_mass_balances():
    concordance = load_concordance(ROOT / "config/commodities.yaml")
    report = validate_concordance(concordance, FAOSTAT)
    assert report["commodity_count"] == 31
    assert report["mapping_records_checked"] > 70
    assert report["status"] == "passed"

