function result = run_reference_candidate(outputPath,settingsPath)
% Original full-dimensional four-target/six-power single-start fingerprint.
% This does not run or certify the original 6000-start full figure bank.
base=fileparts(mfilename('fullpath'));
if nargin<1,outputPath=fullfile(base,'outputs','reference-candidate-v2','ris-fingerprint-matlab.json');end
if nargin<2,settingsPath=fullfile(base,'settings_reference_candidate.json');end
result=mis_sensing_strict_engine(outputPath,'reference-fingerprint',settingsPath);
end
