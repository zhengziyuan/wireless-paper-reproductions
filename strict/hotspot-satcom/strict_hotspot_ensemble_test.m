function result=strict_hotspot_ensemble_test(fixturePath,outputPath)
% Independent all-user/full-rank initialization proof and exact phase schedule.
f=load(fixturePath);cases={};
for U=1:6
    for noRIS=0:1
        x=f.(sprintf('case_U%d_noRIS%d',U,noRIS));schedule=strict_hotspot_ensemble('phases',x.phi0,x.seed,U);phaseError=0;beamError=0;proofs=cell(1,U+1);
        for id=0:U
            phaseError=max(phaseError,max(abs(schedule{id+1}(:)-x.phase_schedule(id+1,:).')));
            [W,proof]=strict_hotspot_ensemble('initialize',x.Q,x.Psi,x.W0,x.noise,x.power,x.target,id);
            reference=x.(sprintf('W_start%d',id));beamError=max(beamError,max(abs(W(:)-reference(:))));proofs{id+1}=proof;
        end
        cases{end+1}=struct('U',U,'no_ris',logical(noRIS),'phase_schedule_max_error',phaseError,'initial_beam_max_error',beamError, ...
            'all_initial_feasibility_pass',all(cellfun(@(p)p.physical_feasibility_pass,proofs)), ...
            'all_passed',phaseError<1e-13&&beamError<1e-10&&all(cellfun(@(p)p.physical_feasibility_pass,proofs))); %#ok<AGROW>
    end
end
gates=struct('physical_constraint_pass',true,'convergence_pass',true,'solver_primal_pass',true,'qt_sdr_bound_pass',true);
rows={struct('start_id',0,'executed',true,'checks',gates,'evaluation',struct('hu_sum_rate',1)), ...
    struct('start_id',1,'executed',true,'checks',gates,'evaluation',struct('hu_sum_rate',8)), ...
    struct('start_id',2,'executed',true,'checks',gates,'evaluation',struct('hu_sum_rate',3))};
[good,selected]=strict_hotspot_ensemble('summarize',rows,0:2);goodSelection=good.all_required_starts_pass&&selected.start_id==1;
[missing,~]=strict_hotspot_ensemble('summarize',rows(1:2),0:2);rows{3}.checks.convergence_pass=false;
[capped,selected]=strict_hotspot_ensemble('summarize',rows,0:2);capReject=~capped.all_required_starts_pass&&selected.start_id==1;
rows{2}.checks.qt_sdr_bound_pass=false;[badBound,selected]=strict_hotspot_ensemble('summarize',rows,0:2);boundReject=~badBound.all_required_starts_pass&&selected.start_id==0;
checks=struct('all_full_dimension_initializations_pass',all(cellfun(@(c)c.all_passed,cases)), ...
    'best_complete_selection_pass',goodSelection,'missing_start_rejected',~missing.all_required_starts_pass, ...
    'selected_good_start_cannot_certify_cap_pass',capReject,'bad_bound_start_rejected',boundReject);
result=struct('scope','full_dimension_declared_initial_ensemble_component_NOT_algorithm_stops_or_figures', ...
    'cases',{cases},'checks',checks,'all_passed',all(structfun(@(x)x,checks)),'full_reproduction_pass',false,'reference_ordinates_used',false);
folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));
assert(result.all_passed,'Independent ensemble proof or phase parity failed');
end
