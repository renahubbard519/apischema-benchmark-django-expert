from dataclasses import dataclass

from graphql import print_schema

from apischema import graphql_schema, interface


@interface
@dataclass
class Bar:
    bar: int


@dataclass
class Foo(Bar):
    baz: str


def foo() -> Foo:
    ...


schema = graphql_schema(query=[foo])
schema_str = """\
type Query {
  foo: Foo
}

type Foo implements Bar {
  bar: Int!
  baz: String!
}

interface Bar {
  bar: Int!
}
"""
assert print_schema(schema) == schema_str
