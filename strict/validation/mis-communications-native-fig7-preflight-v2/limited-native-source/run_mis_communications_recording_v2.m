function result=run_mis_communications_recording_v2(outputPath,figureName,settingsPath,recordFolder)
% Explicit WORK version; original package and all numeric controls unchanged.
base=fileparts(mfilename('fullpath'));
if nargin<3,settingsPath=fullfile(base,'settings.json');end
assert(nargin==4,'Pass a fresh recording folder; never resume old partial files.');
assert(string(figureName)=="fig7"||startsWith(string(figureName),"recording-preflight:fig7:"));
settings=jsondecode(fileread(settingsPath));assert(settings.number_of_starts==6000&&settings.rcg_max_iterations==4000);
identity=jsondecode(fileread(fullfile(base,'recording-source-freeze.json')));
identity.actual_matlab_version=version;identity.actual_computer=computer;
identity.actual_engine_which=which('mis_communications_strict_engine_recording_v2');
if string(figureName)=="fig7",mode='full12000';else,mode='fixed_original_full_start_preflight_not_full_bank';end
comm_recording_observer_v2('configure',struct('record_folder',recordFolder,'mode',mode,'source_identity',identity));
try
    result=mis_communications_strict_engine_recording_v2(outputPath,figureName,settingsPath);
catch problem
    comm_recording_observer_v2('fatal-save',struct('identifier',problem.identifier,'message',problem.message,'stack',problem.stack));
    rethrow(problem);
end
status=comm_recording_observer_v2('finalize');
result.native_all_start_recording_status=status;
result.recording_only_not_independent_physical_certificate=true;
if string(figureName)=="fig7",result.overall_full_success=result.overall_full_success&&status.all_full_recording_gates_passed;end
[parent,~,~]=fileparts(outputPath);if ~isempty(parent)&&~isfolder(parent),mkdir(parent);end
fid=fopen(outputPath,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));
end
