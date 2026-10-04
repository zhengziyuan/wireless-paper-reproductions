"""Render model-evaluated MIS outputs, refusing incomplete or reference-only data.

PNG/SVG and a provenance receipt are written together. Display cropping changes
neither computed samples nor physical scenarios. No curve is fabricated to fill
a missing point. Original-figure agreement remains a separate comparison gate.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mis_population_evidence import verify_full_mis_summary_population

HERE = Path(__file__).resolve().parent


def finite(values):
    array = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError("Nonfinite numerical samples are not plot-ready")
    return array


def db(values):
    values = finite(values)
    if np.any(values <= 0):
        raise ValueError("Nonpositive log ordinate; no undisclosed floor")
    return 10 * np.log10(values)


def best(entry, key="result"):
    run = entry[key]
    result = run.get("best_feasible")
    if result is None:
        raise ValueError("Missing feasible optimized result; do not replace it with a reference")
    return result


def save(fig, folder, basename):
    fig.savefig(folder / (basename + ".png"), dpi=180)
    fig.savefig(folder / (basename + ".svg"))
    plt.close(fig)


def render_sensing_beams(data, folder):
    points = data["points"]
    if len(points) != 1:
        raise ValueError("Beampattern source requires one complete original configuration")
    samples = points[0]["beampattern_samples"]
    az, el = finite(samples["azimuth_deg"]), finite(samples["elevation_deg"])
    panels = samples["maps"]
    if len(panels) != 9:
        raise ValueError("Original figure requires all nine target panels")
    fig, axes = plt.subplots(3, 3, figsize=(12.5, 9.8), constrained_layout=True)
    scalars = []
    for index, (ax, panel) in enumerate(zip(axes.flat, panels)):
        values = finite(panel["normalized_gain"])
        if values.shape != (len(el), len(az)) or panel["target"] != index:
            raise ValueError("Target order or full beampattern grid mismatch")
        # Original display uses a -35dB color limit; data remain unmodified.
        handle = ax.pcolormesh(az, el, 10*np.log10(np.maximum(values, 1e-300)),
                               shading="auto", cmap="viridis", vmin=-35, vmax=0, rasterized=True)
        ta, te = panel["target_azimuth_deg"], panel["target_elevation_deg"]
        ax.scatter([ta], [te], marker="x", s=60, c="white", linewidths=1.7)
        metric = float(db(panel["target_metric"]))
        ax.set(xlim=(-15, 105), ylim=(20, 80), xticks=[0, 45, 90], yticks=[30, 50, 70],
               xlabel="Azimuth (degrees)", ylabel="Elevation (degrees)",
               title=f"Target {index+1}: {panel['target_metric_name']} {metric:.2f} dB")
        scalars.append({"target": index+1, "azimuth_deg": ta, "elevation_deg": te,
                        "metric": panel["target_metric_name"], "metric_db": metric})
    fig.colorbar(handle, ax=list(axes.flat), label="Normalized gain (dB)", shrink=.75)
    fig.suptitle(f"{data['figure']} · independent full-size calculation · reference agreement NOT verified", fontsize=12)
    save(fig, folder, data["figure"])
    return {"kind": "nine_beampattern_panels", "target_metrics": scalars,
            "computed_grid": [len(el), len(az)], "display_crop_only": [-15, 105, 20, 80],
            "color_display_limits_db": [-35, 0], "simulation_samples_modified": False}


def sensing_curves(data):
    number = int(data["figure"].removeprefix("fig"))
    groups = {}
    def add(label, x, y):
        groups.setdefault(label, []).append((float(x), float(y)))
    for entry in data["points"]:
        cfg, run = entry["configuration"], entry["result"]
        if number in (7, 8, 15):
            x = cfg["power_dbm"]
        elif number in (9, 10, 11, 12):
            x = cfg["ms1"][0]
        elif number in (13,14):
            # The original four groups share Kphi=2..7 display positions.
            # Tick labels express Kphi*Ktheta; different Ktheta groups must
            # not be shifted to unrelated x positions.
            x = cfg["Kphi"]
        else:
            x = cfg["Kphi"] * cfg["Ktheta"]
        if number in (15, 16):
            add("MIS", x, db(best(entry)["metrics"]["min_binary_metric"]))
            for source, label in (("one_bit", "RIS 1-bit"), ("two_bit", "RIS 2-bit"), ("continuous", "RIS continuous")):
                add(label, x, db(np.min(entry["RIS"][source])))
        elif number in (7, 8, 11, 12):
            label = f"N={cfg['ms2'][0]}"
            y = run["minimum_sinr"] if number == 8 else best(entry)["metrics"]["min_binary_metric"]
            add(label, x, db(y))
            if number == 8 and cfg["ms2"][0] == 6:
                add("RALM N=6", x, db(best(entry, "RALM_reference")["metrics"]["min_binary_metric"]))
        elif number in (9, 10):
            label = f"gap={cfg['gap']}"
            y = run["minimum_sinr"] if number == 10 else best(entry)["metrics"]["min_binary_metric"]
            add(label, x, db(y))
            if number == 10 and cfg["gap"] == 4:
                add("RALM gap=4", x, db(best(entry, "RALM_reference")["metrics"]["min_binary_metric"]))
        elif number in (13, 14):
            label = f"N={cfg['ms2'][0]}, Ktheta={cfg['Ktheta']}"
            y = run["minimum_sinr"] if number == 14 else best(entry)["metrics"]["min_binary_metric"]
            add(label, x, db(y))
            if number == 14 and cfg["ms2"][0] == 16 and cfg["Ktheta"] == 3:
                add("RALM N=16, Ktheta=3", x, db(best(entry, "RALM_reference")["metrics"]["min_binary_metric"]))
        else:
            raise ValueError("Use the same Fig3 full initialization bank for convergence Figs5/6; do not rerun/select a different best start")
    curves = []
    for label, pairs in groups.items():
        pairs.sort()
        if len(set(x for x,y in pairs)) != len(pairs):
            raise ValueError("Duplicate curve abscissas")
        curves.append({"label": label, "x": [x for x,y in pairs], "y": [y for x,y in pairs]})
    return curves


def render_curves(curves, folder, basename, xlabel, ylabel, reference=None):
    fig, ax = plt.subplots(figsize=(7, 4.8), constrained_layout=True)
    for curve in curves:
        ax.plot(finite(curve["x"]), finite(curve["y"]), "o-", label=curve["label"])
    if reference:
        for curve in reference["curves"]:
            ax.plot(finite(curve["x"]), finite(curve["y"]), "--", alpha=.65,
                    label="Original reference: " + curve["label"])
    ax.set(xlabel=xlabel, ylabel=ylabel, title="Independent calculation · original agreement NOT certified")
    ax.grid(True, alpha=.25)
    ax.legend(fontsize=8)
    save(fig, folder, basename)


def render_communications(data, folder):
    """All original curve/pattern configurations; no reference-driven values."""
    number=int(data['figure'][3:]);entries=data['points']
    if number in (7,8):
        entry=entries[0];samples=entry['beampattern_samples'];sms=entry['SMS']['beampattern_samples']
        az=finite(samples['azimuth_deg']);values=finite(samples['pattern_snr'])
        expected=(np.prod(entry['configuration']['ms1'])-np.prod(entry['configuration']['ms2'])+1)
        # These two specific cases use N1 and U=M. General geometric counts
        # remain the simulation's explicit number_of_patterns.
        if values.shape!=(len(az),int(expected)) or samples['number_of_patterns']!=expected:
            raise ValueError('Missing original case-study patterns')
        if sms['azimuth_deg']!=samples['azimuth_deg'] or np.shape(sms['pattern_snr'])!=(len(az),1):
            raise ValueError('SMS original angular cut mismatch')
        fig,ax=plt.subplots(figsize=(7.4,5),constrained_layout=True)
        lines=[]
        for u in range(values.shape[1]):lines.append(ax.plot(az,values[:,u],label=f'MIS pattern {u+1}')[0])
        ax.plot(az,finite(sms['pattern_snr'])[:,0],'k--',label='SMS')
        user_angles=samples['user_azimuth_deg'];schedule=samples['user_pattern'];user_values=finite(samples['user_snr_by_pattern'])
        if len(user_angles)!=entry['configuration']['K'] or user_values.shape!=(len(user_angles),values.shape[1]):
            raise ValueError('Incomplete scheduled user values')
        for k,(a,u) in enumerate(zip(user_angles,schedule)):
            ax.scatter([a],[user_values[k,u]],color=lines[u].get_color(),s=42,zorder=4)
        ax.set(xlabel='Azimuth (degrees)',ylabel='SNR (linear)',xlim=(-90,90),
               title='Complete optimizer bank · original agreement not yet certified')
        ax.grid(alpha=.25);ax.legend(fontsize=8);save(fig,folder,data['figure'])
        return {'kind':'all_original_case_study_patterns','patterns':values.shape[1],
                'angle_samples':len(az),'source_correction_id':entry['configuration'].get('source_correction_id')}
    if number==9:
        fig,axes=plt.subplots(3,3,figsize=(12.2,10),constrained_layout=True)
        for ax,(side,K) in zip(axes.flat,((s,k) for s in (6,8,10) for k in (8,16,32))):
            selected=[e for e in entries if e['configuration']['ms1']==[side,side] and e['configuration']['K']==K]
            matrix=np.full((side,side),np.nan)
            for entry in selected:
                nr,nc=entry['configuration']['ms2']
                value=best(entry)['metrics']['min_binary_snr']/best(entry,'SMS')['metrics']['min_binary_snr']
                if not np.isnan(matrix[nr-1,nc-1]):raise ValueError('Duplicate original geometry')
                matrix[nr-1,nc-1]=value
            finite(matrix)
            handle=ax.imshow(matrix,origin='lower',extent=(.5,side+.5,.5,side+.5),aspect='equal')
            ax.set(xlabel='MS2 columns',ylabel='MS2 rows',title=f'MS1 {side}×{side}; K={K}')
            fig.colorbar(handle,ax=ax,label='Worst SNR / SMS (linear ratio)',shrink=.75)
        fig.suptitle('Complete original geometries · reference agreement not certified',fontsize=12)
        save(fig,folder,data['figure']);return {'kind':'nine_full_geometry_heatmaps','panels':9}
    if number==10:
        fig,axes=plt.subplots(1,3,figsize=(15,4.8),constrained_layout=True);allcurves=[]
        for ax,total in zip(axes,(64,100,144)):
            for K in (8,16,32):
                for scheme in (1,2):
                    selected=sorted((e for e in entries if e['configuration']['total']==total and e['configuration']['K']==K
                        and e['configuration']['scheme']==scheme),key=lambda e:np.prod(e['configuration']['ms2']))
                    label=f'K={K}, scheme{scheme}'
                    curve={'label':f'Total{total} '+label,'x':[float(np.prod(e['configuration']['ms2'])) for e in selected],
                           'y':[best(e)['metrics']['min_binary_snr'] for e in selected]}
                    allcurves.append(curve);ax.plot(finite(curve['x']),finite(curve['y']),'o-',label=label)
            ax.set(xlabel='MS2 element count',ylabel='Worst SNR (linear)',title=f'Total M+N={total}')
            ax.grid(alpha=.25);ax.legend(fontsize=7)
        save(fig,folder,data['figure']);return {'kind':'three_allocation_panels','curves':allcurves}
    if number==11:
        curves=[]
        for shape,movable in (([1,64],[1,n]) for n in (36,16,4)):
            selected=sorted((e for e in entries if e['configuration']['ms1']==shape and e['configuration']['ms2']==movable),key=lambda e:e['configuration']['K'])
            curves.append({'label':f'MIS {shape}, MS2 {movable}','x':[e['configuration']['K'] for e in selected],
                           'y':[best(e)['metrics']['min_binary_snr'] for e in selected]})
        for n in (6,4,2):
            selected=sorted((e for e in entries if e['configuration']['ms1']==[8,8] and e['configuration']['ms2']==[n,n]),key=lambda e:e['configuration']['K'])
            curves.append({'label':f'MIS 8×8, MS2 {n}×{n}','x':[e['configuration']['K'] for e in selected],
                           'y':[best(e)['metrics']['min_binary_snr'] for e in selected]})
        # All independently executed SMS banks are displayed, not silently
        # averaged/picked from three different local minima as one reference.
        for curve,shape,movable in zip(curves,([1,64],[1,64],[1,64],[8,8],[8,8],[8,8]),([1,36],[1,16],[1,4],[6,6],[4,4],[2,2])):
            selected=sorted((e for e in entries if e['configuration']['ms1']==shape and e['configuration']['ms2']==movable),key=lambda e:e['configuration']['K'])
            curves.append({'label':f'SMS independent bank for {curve["label"]}','x':[e['configuration']['K'] for e in selected],
                           'y':[best(e,'SMS')['metrics']['min_binary_snr'] for e in selected]})
        x=sorted({e['configuration']['K'] for e in entries})
        curves.append({'label':'Dynamic RIS analytic bound','x':x,'y':[data['settings']['reference_snr']*64**2]*len(x)})
        render_curves(curves,folder,data['figure'],'Number of users K','Worst SNR (linear)')
        return {'kind':'all_user_sweep_curves','curves':curves,
                'SMS_replication_note':'All six actual baseline banks shown; source has two SMS families, agreement/aggregation still requires validation.'}
    raise ValueError('Unknown communication figure')


def render_sensing_convergence(data,folder,number):
    run=data['points'][0]['result']
    if run['number_of_starts']!=6000 or run.get('mean_outer_counts')!=[6000]*30:
        raise ValueError('Convergence means require all6000 starts of the exact same Fig3 bank')
    history=best(data['points'][0])['history'];values=[]
    for index in range(30):
        step=history[min(index,len(history)-1)]
        values.append(float(step['eta']) if number==5 else max(0,float(np.max(step['q']))))
    average=run['mean_outer_eta' if number==5 else 'mean_outer_violation']
    curves=[{'label':'Best final feasible initialization','x':list(range(1,31)),'y':values},
            {'label':'Mean of the same6000 initializations','x':list(range(1,31)),'y':finite(average).tolist()}]
    if number==5:render_curves(curves,folder,f'fig{number}','Outer iteration','Epigraph eta (linear)')
    else:
        fig,ax=plt.subplots(figsize=(7,4.8),constrained_layout=True)
        for curve in curves:
            y=finite(curve['y']);line=ax.semilogy(curve['x'],np.ma.masked_less_equal(y,0),'o-',label=curve['label'])[0]
            zeros=y==0
            if np.any(zeros):ax.scatter(np.array(curve['x'])[zeros],np.full(np.sum(zeros),1e-12),marker='v',color=line.get_color(),label='Exact zero (display at1e-12)')
        ax.set(xlabel='Outer iteration',ylabel='Maximum positive constraint residual',title='Same complete Fig3 bank · no different best per iteration')
        ax.grid(alpha=.25);ax.legend(fontsize=8);save(fig,folder,f'fig{number}')
    return {'kind':'same_bank_convergence','curves':curves,'terminated_starts_held_at_actual_final_state':True,
            'zero_display_floor':1e-12 if number==6 else None,'stored_residuals_modified':False}


def render(source, output, reference_path=None, figure=None):
    source, output = Path(source), Path(output)
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    if figure is not None:
        if data.get('paper_id')!='mis-sensing' or data.get('figure')!='fig3' or figure not in (5,6):
            raise ValueError('Only sensing Figs5/6 can reuse the exact original Fig3 bank')
        data=dict(data,figure=f'fig{figure}',source_figure='fig3')
    if data.get("scope") not in ("full_size_full_budget_independent_reimplementation", "independent_simulation_curves"):
        raise ValueError("Partial starts, components and references cannot be rendered as full original figures")
    if (data.get("paper_id") in ("mis-sensing", "mis-communications")
            and data.get("scope") != "full_size_full_budget_independent_reimplementation"):
        raise ValueError("MIS figures require the original complete population; generic curve scope cannot bypass this gate")
    summary_population = None
    if data.get("scope") != "independent_simulation_curves":
        mapping = json.loads((HERE / data["paper_id"] / "figure_map.json").read_text(encoding="utf-8-sig"))
        specification = next(x for x in mapping["figures"] if x["id"] == data["figure"])
        if len(data["points"]) != specification["point_count"] or data.get("full_figure_execution_complete") is not True:
            raise ValueError("Missing original figure configurations/full execution receipt; refusing partial plot")
        inventory=json.loads((HERE/data['paper_id']/'figures.json').read_text(encoding='utf-8-sig'))
        expected=next(item['points'] for item in inventory if item['id']==data.get('source_figure',data['figure']))
        actual=[item['configuration'] for item in data['points']]
        key=lambda item:json.dumps(item,sort_keys=True,separators=(',',':'))
        if Counter(map(key,actual))!=Counter(map(key,expected)):
            raise ValueError('Duplicate, changed or missing original figure configurations; count alone is insufficient')
        source_figure=next(item for item in inventory if item['id']==data.get('source_figure',data['figure']))
        summary_population=verify_full_mis_summary_population(data,source_figure)
    output.mkdir(parents=True, exist_ok=True)
    if data["paper_id"] == "mis-sensing" and data["figure"] in ("fig2", "fig3", "fig4"):
        result = render_sensing_beams(data, output)
    elif data['paper_id']=='mis-sensing' and data['figure'] in ('fig5','fig6'):
        result=render_sensing_convergence(data,output,int(data['figure'][3:]))
    elif data["paper_id"] == "mis-sensing":
        curves = sensing_curves(data)
        document = {"paper_id": data["paper_id"], "figure": int(data["figure"][3:]),
                    "data_kind": "independent_simulation_curves", "curves": curves,
                    "full_execution_verified": bool(data.get("overall_full_success")),
                    "source_result_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        (output / "curves.json").write_text(json.dumps(document, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        reference = json.loads(Path(reference_path).read_text(encoding="utf-8-sig")) if reference_path else None
        render_curves(curves, output, data["figure"], specification["x"], "SINR/PSLR (dB)", reference)
        result = {"kind": "multi_curve", "curve_count": len(curves)}
    elif data['paper_id']=='mis-communications':
        result=render_communications(data,output)
    elif data.get("data_kind") == "independent_simulation_curves":
        render_curves(data["curves"], output, "figure", data["x_label"], data["y_label"])
        result = {"kind": "multi_curve", "curve_count": len(data["curves"])}
    else:
        raise ValueError("Renderer is not yet implemented for this source schema; no placeholder plot")
    result.update(paper_id=data["paper_id"], figure=data["figure"], source_result_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  full_figure_execution_complete=bool(data.get("full_figure_execution_complete", False)),
                  overall_full_success=bool(data.get("overall_full_success", False)),
                  original_figure_reproduction_certified=False)
    if summary_population is not None:
        result['complete_start_summary_population_evidence']=summary_population
    (output / "render_receipt.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument('--figure',type=int,choices=[5,6],help='Reuse an actual complete sensing Fig3 bank for convergence')
    args = parser.parse_args()
    print(json.dumps(render(args.result, args.output_dir, args.reference,args.figure)))
