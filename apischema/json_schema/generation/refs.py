from dataclasses import Field
from enum import Enum
from typing import (  # type: ignore
    Any,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
)

from apischema.conversions.utils import Conversions
from apischema.json_schema.generation.visitor import SchemaVisitor
from apischema.json_schema.refs import get_ref, schema_ref
from apischema.types import AnyType
from apischema.utils import is_hashable

try:
    from apischema.typing import Annotated
except ImportError:
    Annotated = ...  # type: ignore

Refs = Dict[str, Tuple[AnyType, int]]


class Recursive(Exception):
    pass


class RefsExtractor(SchemaVisitor):
    def __init__(self, conversions: Optional[Conversions], refs: Refs):
        super().__init__(conversions)
        self.refs = refs

    def _incr_ref(self, ref: Optional[str], cls: AnyType) -> bool:
        if ref is None:
            return False
        else:
            ref_cls, count = self.refs.get(ref, (cls, 0))
            if ref_cls != cls:
                raise ValueError(
                    f"Types {cls} and {self.refs[ref]} share same reference '{ref}'"
                )
            self.refs[ref] = (ref_cls, count + 1)
            return count > 0

    def annotated(self, cls: AnyType, annotations: Sequence[Any]):
        for annotation in reversed(annotations):
            if isinstance(annotation, schema_ref):
                annotation.check_type(cls)
                ref = annotation.ref
                if not isinstance(ref, str):
                    raise ValueError("Annotated schema_ref can only be str")
                annotated = Annotated[(cls, *filter(is_hashable, annotations))]  # type: ignore # noqa E501
                if self._incr_ref(ref, annotated):
                    return
        return self.visit(cls)

    def any(self):
        pass

    def collection(self, cls: Type[Iterable], value_type: AnyType):
        return self.visit(value_type)

    def dataclass(
        self,
        cls: Type,
        types: Mapping[str, AnyType],
        fields: Sequence[Field],
        init_vars: Sequence[Field],
    ):

        for field in self._dataclass_fields(fields, init_vars):
            self._visit_field(field, types[field.name])

    def enum(self, cls: Type[Enum]):
        pass

    def literal(self, values: Sequence[Any]):
        pass

    def mapping(self, cls: Type[Mapping], key_type: AnyType, value_type: AnyType):
        self.visit(key_type)
        self.visit(value_type)

    def named_tuple(
        self,
        cls: Type[Tuple],
        types: Mapping[str, AnyType],
        defaults: Mapping[str, Any],
    ):
        for cls in types.values():
            self.visit(cls)

    def new_type(self, cls: AnyType, super_type: AnyType):
        self.visit(super_type)

    def primitive(self, cls: Type):
        pass

    def subprimitive(self, cls: Type, superclass: Type):
        self.visit(superclass)

    def tuple(self, types: Sequence[AnyType]):
        for cls in types:
            self.visit(cls)

    def typed_dict(self, cls: Type, keys: Mapping[str, AnyType], total: bool):
        for cls in keys.values():
            self.visit(cls)

    def _union_result(self, results: Iterable):
        for _ in results:
            pass

    def visit(self, cls: AnyType):
        if (
            not is_hashable(cls)
            or self.is_extra_conversions(cls)
            or not self._incr_ref(get_ref(cls), cls)
        ):
            super().visit(cls)
