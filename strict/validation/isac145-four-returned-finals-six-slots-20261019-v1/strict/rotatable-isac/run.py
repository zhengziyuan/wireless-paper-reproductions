from __future__ import annotations
import argparse
import copy
import json
import time
from pathlib import Path
import numpy as np
from core import channels,evaluate,initialize,update_w,update_theta,update_rotation,optimize


def coordinates(shape,wavelength):
    rows,cols=shape
    return [[(a-(rows-1)/2)*wavelength/2,(b-(cols-1)/2)*wavelength/2,0] for b in range(cols) for a in range(rows)]


def directions(azimuth,elevation):
    return np.stack([np.cos(elevation)*np.cos(azimuth),np.cos(elevation)*np.sin(azimuth),np.sin(elevation)],axis=-1)


def build_scenario(config,k,b,power=1.,rho=10.,bs_shape=None,rng=None,component=False):
    c=copy.deepcopy(config);rng=np.random.default_rng(config["seed"]) if rng is None else rng
    c.update(bs_coordinates=coordinates(bs_shape or config["bs_shape"],config["wavelength"]),
             ris_coordinates=coordinates(config["ris_shape"],config["wavelength"]),
             noise=[config["noise_power"]]*k,power=power,rho=rho,directivity_exponent=b,maximum_gain=2*(b+1))
    paths=config["paths_per_link"]
    def ds(shape):
        if component:
            count=int(np.prod(shape));az=np.linspace(-1.1,1.2,count).reshape(shape);el=np.linspace(.3,.7,count).reshape(shape)
        else:
            az=rng.uniform(-np.pi,np.pi,shape);el=rng.uniform(-np.pi/3,np.pi/3,shape)
        return directions(az,el).tolist()
    for key in ["bu_directions","ru_directions"]:c[key]=ds((k,paths))
    for key in ["br_directions","rb_directions"]:c[key]=ds((paths,))
    for key,shape in [("bu",(k,paths)),("ru",(k,paths)),("br",(paths,))]:
        if component:
            j=np.arange(int(np.prod(shape))).reshape(shape)+1
            real=.3*np.cos(j);imag=.3*np.sin(j*.7)
        else:
            real=rng.normal(size=shape)*np.sqrt(config["path_gain_variance_each"]/2)
            imag=rng.normal(size=shape)*np.sqrt(config["path_gain_variance_each"]/2)
        c[key+"_gain_re"]=real.tolist();c[key+"_gain_im"]=imag.tolist()
    az=np.linspace(-np.pi,np.pi,c["sensing_azimuth_points"]);el=np.linspace(-np.pi/4,np.pi/4,c["sensing_elevation_points"])
    # MATLAB meshgrid(:): elevations vary fastest, then azimuths.
    azg=np.repeat(az,len(el));elg=np.tile(el,len(az));target=directions(azg,elg)
    c["bt_directions"]=target.tolist();c["rt_directions"]=target.tolist()
    desired=np.zeros(len(target))
    for a0,a1,e0,e1 in np.deg2rad(config["desired_sectors_degrees"]):
        desired[(azg>=a0-1e-14)&(azg<=a1+1e-14)&(elg>=e0-1e-14)&(elg<=e1+1e-14)]=1
    c["desired_pattern"]=desired.tolist()
    return c


