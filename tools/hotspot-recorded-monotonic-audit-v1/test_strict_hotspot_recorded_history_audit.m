function test_strict_hotspot_recorded_history_audit()
% Synthetic tests only; no saved scientific case is read.
cases={ [10,10.0000005],true,true,true,0; [10,10],true,true,true,0; ...
        [10,9.9999995],true,true,false,1; [10,9],true,true,false,1; ...
        [10,9.9999995,10.01],true,false,false,1; [10,10.0000005],false,true,[],0; ...
        [10,9.9999995],false,true,false,1};
for k=1:size(cases,1)
    h=cases{k,1};r=strict_hotspot_recorded_history_audit(h,1e-5,cases{k,2});
    assert(isequal(r.production_signed_stop_recomputed,cases{k,3}));
    assert(isequal(r.independent_recorded_stop_and_nondecrease_gate,cases{k,4}));
    assert(r.negative_increment_count==cases{k,5});
end
r=strict_hotspot_recorded_history_audit([10,9.9999995],1e-5,true);assert(r.negative_within_numerical_abs_tolerance_count==1);
r=strict_hotspot_recorded_history_audit([10,9],1e-5,true);assert(r.negative_within_numerical_abs_tolerance_count==0);
r=strict_hotspot_recorded_history_audit([],1e-5,true);assert(isempty(r.independent_recorded_stop_and_nondecrease_gate));
r=strict_hotspot_recorded_history_audit(10,1e-5,true);assert(isempty(r.independent_recorded_stop_and_nondecrease_gate));
invalid={@()strict_hotspot_recorded_history_audit([1,nan],1e-5,true), ...
    @()strict_hotspot_recorded_history_audit([1,inf],1e-5,true), ...
    @()strict_hotspot_recorded_history_audit([1,2],nan,true), ...
    @()strict_hotspot_recorded_history_audit([1,2],1e-5,1), ...
    @()strict_hotspot_recorded_history_audit([1,2],0,true)};
for k=1:numel(invalid),failed=false;try,invalid{k}();catch,failed=true;end;assert(failed);end
for v=[-1e-9,0,1e-6,2e-6]
    r=strict_hotspot_gradient_norm_audit(v,1e-6);
    assert(r.production_gradient_stop_recomputed==(v<=1e-6));
    assert(r.independent_recorded_gradient_gate==(v>=0&&v<=1e-6));
end
r=strict_hotspot_gradient_norm_audit(-1e-9,1e-6);
assert(r.production_gradient_stop_recomputed&&~r.independent_recorded_gradient_gate);
disp('synthetic recorded-history audit tests passed; no scientific data run');
end
