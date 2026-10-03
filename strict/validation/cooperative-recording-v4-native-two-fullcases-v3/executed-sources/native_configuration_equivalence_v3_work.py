"""Exact configuration serialization equivalence, not numerical-array coercion.

The one ACTUAL observed MATLAB jsondecode/jsonencode difference is a configured
J=1 satellite_latitudes_deg JSON list [x] becoming scalar x. No tolerance,
general list flattening, model change, manuscript coordinate inference, or
other field conversion is allowed. Immutable file SHA is checked separately.
"""
import copy


def verify(original, native):
    checked=copy.deepcopy(native);converted=[]
    source=original['tuned_not_reported']['satellite_latitudes_deg']
    saved=native['tuned_not_reported']['satellite_latitudes_deg']
    if source!=saved:
        assert original['reported']['J']==native['reported']['J']==1
        assert isinstance(source,list) and len(source)==1
        assert isinstance(saved,(int,float)) and not isinstance(saved,bool)
        assert source[0]==saved
        checked['tuned_not_reported']['satellite_latitudes_deg']=[saved]
        converted.append({'field':'configuration.tuned_not_reported.satellite_latitudes_deg',
            'original_JSON_value':source,'actual_native_JSON_value':saved,
            'exact_singleton_value_equal':source[0]==saved,'J_is_exactly_one':True})
    checks={'all_other_configuration_fields_exactly_unchanged':checked==original,
        'only_predeclared_J1_satellite_latitude_singleton_metadata_conversion':len(converted)<=1}
    assert all(checks.values()),'Unapproved configuration serialization/model difference'
    return {'scope':'exact_JSON_scalar_singleton_geometry_metadata_only_NOT_matrix_flattening',
        'checks':checks,'all_metadata_conversion_checks_pass':all(checks.values()),
        'actual_conversions':converted,'numerical_arrays_or_model_changed':False}
