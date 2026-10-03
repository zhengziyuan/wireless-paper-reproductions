"""Source-derived angular/geometry and physical-bound tests; no figure optimizer."""
import json
from pathlib import Path
import numpy as np
import run
from engine import serialize


def main():
    settings=json.loads((run.HERE/"settings.json").read_text())
    figures=json.loads((run.HERE/"figures.json").read_text())
    maps=json.loads((run.HERE/"figure_map.json").read_text())
    checks={"complete_point_counts_match_source_map":all(len(f["points"])==next(m["point_count"] for m in maps["figures"] if m["id"]==f["id"]) for f in figures)}
    if settings["kind"]=="communications":
        for fid,U in (("fig7",2),("fig8",4)):
            f=next(f for f in figures if f["id"]==fid)
            model=run.make_model(f["points"][0],settings)
            z=run.initialize(model,settings,run.PortableRandom(2))
            samples=run.communication_beampattern_samples(model,serialize(z))
            checks[fid+"_original_user_angles"]=model.config["azimuth_deg"]==[-60.,-20.,20.,60.]
            checks[fid+"_all_angle_pattern_samples"]=np.shape(samples["pattern_snr"])==(361,U)
            checks[fid+"_SNR_upper_bound"]=bool(np.max(samples["pattern_snr"])<=settings["reference_snr"]*model.M**2*(1+1e-12))
    else:
        f=next(f for f in figures if f["id"]=="fig3")
        model=run.make_model(f["points"][0],settings)
        checks["source_marker_azimuth_and_numbering"]=model.config["azimuth_deg"]==[0.,45.,90.,0.,45.,90.,0.,45.,90.]
        checks["source_marker_elevation_and_numbering"]=model.config["elevation_deg"]==[30.,30.,30.,50.,50.,50.,70.,70.,70.]
        z=run.initialize(model,settings,run.PortableRandom(2))
        a=model.fields(z)[3]
        bounds=model.beta[:model.targets]*model.M**4/model.config["noise_over_power"]
        observed=model.metric(z,"sinr")
        checks["unit_modulus_amplitude_triangle_bound"]=bool(np.max(a)<=model.M**2*(1+1e-12))
        checks["quartic_echo_noise_bound"]=bool(np.all(observed<=bounds[:,None]*(1+1e-12)))
        pslr=run.make_model(f["points"][0],settings,pslr=True)
        checks["full_60_by_60_clutter_grid"]=pslr.K-model.targets==3600
        checks["source_rectangular_guard"]=settings["mainlobe_guard_azimuth_deg"]==22.5 and settings["mainlobe_guard_elevation_deg"]==10
        checks["all_other_targets_retained"]=all(set(range(model.targets))-{k} <=set(v) for k,v in enumerate(pslr.config["pslr_opponents"]))
        print(json.dumps({"source_normalization_audit":{
            "scope":"parameter_consistency_audit_not_simulation_curve",
            "fig3_upper_linear":float(bounds[0]),"fig3_upper_db":float(10*np.log10(bounds[0])),
            "fig15_P30_M100_upper_db":float(10*np.log10(10**(settings["reference_echo_db"]/10)*100**4)),
            "reported_fig3_annotation_db":32.02,"reported_fig15_MIS_P30_db_from_EPS_ticks":21.6700,
            "reference_contract":"conditional inverse-W, processing-factor1; units and noise stage not stated by source",
            "bound_formula":"P_W * reference_effective_per_W * M^4",
            "fig3_exceeds_this_explicit_contract":bool(32.02>10*np.log10(bounds[0])),
            "reported_physical_scenario_proven_impossible":False}},indent=2))
    if not all(checks.values()):raise AssertionError(checks)
    print(json.dumps({"scope":"source_input_and_identity_unit_tests_not_full_figure","checks":checks},indent=2))


if __name__=="__main__":main()
