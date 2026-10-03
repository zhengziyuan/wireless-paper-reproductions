function result = run_mis_sensing(outputPath, figureName, settingsPath)
% Full figures: run_mis_sensing('output.json','fig7').
% Component validation: run_mis_sensing('unit.json','component-test').
if nargin<2, figureName='component-test'; end
if nargin<3, settingsPath=fullfile(fileparts(mfilename('fullpath')),'settings.json'); end
result=mis_sensing_strict_engine(outputPath,figureName,settingsPath);
end