def component_test(config):
    c=build_scenario(config,2,2,component=True)
    w,theta,r=initialize(c);metric,(gw,gt,gr)=evaluate(w,theta,r,c,None,True);iota=metric["iota"]
    eps=1e-6;numr=np.zeros(6)
    numw=np.zeros_like(w)
    for a in range(w.shape[0]):
        for d in range(w.shape[1]):
            plus,minus=w.copy(),w.copy();plus[a,d]+=eps;minus[a,d]-=eps
            real=(evaluate(plus,theta,r,c,iota)["utility"]-evaluate(minus,theta,r,c,iota)["utility"])/(2*eps)
            plus,minus=w.copy(),w.copy();plus[a,d]+=1j*eps;minus[a,d]-=1j*eps
            imag=(evaluate(plus,theta,r,c,iota)["utility"]-evaluate(minus,theta,r,c,iota)["utility"])/(2*eps)
            numw[a,d]=real+1j*imag
    for d in range(6):
        plus,minus=r.copy(),r.copy();plus[d]+=eps;minus[d]-=eps
        numr[d]=(evaluate(w,theta,plus,c,iota)["utility"]-evaluate(w,theta,minus,c,iota)["utility"])/(2*eps)
    numtheta=np.zeros(len(theta))
    phasegradient=np.real(np.conj(gt)*(1j*theta))
    for d in range(len(theta)):
        plus,minus=theta.copy(),theta.copy();plus[d]*=np.exp(1j*eps);minus[d]*=np.exp(-1j*eps)
        numtheta[d]=(evaluate(w,plus,r,c,iota)["utility"]-evaluate(w,minus,r,c,iota)["utility"])/(2*eps)
    # One actual original QT/MM update and one actual original RCG/PGA block;
    # component caps are explicit tests, not full-run configuration changes.
    test=copy.deepcopy(c)
    test["W_solver"]["maximum_iterations"]=1;test["RCG_solver"]["maximum_iterations"]=2;test["PGA_solver"]["maximum_iterations"]=3
    neww,hw=update_w(w,theta,r,test,iota);newtheta,ht=update_theta(w,theta,r,test,iota)
    probe=copy.deepcopy(test);probe["RCG_solver"]["mode"]="literal_printed"
    printed_rcg_failure=None
    try: update_theta(w,theta,r,probe,iota)
    except RuntimeError as error: printed_rcg_failure=str(error)
    bound=np.ones(6)*np.pi/2
    printed=copy.deepcopy(test);printed["PGA_solver"]["BB_interpretation"]="as_printed"
    printed_r,hp=update_rotation(w,theta,r,printed,iota,-bound,bound)
    corrected=copy.deepcopy(test);corrected["PGA_solver"]["BB_interpretation"]="ascent_sign_correction"
    corrected_r,hc=update_rotation(w,theta,r,corrected,iota,-bound,bound)
    pd=np.asarray(c["desired_pattern"]);pattern=metric["pattern"]
    checks={"rotation_gradient_error":float(np.max(abs(gr-numr))),"RIS_gradient_error":float(np.max(abs(phasegradient-numtheta))),
            "W_gradient_error":float(np.max(abs(gw-numw))),
            "gradient_pass":bool(max(np.max(abs(gr-numr)),np.max(abs(phasegradient-numtheta)),np.max(abs(gw-numw)))<1e-5),
            "QT_MM_non_decrease":bool(hw["objective"][-1]>=hw["objective"][0]-1e-8),
            "power_feasible":bool(np.sum(abs(neww)**2)<=c["power"]+1e-10),
            "RCG_unit_modulus_error":float(np.max(abs(abs(newtheta)-1))),
            "NMSE_identity_error":float(abs(metric["nmse"]-(1-(pd@pattern)**2/((pd@pd)*(pattern@pattern))))),
            "full_model_BS_count":len(w),"full_model_RIS_count":len(theta),"full_model_sensing_grid":len(pattern),
            "printed_BB_negative_denominator_observed":bool(any(v["denominator"]<0 for v in hp["BB"])),
            "printed_RCG_non_ascent_diagnostic":printed_rcg_failure,
            "finite":bool(np.all(np.isfinite(neww)))}
    assert checks["gradient_pass"] and checks["QT_MM_non_decrease"] and checks["power_feasible"]
    assert checks["RCG_unit_modulus_error"]<1e-12 and checks["NMSE_identity_error"]<1e-12
    return {"paper_id":"rotatable-isac","mode":"component_test_not_full_run",
            "metrics":{"initial":{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in metric.items()},
                       "printed_BB_rotation":printed_r.tolist(),"corrected_BB_rotation":corrected_r.tolist()},
            "checks":checks,"history":{"W":hw,"RIS":ht,"PGA_printed":hp,"PGA_correction_diagnostic":hc}}


def run_scenario(c,rotation_half_width=np.pi/2):
    results={};histories={};checks={}
    for name,bs,ris,with_ris in [("Rot-BS & Rot-RIS",True,True,True),("Rot-BS & Fix-RIS",True,False,True),
            ("Fix-BS & Rot-RIS",False,True,True),("Fix-BS & Fix-RIS",False,False,True),
            ("Rot-BS & No-RIS",True,False,False),("Fix-BS & No-RIS",False,False,False)]:
        scene=copy.deepcopy(c)
        if not with_ris:scene["br_gain_re"]=[0.]*len(c["br_gain_re"]);scene["br_gain_im"]=[0.]*len(c["br_gain_im"])
        bs_width=c.get("rotation_bs_half_width",c.get("rotation_half_width",rotation_half_width))
        ris_width=c.get("rotation_ris_half_width",c.get("rotation_half_width",rotation_half_width))
        widths=np.r_[np.ones(3)*bs_width*bs,np.ones(3)*ris_width*ris]
        try:
            w,theta,r,history=optimize(scene,-widths,widths,with_ris)
            metric=evaluate(w,theta,r,scene)
            results[name]={key:value.tolist() if isinstance(value,np.ndarray) else value for key,value in metric.items()}
            results[name].update(w_re=w.real.tolist(),w_im=w.imag.tolist(),theta_re=theta.real.tolist(),theta_im=theta.imag.tolist(),rotation=r.tolist())
            checks[name]={"status":"executed","converged":history["converged"],"inner_all_converged":history["inner_all_converged"],"full_converged":history["full_converged"],"power_feasible":bool(np.sum(abs(w)**2)<=c["power"]+c["verification_tolerance"]),
                          "unit_modulus_error":float(np.max(abs(abs(theta)-1))),"rotation_feasible":bool(np.all(abs(r)<=widths+1e-12))}
            histories[name]=history
        except (RuntimeError,ValueError) as error:
            results[name]={"status":"failed","error":str(error)};checks[name]={"status":"failed"}
    return {"paper_id":"rotatable-isac","mode":"full_scenario","metrics":results,"checks":checks,"history":histories}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--config",type=Path,default=Path(__file__).with_name("full_config.json"))
    p.add_argument("--component-test",action="store_true");p.add_argument("--scenario",type=Path)
    p.add_argument("--output",type=Path,required=True);args=p.parse_args();config=json.loads(args.config.read_text())
    start=time.perf_counter()
    if args.component_test:result=component_test(config)
    elif args.scenario:
        result=run_scenario(json.loads(args.scenario.read_text()))
        from isac_metadata import fingerprint
        result["input_fingerprint"]=fingerprint(args.config.read_bytes(),args.scenario.read_bytes())
    else:p.error("Choose --component-test or an exported full --scenario.")
    result["elapsed_seconds"]=time.perf_counter()-start
    from isac_metadata import implementation_fingerprint
    result["implementation_fingerprint"]=implementation_fingerprint()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n");print(json.dumps({"mode":result["mode"],"checks":result["checks"]}))
