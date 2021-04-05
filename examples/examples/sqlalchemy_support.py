from collections.abc import Collection
from inspect import getmembers
from itertools import starmap
from typing import Any, Optional

from graphql import print_schema
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import as_declarative

from apischema import Undefined, deserialize, serialize
from apischema.graphql import graphql_schema
from apischema.json_schema import serialization_schema
from apischema.objects import ObjectField, as_object


def column_field(name: str, column: Column) -> ObjectField:
    required = False
    default: Any = ...
    if column.default is not None:
        default = column.default
    elif column.server_default is not None:
        default = Undefined
    elif column.nullable:
        default = None
    else:
        required = True
    col_type = column.type.python_type
    col_type = Optional[col_type] if column.nullable else col_type
    return ObjectField(column.name or name, col_type, required, default=default)


# Very basic SQLAlchemy support
@as_declarative()
class Base:
    def __init_subclass__(cls):
        columns = getmembers(cls, lambda m: isinstance(m, Column))
        if not columns:
            return
        as_object(cls, list(starmap(column_field, columns)))


class Foo(Base):
    __tablename__ = "foo"
    bar = Column(Integer, primary_key=True)
    baz = Column(String)


foo = deserialize(Foo, {"bar": 0})
assert isinstance(foo, Foo)
assert foo.bar == 0
assert serialize(foo) == {"bar": 0, "baz": None}
assert serialization_schema(Foo) == {
    "$schema": "http://json-schema.org/draft/2019-09/schema#",
    "type": "object",
    "properties": {"bar": {"type": "integer"}, "baz": {"type": ["string", "null"]}},
    "required": ["bar"],
    "additionalProperties": False,
}


def foos() -> Optional[Collection[Foo]]:
    ...


schema = graphql_schema(query=[foos])
schema_str = """\
type Query {
  foos: [Foo!]
}

type Foo {
  bar: Int!
  baz: String
}
"""
assert print_schema(schema) == schema_str
