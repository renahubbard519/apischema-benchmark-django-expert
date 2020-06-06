import collections.abc
import sys
from typing import (
    AbstractSet,
    Any,
    Collection,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

from dataclasses import Field

AnyType = Any
NoneType: Type[None] = type(None)
Number = Union[int, float]

PRIMITIVE_TYPES = {str, int, bool, float, NoneType}

if sys.version_info >= (3, 7):
    ITERABLE_TYPES = {
        collections.abc.Iterable: tuple,
        collections.abc.Collection: tuple,
        collections.abc.Sequence: tuple,
        tuple: tuple,
        collections.abc.MutableSequence: list,
        list: list,
        collections.abc.Set: frozenset,
        frozenset: frozenset,
        collections.abc.MutableSet: set,
        set: set,
    }

    LIST_TYPE = list

    MAPPING_TYPES = {
        collections.abc.Mapping: dict,
        collections.abc.MutableMapping: dict,
        dict: dict,
    }
else:
    ITERABLE_TYPES = {
        Iterable: tuple,
        Collection: tuple,
        Sequence: tuple,
        Tuple: tuple,
        MutableSequence: list,
        List: list,
        AbstractSet: frozenset,
        FrozenSet: frozenset,
        Set: set,
    }

    LIST_TYPE = list

    MAPPING_TYPES = {Mapping: dict, MutableMapping: dict, Dict: dict}


if sys.version_info >= (3, 7):
    OrderedDict = dict
else:
    from collections import OrderedDict  # noqa

# Kind of hack to benefit of PEP 584
if sys.version_info >= (3, 9):
    Metadata = Mapping[str, Any]
    DictWithUnion = dict
else:

    class Metadata(Mapping[str, Any]):
        def __or__(self, other: Mapping[str, Any]) -> "Metadata":
            return DictWithUnion({**self, **other})

    class DictWithUnion(Dict[str, Any], Metadata):  # noqa
        pass


class MetadataMixin(Metadata):
    metadata: Mapping[str, Any]

    def __getitem__(self, key):
        return self.metadata[key]

    def __iter__(self):
        return iter(self.metadata)

    def __len__(self):
        return len(self.metadata)

    def _resolve(self, field: Field, field_type: AnyType) -> Metadata:
        return self
