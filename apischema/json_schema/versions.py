from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Mapping,
    NewType,
    Optional,
    Type,
)

from apischema.conversion.converters import extra_serializer
from apischema.conversion.utils import Conversions
from apischema.json_schema.types import JsonSchema

RefFactory = Callable[[str], str]


def ref_prefix(prefix: str) -> RefFactory:
    if not prefix.endswith("/"):
        prefix += "/"
    return lambda ref: prefix + ref


def isolate_ref(schema: Dict[str, Any]):
    if "$ref" in schema and len(schema) > 1:
        schema.setdefault("allOf", []).append({"$ref": schema.pop("$ref")})


JsonSchema7 = NewType("JsonSchema7", Mapping[str, Any])


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


OpenAPI30 = NewType("OpenAPI30", Mapping[str, Any])


@extra_serializer(conversions={JsonSchema: OpenAPI30})
def to_open_api_3_0(schema: JsonSchema) -> OpenAPI30:
    result = schema.copy()
    for key in ("dependentRequired", "unevaluatedProperties", "$defs"):
        result.pop(key, ...)
    isolate_ref(result)
    if "null" in result.get("type", ()):
        result.setdefault("nullable", True)
        if result["type"] == "null":
            result.pop("type")
        else:
            types = [t for t in result["type"] if t != "null"]
            result["type"] = types if len(types) > 1 else types[0]
    if "examples" in result:
        result.setdefault("example", result.pop("examples")[0])
    return OpenAPI30(result)


@dataclass
class JsonSchemaVersion:
    schema: Optional[str] = None
    ref_prefix: str = ""
    serialization: Optional[Type] = None
    all_refs: bool = True

    @property
    def conversions(self) -> Optional[Conversions]:
        return None if self.serialization is None else {JsonSchema: self.serialization}

    @property
    def ref_factory(self) -> RefFactory:
        return ref_prefix(self.ref_prefix)

    DRAFT_2019_09: ClassVar["JsonSchemaVersion"]
    DRAFT_7: ClassVar["JsonSchemaVersion"]
    OPEN_API_3_0: ClassVar["JsonSchemaVersion"]


JsonSchemaVersion.DRAFT_2019_09 = JsonSchemaVersion(
    "http://json-schema.org/draft/2019-09/schema#", "#/$defs/", None, False,
)
JsonSchemaVersion.DRAFT_7 = JsonSchemaVersion(
    "http://json-schema.org/draft-07/schema#", "#/definitions/", JsonSchema7, False,
)
JsonSchemaVersion.OPEN_API_3_0 = JsonSchemaVersion(
    None, "#/components/schema/", OpenAPI30, True
)
