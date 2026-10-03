function result=strict_hotspot_spectral_test(fixturePath,outputPath)
% Bounded synthetic trajectory parity; original stop flags remain capped.
f=load(fixturePath);
[cp,ch,cs]=strict_hotspot_rgd_spectral('phase',f.phi,f.x,'criterion',f.P,f.noise,f.settings);
[rp,rh,rs]=strict_hotspot_rgd_spectral('phase',f.phi,f.x,'rate',f.W,f.noise,f.settings);
checks=struct('criterion_phi_max_error',max(abs(cp(:)-f.criterion_phi(:))), ...
    'criterion_history_max_error',max(abs(ch(:)-f.criterion_history(:))), ...
    'rate_phi_max_error',max(abs(rp(:)-f.rate_phi(:))),'rate_history_max_error',max(abs(rh(:)-f.rate_history(:))));
allpass=checks.criterion_phi_max_error<1e-8&&checks.rate_phi_max_error<1e-8&&checks.criterion_history_max_error<1e-10&&checks.rate_history_max_error<1e-10;
result=struct('scope','synthetic_full_dimension_12_step_original_RGD_trajectory_NOT_convergence_or_paper_reproduction', ...
    'checks',checks,'actual_stops',struct('criterion',cs,'rate',rs),'all_passed',allpass,'full_reproduction_pass',false);
if nargin>1,folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
assert(allpass,'Original RGD spectral step trajectory parity failed');
end
