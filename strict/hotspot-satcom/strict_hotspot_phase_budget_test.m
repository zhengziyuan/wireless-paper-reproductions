function result=strict_hotspot_phase_budget_test(fixturePath,outputPath)
% Same full-model original RGD, original gradient/retraction/Armijo and1e-6 stop.
% Larger unreported safety cap is not a changed threshold or full figure.
f=load(fixturePath);t=f.settings;keys=fieldnames(t);
for k=1:numel(keys),if isnumeric(t.(keys{k})),t.(keys{k})=double(t.(keys{k}));end,end
[phi,history,stop]=strict_hotspot_rgd_spectral('phase',f.phi0,f.inputs,'criterion',f.projector_square,f.noise,t);
[value,g]=strict_hotspot_statistical('criterion_gradient',f.inputs,phi,f.projector_square);
result=struct('scope','independent_full_model_original_RGD_unreported_cap_diagnostic_NOT_complete_chain_or_figures', ...
    'actual_termination',stop,'phase_history',history,'independently_recomputed_gradient_norm',norm(g), ...
    'recomputed_criterion',value,'original_gradient_threshold',t.gradient_tolerance, ...
    'unreported_safety_cap',t.rgd_max_iterations,'full_reproduction_pass',false);
if nargin>1,folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
end
