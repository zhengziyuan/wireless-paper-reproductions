function result=strict_hotspot_no_ris_init_test(fixturePath,configPath,outputPath,executeFullQT)
% Independent original-model feasible-start proof; optional complete original QT.
% No reference ordinates, changed constraints or replacement optimizer.
if nargin<4,executeFullQT=false;end
f=load(fixturePath);config=jsondecode(fileread(configPath));t=config.tuned_not_reported;U=size(f.Q,1);records=cell(1,U);baseline=strict_hotspot_statistical('evaluate',f.Q,f.Psi,f.W0,f.noise);
for u=1:U
    W=f.(['candidate_',num2str(u-1)]);e=strict_hotspot_statistical('evaluate',f.Q,f.Psi,W,f.noise);primal=max([0,e.total_power/f.power-1,max(f.target(:)-e.sinr(U+1:end))]);
    record=struct('selected_HU',u-1,'candidate_evaluation',e,'physical_violation',primal, ...
        'physical_feasibility_pass',primal<1e-5,'original_initialization_rate',baseline.hu_sum_rate, ...
        'same_model_higher_feasible_objective_pass',e.hu_sum_rate>baseline.hu_sum_rate,'executed_full_original_QT',executeFullQT);
    if executeFullQT
        [w,h,stop,diagnostics]=strict_hotspot_statistical('qt_loop',f.Q,f.Psi,W,f.noise,f.power,f.target,t);
        record.actual_status=strict_hotspot_termination('scheme',{stop},diagnostics,t);record.original_QT_history=h;
        record.original_QT_evaluation=strict_hotspot_statistical('evaluate',f.Q,f.Psi,w,f.noise);
    end
    records{u}=record;
end
if executeFullQT
    [w,h,stop,diagnostics]=strict_hotspot_statistical('qt_loop',f.Q,f.Psi,f.W0,f.noise,f.power,f.target,t);
    baselineFinal=struct('evaluation',strict_hotspot_statistical('evaluate',f.Q,f.Psi,w,f.noise),'history',h, ...
        'actual_status',strict_hotspot_termination('scheme',{stop},diagnostics,t));
else,baselineFinal=[];end
checks=struct('all_same_model_feasible_candidates_pass',all(cellfun(@(x)x.physical_feasibility_pass,records)), ...
    'higher_feasible_objective_exists_pass',any(cellfun(@(x)x.same_model_higher_feasible_objective_pass,records)));
if executeFullQT,checks.actual_complete_QT_stops_pass=baselineFinal.actual_status.algorithm_success&&all(cellfun(@(x)x.actual_status.algorithm_success,records));end
result=struct('scope','independent_same_original_QT_feasible_start_basin_diagnosis_NOT_figures','checks',checks, ...
    'cases',{records},'original_symmetric_final',baselineFinal,'all_passed',all(structfun(@(x)x,checks)), ...
    'reference_ordinates_used',false,'full_reproduction_pass',false);
if nargin>2,folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
assert(result.all_passed,'Independent same-model initialization proof failed');
end
