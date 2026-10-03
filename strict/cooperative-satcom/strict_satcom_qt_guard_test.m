function result=strict_satcom_qt_guard_test(fixturePath,outputPath)
% Independently generated same-input failed QT fixture, not an author file.
f=load(fixturePath);
[~,info]=strict_satcom_qt_guard('mr',f.p0,f.signal,f.cross,f.power,f.leak,f.offset,f.power_limit,f.interference_limit);
checks=struct('primal_relative_violation',info.solver_diagnostics.constraint_max_relative_violation, ...
    'qt_bound_violation',info.qt_bound_max_violation,'qt_tightness_error',info.qt_tightness_error, ...
    'minimum_sinr_improvement',min(info.after.sinr)-min(info.before.sinr));
allpass=checks.primal_relative_violation<=1e-5&&checks.qt_bound_violation<=1e-5&&checks.qt_tightness_error<1e-10&&checks.minimum_sinr_improvement>=-1e-5;
result=struct('scope','independently_generated_same_original_QT_input_numeric_guard_component_NOT_full_figures', ...
    'checks',checks,'actual_solver_diagnostics',info.solver_diagnostics,'all_passed',allpass,'full_reproduction_pass',false);
if nargin>1,folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
assert(allpass,'Original same-QT input independent physical/primal/bound gates failed');
end
