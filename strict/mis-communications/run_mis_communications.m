function result = run_mis_communications(outputPath, figureName, settingsPath)
% Full figures: run_mis_communications('output.json','fig7').
% Component validation: run_mis_communications('unit.json','component-test').
if nargin<2, figureName='component-test'; end
if nargin<3, settingsPath=fullfile(fileparts(mfilename('fullpath')),'settings.json'); end
result=mis_communications_strict_engine(outputPath,figureName,settingsPath);
end

