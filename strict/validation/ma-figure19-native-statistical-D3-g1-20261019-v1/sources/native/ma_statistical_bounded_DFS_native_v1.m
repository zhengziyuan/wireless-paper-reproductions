function report=ma_statistical_bounded_DFS_native_v1(model,folder,binding,nodeBudget)
% Native exact statistical target, bounded memory/frontier and work chunks.
% nodeBudget is a resumable work boundary, never a total scientific cap.
assert(isscalar(nodeBudget)&&isfinite(nodeBudget)&&nodeBudget>0&&nodeBudget==fix(nodeBudget),'MAExact:Work','Finite positive node work chunk required.');
selected=struct('caller_binding',binding,'model_primitive_SHA256',ma_native_grid_io_v1('sha_value',model.primitive_floating_input),...
    'N',model.N,'M',model.M,'D',model.D,'mode',model.mode,'target','exact_rational_native_frozen_statistical_product',...
    'tie','ascending canonical combination; strict exact greater first tie','spacing','exact squared binary64-grid distances');
ma_native_grid_io_v1('bind',folder,selected);path=fullfile(folder,'bounded-frontier.mat');
if isfile(path)
    state=ma_native_grid_io_v1('load',path);ma_native_grid_io_v1('assert_same',state.binding,selected,'Saved native exact frontier identity differs');
else
    state=struct('binding',selected,'stack',{{struct('indices',[],'remaining',1:model.count,'next',1,'entered',false)}},...
        'nodes',0,'leaves',0,'pruned',0,'infeasible',0,'best',[],'winner_indices',[],'improvements',0,...
        'rolling_decision_SHA256',repmat('0',1,64),'last_closed_decision',[],...
        'complete',false,'status','unstarted','host_failure',[],'elapsed_seconds',0);
    ma_native_grid_io_v1('mat',path,state);
    payload=model.primitive_floating_input;save(fullfile(folder,'native-frozen-primitive-inputs-once.mat'),'payload','-v7');
end
if state.complete,report=state;return;end
lock=fullfile(folder,'active-exact-search.lock');jfile=javaObject('java.io.File',lock);
assert(jfile.createNewFile(),'MAExact:ActiveOrUncertain','Existing active/abandoned search lock requires actual previous-owner terminal review.');
started=tic;before=state.nodes;failure=[];
try
    while ~isempty(state.stack)&&state.nodes-before<nodeBudget
        frame=state.stack{end};indices=frame.indices;remaining=frame.remaining;r=model.N-numel(indices);
        if ~frame.entered
            state.nodes=state.nodes+1;
            if numel(remaining)<r
                state.infeasible=state.infeasible+1;state.stack(end)=[];state=closed(state,'infeasible',indices,[]);
            elseif r==0
                value=ma_statistical_value_bound_native_v1('value',model,indices,[]);state.leaves=state.leaves+1;
                if isempty(state.best)||value>ma_rat_v1.unpack(state.best)
                    state.best=pack(value);state.winner_indices=indices;state.improvements=state.improvements+1;
                end
                state.stack(end)=[];state=closed(state,'exact_leaf',indices,pack(value));
            else
                upper=ma_statistical_value_bound_native_v1('upper',model,indices,remaining);
                if ~isempty(state.best)&&upper<=ma_rat_v1.unpack(state.best)
                    state.pruned=state.pruned+1;state.stack(end)=[];state=closed(state,'exact_upper_not_above_incumbent',indices,pack(upper));
                else,state.stack{end}.entered=true;end
            end
        else
            if frame.next>numel(remaining),state.stack(end)=[];continue;end
            point=remaining(frame.next);state.stack{end}.next=frame.next+1;
            future=remaining(frame.next+1:end);future=future(model.compatible(point,future));
            state.stack{end+1}=struct('indices',[indices,point],'remaining',future,'next',1,'entered',false);
        end
    end
    state.complete=isempty(state.stack);
    if state.complete,state.status='complete_exact_native_statistical_search';else,state.status='bounded_work_boundary_frontier_retained_not_complete';end
    state.elapsed_seconds=state.elapsed_seconds+toc(started);ma_native_grid_io_v1('mat',path,state);
catch err
    failure=ma_native_grid_io_v1('failure',err);state.host_failure=failure;state.status='retained_exact_search_error_no_automatic_retry';
    % Last successfully committed frontier is preserved. An error snapshot is
    % diagnostic only and does not authorize continuing an uncertain owner.
    ma_native_grid_io_v1('mat',fullfile(folder,'retained-search-error.mat'),state);
end
report=state;report.memory_scope='Only O(N*grid) live frontier, cached small model, one rolling decision hash/last witness; no all-leaf or all-prune tape.';
report.rolling_digest_is_not_a_stored_independent_full_tree_certificate=true;
report.new_instantaneous_MC_or_optimizer_calls=0;report.ownstate_reference_dual_or_paper_PASS=false;
if ~isempty(state.best),report.display_rate_log2_product=display_log2(ma_rat_v1.unpack(state.best));report.winner_positions=model.grid(state.winner_indices,:);end
ma_native_grid_io_v1('json',fullfile(folder,'progress.json'),report);
if isempty(failure),delete(lock);else,error('MAExact:RetainedFailure','Saved native exact search error retained: %s',failure.message);end
end

function state=closed(state,kind,prefix,value)
event=struct('previous',state.rolling_decision_SHA256,'kind',kind,'prefix',prefix,'exact_value',value,...
    'incumbent_version',state.improvements,'winner',state.winner_indices,'incumbent',state.best);
state.rolling_decision_SHA256=ma_native_grid_io_v1('sha_value',event);state.last_closed_decision=event;
end
