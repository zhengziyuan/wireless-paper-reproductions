function result=test_isac_fixed_channel_cache_matlab(outputPath,scenePath,configPath)
% Independent actual full W block; original10000 budget and stop gates.
result=run_strict_rotatable_isac(outputPath,scenePath,configPath,'fixed_channel_cache_equivalence');
end
