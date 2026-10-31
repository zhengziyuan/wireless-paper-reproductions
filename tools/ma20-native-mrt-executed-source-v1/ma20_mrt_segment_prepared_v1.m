function summary=ma20_mrt_segment_prepared_v1(jobPath,configPath,eventsPath,priorState)
% Prepared, not an admission or a standalone scientific run.
% A parent guard must pin all inputs and sources, own a single-writer lease,
% establish the prior committed state and enforce the external resource limits.
% The input bank is read in place; no previous output is overwritten.
outputRoot=getenv('MA20_NATIVE_OUTPUT_ROOT');assert(~isempty(outputRoot) && startsWith(string(eventsPath),string(outputRoot)),'Output must remain under selected output root.');
assert(~isfile(eventsPath),'Fresh immutable event file required.');
job=jsondecode(fileread(jobPath));config=jsondecode(fileread(configPath));
assert(job.figure==20 && job.point==3 && job.realization==0 && job.N==6 && job.M==5);
assert(job.kappa==100 && job.power==1 && job.A==2 && job.brute_force_D==3);
assert(config.maximum_AO_iterations==10000 && config.nlos_realizations_per_geometry==1000);
assert(size(job.nlos_re,1)==1000 && isequal(size(job.nlos_re),size(job.nlos_im)));
assert(all(isfinite(job.nlos_re(:))) && all(isfinite(job.nlos_im(:))));
[c,t,~]=ma20_original_components_exposed_prepared_v1('context',job,config);
if nargin<4 || isempty(priorState)
    state=struct('schema','MA20_NATIVE_MRT_SEGMENT_STATE_V1','t',t,'sweep',0,'antenna',0,...
        'sweep_start',ma20_original_components_exposed_prepared_v1('mrt_value',t,c),...
        'updates',0,'done',false,'original_converged_flag',false,'termination','pending');
else
    state=priorState;
    assert(strcmp(state.schema,'MA20_NATIVE_MRT_SEGMENT_STATE_V1') && ~state.done);
    assert(state.sweep>=0 && state.sweep<10000 && state.antenna>=0 && state.antenna<job.N);
    assert(state.updates==state.sweep*job.N+state.antenna && isequal(size(state.t),[job.N,2]));
    assert(all(isfinite(state.t(:))) && isfinite(state.sweep_start));
end
% Reserve room for a complete event before starting its coordinate. Should an
% unexpectedly large event occur, retain it separately instead of truncating.
limitBytes=64*1024; eventReserve=16*1024; maxOverflow=128*1024; used=0;
while ~state.done && state.sweep<config.maximum_AO_iterations
    if used+eventReserve>limitBytes,break;end
    inputState=state;
    [state.t,record]=ma20_original_components_exposed_prepared_v1('coordinate',state.t,c,state.antenna+1,'MRT');
    record.sweep=state.sweep;record.antenna=state.antenna;
    state.antenna=state.antenna+1;state.updates=state.updates+1;
    if state.antenna==job.N
        value=ma20_original_components_exposed_prepared_v1('mrt_value',state.t,c);
        relative=(value-state.sweep_start)/abs(state.sweep_start);
        state.sweep=state.sweep+1;state.antenna=0;state.sweep_start=value;
        % This is the unchanged original native helper's stopping predicate.
        if relative<config.fractional_increase_threshold
            state.done=true;state.original_converged_flag=true;state.termination='fractional_increase';
        elseif state.sweep==config.maximum_AO_iterations
            state.done=true;state.termination='configured_iteration_cap';
        end
    else
        relative=[];
    end
    event=struct('schema','MA20_NATIVE_MRT_COORDINATE_EVENT_V1','input',inputState,...
        'record',record,'output',state,'sweep_relative_change',relative);
    line=[unicode2native(jsonencode(event),'UTF-8'),uint8(10)];
    if numel(line)>eventReserve
        assert(numel(line)<=maxOverflow,'Unexpected event exceeds retention bound.');
        output=[eventsPath,'.overflow'];assert(~isfile(output));
        fid=fopen(output,'wb');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));
        assert(fwrite(fid,line,'uint8')==numel(line));clear cleaner;
        error('MA20:RetainedOversizedEvent','Full event retained separately; automatic continuation prohibited.');
    end
    fid=fopen(eventsPath,'ab');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));
    assert(fwrite(fid,line,'uint8')==numel(line));clear cleaner;
    used=used+numel(line);
end
summary=struct('schema','MA20_NATIVE_MRT_SEGMENT_SUMMARY_V1','state',state,...
    'event_bytes',used,'original_budget_unchanged',true,'full_figure_pass',false,...
    'native_stop_flag_is_independent_convergence_proof',false);
end
