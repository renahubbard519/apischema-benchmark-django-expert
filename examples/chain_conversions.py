from typing import Any, Dict, Mapping, NewType

from apischema.conversion import extra_serializer


class JsonSchema(Dict[str, Any]):
    pass


JsonSchema7 = NewType("JsonSchema7", Mapping[str, Any])


def isolate_ref(schema: Dict[str, Any]):
    if "$ref" in schema and len(schema) > 1:
        schema.setdefault("allOf", []).append({"$ref": schema.pop("$ref")})


@extra_serializer(conversions={JsonSchema: JsonSchema7})
def to_json_schema_7(schema: JsonSchema) -> JsonSchema7:
    result = schema.copy()
    isolate_ref(result)
    if "$defs" in result:
        result["definitions"] = {**result.pop("$defs"), **result.get("definitions", {})}
    if "dependentRequired" in result:
        result["dependencies"] = {
            **result.pop("dependentRequired"),
            **result.get("dependencies", {}),
        }
    return JsonSchema7(result)
