from dataclasses import (  # type: ignore
    InitVar,
    _FIELDS,
    dataclass,
    field,
    replace as std_replace,
)

from apischema.dataclasses import replace
from apischema.dataclasses.cache import _resolve_init_var
from apischema.fields import fields_set, with_fields_set
from apischema.metadata.misc import init_var


@dataclass
class WithInitVar:
    a: InitVar[int] = field(metadata=init_var("int"))


def test_resolve_init_var():
    assert _resolve_init_var(WithInitVar, getattr(WithInitVar, _FIELDS)["a"]) == int


@with_fields_set
@dataclass
class WithFieldsSet:
    a: int = 0


def test_replace():
    obj = WithFieldsSet()
    assert fields_set(obj) == set()
    obj2 = std_replace(obj)
    assert fields_set(obj2) == {"a"}
    obj3 = replace(obj)
    assert fields_set(obj3) == set()
