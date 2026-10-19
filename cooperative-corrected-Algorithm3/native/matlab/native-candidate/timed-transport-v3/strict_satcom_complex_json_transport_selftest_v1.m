function receipt=strict_satcom_complex_json_transport_selftest_v1()
% Pure fixture/JSON test; must run before any scientific algorithm.
doubleValue=complex([-zeros(1,1),0,2.5;Inf,-Inf,NaN],[0,-zeros(1,1),-3;1,-2,4]);
singleValue=complex(single([0,-zeros(1,1);2,3]),single([1,0;-2,4]));
fixture=struct('evaluation_real',[1,2,3],'nested',{{doubleValue,'cell-sentinel',struct('single_complex',singleValue)}}, ...
    'empty_cell',{cell(0,2)},'empty_real',zeros(0,3));
encoded=strict_satcom_complex_json_transport_v1('encode',fixture);
decoded=strict_satcom_complex_json_transport_v1('decode',encoded);
assert(isequaln(decoded,fixture),'Nested struct/cell direct complex-codec roundtrip failed');
assert(isequal(encoded.evaluation_real,fixture.evaluation_real),'Real evaluation fields changed');
assert(isequal(size(decoded.empty_cell),[0,2])&&isequal(size(decoded.empty_real),[0,3]),'Direct container shape changed');
assert_complex_bits(decoded.nested{1},doubleValue);assert_complex_bits(decoded.nested{3}.single_complex,singleValue);
serialized=jsonencode(encoded);assert(ischar(serialized)&&~isempty(serialized),'Nested encoded fixture JSON did not serialize');
values={doubleValue,singleValue};
for index=1:numel(values)
    payload=strict_satcom_complex_json_transport_v1('encode',values{index});
    payloadJSON=jsonencode(payload);
    recovered=strict_satcom_complex_json_transport_v1('decode',jsondecode(payloadJSON));
    assert_complex_bits(recovered,values{index});
end
realHex=cellstr(num2hex(real(doubleValue(:))));imagHex=cellstr(num2hex(imag(doubleValue(:))));
receipt=struct('passed',true,'nested_struct_cell_direct_codec_roundtrip',true,'nested_transport_JSON_serializes',true, ...
    'complex_payload_JSON_roundtrip_class_shape_and_IEEE_bits',true,'real_evaluation_fields_untouched',true, ...
    'signed_zero_fixture_present_where_MATLAB_retains_it',any(strcmp(realHex,'8000000000000000'))||any(strcmp(imagHex,'8000000000000000')), ...
    'NaN_and_Inf_complex_component_bits_preserved',true,'ordinary_JSON_container_shape_and_real_numeric_class_behavior_not_redefined',true, ...
    'scientific_algorithm_executed',false);
end

function assert_complex_bits(actual,expected)
assert(strcmp(class(actual),class(expected))&&isequal(size(actual),size(expected)),'Complex class/shape mismatch');
assert(isequal(num2hex(real(actual(:))),num2hex(real(expected(:)))),'Complex real IEEE bits changed');
assert(isequal(num2hex(imag(actual(:))),num2hex(imag(expected(:)))),'Complex imaginary IEEE bits changed');
end
