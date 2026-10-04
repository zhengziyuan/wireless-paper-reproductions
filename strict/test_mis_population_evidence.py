"""Synthetic metadata controls only: no optimizers, arrays or MATLAB calls."""
import copy
import unittest

from mis_population_evidence import verify_full_mis_summary_population


def documents():
    status = dict(convergence_verified=True, all_inner_tolerances_satisfied=True,
                  final_inner_stationary=True, continuation_complete=True,
                  inner_iteration_cap_exits=0, inner_failure_exits=0,
                  outer_stopping_applicable=False, outer_stopping_met=True,
                  final_inner_residual=1e-7, final_inner_tolerance=1e-6)
    rows = [dict(start=i, feasible=True, binary_eta_feasible=True, score=1.,
                 min_binary_metric=1., solver_status=copy.deepcopy(status)) for i in range(1, 6001)]
    run = dict(number_of_starts=6000, full_start_budget_execution_complete=True,
               overall_full_success=True, selected_best_convergence_verified=True,
               all_start_summaries=rows,
               best_feasible=dict(start=1, score=1., binary_eta_feasible=True,
                                  solver_status=copy.deepcopy(status),metrics=dict(min_binary_snr=1.)))
    cfg = dict(Kphi=2, Ktheta=2)
    source = dict(objective="communications", baselines=["SMS"], points=[cfg])
    data = dict(paper_id="mis-communications", settings=dict(number_of_starts=6000,kind="communications",rcg_gradient_tolerance=1e-6),
                points=[dict(configuration=cfg, result=run, SMS=copy.deepcopy(run))])
    return data, source


