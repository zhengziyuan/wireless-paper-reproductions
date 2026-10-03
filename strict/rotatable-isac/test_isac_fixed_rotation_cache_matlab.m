function result=test_isac_fixed_rotation_cache_matlab(outputPath,scenePath,configPath,activeScenePath)
% Independent full500-step RCG contexts, full2828 W tests, whole all6 scenario.
% Two original exported scenes; no dimensions/inputs/stop budgets reduced.
if nargin<4,activeScenePath=scenePath;end
result=run_strict_rotatable_isac(outputPath,scenePath,configPath,'fixed_rotation_base_cache_equivalence',activeScenePath);
end
