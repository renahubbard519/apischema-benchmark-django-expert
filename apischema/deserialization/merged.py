from typing import Iterable, Iterator, Mapping, Sequence, Type

from apischema.conversions.conversions import DefaultConversions
from apischema.conversions.visitor import DeserializationVisitor
from apischema.objects import ObjectField
from apischema.objects.visitor import DeserializationObjectVisitor
from apischema.types import AnyType
from apischema.utils import get_origin_or_type
from apischema.visitor import Unsupported


class InitMergedAliasVisitor(
    DeserializationObjectVisitor[Iterator[str]], DeserializationVisitor[Iterator[str]]
):
    def mapping(
        self, cls: Type[Mapping], key_type: AnyType, value_type: AnyType
    ) -> Iterator[str]:
        yield from ()

    def object(self, tp: AnyType, fields: Sequence[ObjectField]) -> Iterator[str]:
        for field in fields:
            if field.merged:
                yield from get_deserialization_merged_aliases(
                    get_origin_or_type(tp), field, self.default_conversions
                )
            elif not field.is_aggregate:
                yield field.alias

    def _union_result(self, results: Iterable[Iterator[str]]) -> Iterator[str]:
        results = list(results)
        if len(results) != 1:
            raise NotImplementedError
        return results[0]


def get_deserialization_merged_aliases(
    cls: Type, field: ObjectField, default_conversions: DefaultConversions
) -> Iterator[str]:
    assert field.merged
    try:
        yield from InitMergedAliasVisitor(default_conversions).visit_with_conv(
            field.type, field.deserialization
        )
    except (NotImplementedError, Unsupported):
        raise TypeError(
            f"Merged field {cls.__name__}.{field.name} must have an object type"
        ) from None