class Population(unittest.TestCase):
    def test_all12000_summary_slots_not_independent_physical_certificate(self):
        data, source = documents()
        result = verify_full_mis_summary_population(data, source)
        self.assertEqual(result["checked_start_summaries"], 12000)
        self.assertFalse(result["independent_endpoint_gradients_or_physical_model_verified"])
        self.assertFalse(result["full_reproduction_certified"])

    def test_selected_best_true_cannot_hide_other_capped_start(self):
        data, source = documents()
        status = data["points"][0]["result"]["all_start_summaries"][5999]["solver_status"]
        status["inner_iteration_cap_exits"] = 1
        status["all_inner_tolerances_satisfied"] = False
        with self.assertRaisesRegex(ValueError, "start6000"):
            verify_full_mis_summary_population(data, source)

    def test_missing_duplicate_boolean_identifiers_and_missing_baseline_rejected(self):
        for mutation in ("missing", "duplicate", "bool", "SMS"):
            with self.subTest(mutation=mutation):
                data, source = documents()
                rows = data["points"][0]["result"]["all_start_summaries"]
                if mutation == "missing": rows.pop()
                elif mutation == "duplicate": rows[-1]["start"] = 1
                elif mutation == "bool": rows[0]["start"] = True
                else: del data["points"][0]["SMS"]
                with self.assertRaises(ValueError): verify_full_mis_summary_population(data, source)

    def test_nonfinite_residual_false_outer_stop_or_inconsistent_best_rejected(self):
        for mutation in ("nan", "residual", "outer", "outer_bool", "best", "missing_status"):
            with self.subTest(mutation=mutation):
                data, source = documents()
                run = data["points"][0]["result"]
                status = run["all_start_summaries"][-1]["solver_status"]
                if mutation == "nan": status["final_inner_residual"] = float("nan")
                elif mutation == "residual": status["final_inner_residual"] = 2e-6
                elif mutation == "outer": status.update(outer_stopping_applicable=True, outer_stopping_met=False)
                elif mutation == "outer_bool": status["outer_stopping_applicable"] = 0
                elif mutation == "best": run["best_feasible"]["score"] = 2.
                else: del status["all_inner_tolerances_satisfied"]
                with self.assertRaises(ValueError): verify_full_mis_summary_population(data, source)

    def test_analytical_panel_does_not_invent_start_population(self):
        source = dict(objective="closed_form_sinr", points=[{}], baselines=[])
        data = dict(paper_id="mis-sensing", points=[dict(configuration={}, result=dict(available=True, minimum_sinr=1.))])
        self.assertEqual(verify_full_mis_summary_population(data, source)["checked_start_summaries"], 0)

    def test_RIS_aggregate_flag_alone_is_not_all_target_evidence(self):
        data, source = documents()
        source["baselines"] = ["RIS_continuous", "RIS_1bit", "RIS_2bit"]
        data["points"][0]["RIS"] = dict(available=True, optimization_convergence_verified=True)
        with self.assertRaisesRegex(ValueError, "RIS aggregate"):
            verify_full_mis_summary_population(data, source)

    def test_missing_closed_form_comparator_rejected(self):
        data, source = documents()
        source["baselines"] = ["closed_form"]
        with self.assertRaisesRegex(ValueError, "closed-form comparator"):
            verify_full_mis_summary_population(data, source)

    def test_nonmaximum_wrong_tie_and_plot_scalar_rejected(self):
        for mutation in ("nonmaximum", "tie", "plot_scalar"):
            with self.subTest(mutation=mutation):
                data, source = documents(); run = data["points"][0]["result"]
                if mutation == "nonmaximum": run["all_start_summaries"][1]["score"] = 2.
                elif mutation == "tie": run["best_feasible"]["start"] = 2
                else: run["best_feasible"]["metrics"]["min_binary_snr"] = 999.
                with self.assertRaises(ValueError): verify_full_mis_summary_population(data, source)

    def test_float_counts_or_relaxed_stored_tolerance_rejected(self):
        for mutation in ("bank_float", "settings_float", "tolerance"):
            with self.subTest(mutation=mutation):
                data, source = documents(); run = data["points"][0]["result"]
                if mutation == "bank_float": run["number_of_starts"] = 6000.
                elif mutation == "settings_float": data["settings"]["number_of_starts"] = 6000.
                else: run["all_start_summaries"][-1]["solver_status"].update(final_inner_tolerance=1.,final_inner_residual=.01)
                with self.assertRaises(ValueError): verify_full_mis_summary_population(data, source)

    def test_sensing_eta_is_not_binary_metric_and_epsilon_schedule_is_bound(self):
        data, source = documents(); source["baselines"] = []
        data["paper_id"] = "mis-sensing"
        data["settings"] = dict(kind="sensing",number_of_starts=6000,outer_iterations=30,
                                rcg_max_iterations=4000,epsilon_initial=.001,epsilon_min=1e-6)
        run = data["points"][0]["result"]
        for row in run["all_start_summaries"]:
            row["min_binary_metric"] = 2.
            row["solver_status"].update(outer_stopping_applicable=True,final_inner_tolerance=.001)
        run["best_feasible"].update(metrics=dict(eta=1.,min_binary_metric=2.),
                                   solver_status=copy.deepcopy(run["all_start_summaries"][0]["solver_status"]))
        self.assertTrue(verify_full_mis_summary_population(data, source)["all_summary_coverage_and_stop_fields_verified"])
        run["all_start_summaries"][-1]["solver_status"]["final_inner_tolerance"] = .002
        with self.assertRaises(ValueError): verify_full_mis_summary_population(data, source)

    def test_analytical_with_numerical_baseline_still_requires_original_population(self):
        for mutation in ("missing", "one", "float"):
            with self.subTest(mutation=mutation):
                data, source = documents(); source.update(objective="closed_form_sinr",baselines=["ralm_reference_n6"])
                data["points"][0]["RALM_reference"] = data["points"][0]["result"]
                data["points"][0]["result"] = dict(available=True,minimum_sinr=1.)
                if mutation == "missing": del data["settings"]["number_of_starts"]
                else: data["settings"]["number_of_starts"] = 1 if mutation == "one" else 6000.
                with self.assertRaisesRegex(ValueError,"Original6000"):
                    verify_full_mis_summary_population(data, source)

    def test_boolean_best_score_and_nonselected_communication_metric_mismatch_rejected(self):
        for mutation in ("bool", "other_metric"):
            with self.subTest(mutation=mutation):
                data, source = documents(); run = data["points"][0]["result"]
                if mutation == "bool": run["best_feasible"]["score"] = True
                else: run["all_start_summaries"][-1]["score"] = .5
                with self.assertRaises(ValueError): verify_full_mis_summary_population(data, source)

    def test_all_RIS_target_scalars_and_continuous_selection_bound(self):
        data, source = documents(); source["baselines"] = ["RIS_continuous", "RIS_1bit", "RIS_2bit"]
        run = data["points"][0]["result"]
        ris = dict(available=True,target_start_banks=[copy.deepcopy(run) for _ in range(4)],
                   continuous=[1.]*4,one_bit=[.5]*4,two_bit=[.8]*4)
        data["points"][0]["RIS"] = ris
        self.assertEqual(verify_full_mis_summary_population(data, source)["checked_start_summaries"],30000)
        for mutation in ("short", "nan", "bool", "continuous"):
            with self.subTest(mutation=mutation):
                candidate = copy.deepcopy(data); bank = candidate["points"][0]["RIS"]
                if mutation == "short": bank["one_bit"] = [.5]
                elif mutation == "nan": bank["two_bit"][-1] = float("nan")
                elif mutation == "bool": bank["one_bit"][-1] = True
                else: bank["continuous"][-1] = 999.
                with self.assertRaises(ValueError): verify_full_mis_summary_population(candidate, source)


if __name__ == "__main__": unittest.main()
