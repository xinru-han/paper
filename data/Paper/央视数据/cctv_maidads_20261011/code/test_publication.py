"""Check publication boundaries without copying household data."""
import csv
from pathlib import Path
import unittest

from publish_aggregates import ROOT, approved


class PublicationTests(unittest.TestCase):
    def test_private_artifacts_rejected(self):
        names=[
            'data/scenario_inputs_8.dta',
            'outputs/scenarios/cell_scenarios.csv',
            'outputs/corner/smd_actual_support.csv',
            'outputs/scenarios_simplex/cohort_mean/predictions.csv',
            'outputs/scenarios_simplex/pooled_micro/predictions.dta',
            'outputs/estimation/maidads_8_coarse_simplex_multistart/predictions.csv',
            'outputs/scope_audit/frozen_training_box.dta',
            'logs/06_predict.log',
            'outputs/data_audit/category_external_prices_observed.csv',
            'outputs/unreviewed_experiment/model_summary.csv',
        ]
        for name in names:
            with self.subTest(name=name): self.assertFalse(approved(ROOT/name))

    def test_new_aggregates_allowed(self):
        for name in [
            'outputs/scenarios_simplex/cohort_mean/coverage.csv',
            'outputs/scenarios_simplex/pooled_micro/province_income_growth.csv',
            'outputs/scenarios_simplex/elderly_micro/family_income_growth.csv',
            'outputs/corner_freephi/full_holdout_prediction_metrics.csv',
            'outputs/scope_audit/frozen_training_box.csv',
            'outputs/data_audit/simplex_own_price_components.csv',
            'outputs/validation_simplex/all_model_metrics.csv',
            'outputs/validation/all_fold_metrics.csv',
        ]:
            with self.subTest(name=name): self.assertTrue(approved(ROOT/name))

    def test_actual_public_csv_headers(self):
        forbidden={'hh_id','household_id','household_code','hhid','user_id','consumer_id'}
        for path in ROOT.rglob('*.csv'):
            if not approved(path): continue
            with path.open(encoding='utf-8-sig',newline='') as handle:
                header={x.strip().lower() for x in next(csv.reader(handle),[])}
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertFalse(header & forbidden)

    def test_consolidated_latest_results(self):
        text=(ROOT/'outputs/ALL_MAIN_RESULTS.txt').read_text(encoding='utf-8')
        for marker in [
            'simplex_own_price_components.csv',
            'corner_freephi/full_holdout_prediction_metrics.csv',
            'scope_audit/frozen_training_box.csv',
            'scenarios_simplex/cohort_mean/province_income_growth.csv',
            'scenarios_simplex/pooled_micro/coverage.csv',
            'maidads_8_coarse_simplex_multistart/representative_price_elasticities.csv',
        ]:
            with self.subTest(marker=marker): self.assertIn(marker,text)
        self.assertNotIn('--- outputs/scenarios_simplex/cohort_mean/predictions.csv',text)
        self.assertNotIn('--- outputs/corner/smd_actual_support.csv',text)


if __name__=='__main__': unittest.main()
