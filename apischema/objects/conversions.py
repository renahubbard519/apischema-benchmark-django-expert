import inspect
from dataclasses import Field, replace
from types import new_class
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Mapping,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from apischema.metadata import properties
from apischema.objects.fields import MISSING_DEFAULT, ObjectField, set_object_fields
from apischema.objects.getters import object_fields
from apischema.type_names import TypeNameFactory, type_name
from apischema.types import OrderedDict
from apischema.typing import get_type_hints
from apischema.utils import (
    empty_dict,
    is_method,
    method_wrapper,
    substitute_type_vars,
    subtyping_substitution,
    to_pascal_case,
    with_parameters,
)


def set_type_name(cls: type, name: Union[str, TypeNameFactory, None]):
    if isinstance(name, TypeNameFactory):
        name(cls)
    else:
        type_name(name)(cls)


def _fields_and_init(
    cls: type, fields_and_methods: Union[Iterable[Any], Callable[[], Iterable[Any]]]
) -> Tuple[Sequence[ObjectField], Callable[[Any, Any], None]]:
    fields = object_fields(cls)
    output_fields: Dict[str, ObjectField] = OrderedDict()
    methods = []
    if callable(fields_and_methods):
        fields_and_methods = fields_and_methods()
    for elt in fields_and_methods:
        if elt is ...:
            output_fields.update(fields)
            continue
        if isinstance(elt, tuple):
            elt, metadata = elt
        else:
            metadata = empty_dict
        if not isinstance(metadata, Mapping):
            raise TypeError(f"Invalid metadata {metadata}")
        if isinstance(elt, Field):
            elt = elt.name
        if isinstance(elt, str) and elt in fields:
            elt = fields[elt]
        if is_method(elt):
            elt = method_wrapper(elt)
        if isinstance(elt, ObjectField):
            if metadata:
                output_fields[elt.name] = replace(
                    elt, metadata={**elt.metadata, **metadata}, default=MISSING_DEFAULT
                )
            else:
                output_fields[elt.name] = elt
            continue
        elif callable(elt):
            types = get_type_hints(elt)
            first_param = next(iter(inspect.signature(elt).parameters))
            substitution, _ = subtyping_substitution(
                types.get(first_param, with_parameters(cls)), cls
            )
            ret = substitute_type_vars(types.get("return", Any), substitution)
            output_fields[elt.__name__] = ObjectField(
                elt.__name__, ret, metadata=metadata
            )
            methods.append((elt, output_fields[elt.__name__]))
        else:
            raise TypeError(f"Invalid serialization member {elt} for class {cls}")

    serialized_methods = [m for m, f in methods if output_fields[f.name] is f]
    serialized_fields = list(
        output_fields.keys() - {m.__name__ for m in serialized_methods}
    )

    def __init__(self, obj):
        for field in serialized_fields:
            setattr(self, field, getattr(obj, field))
        for method in serialized_methods:
            setattr(self, method.__name__, method(obj))

    return tuple(output_fields.values()), __init__


T = TypeVar("T")


def object_serialization(
    cls: Type[T],
    fields_and_methods: Union[Iterable[Any], Callable[[], Iterable[Any]]],
    type_name: Union[str, TypeNameFactory] = None,
) -> Callable[[T], Any]:

    generic, bases = cls, ()
    if getattr(cls, "__parameters__", ()):
        generic = cls[cls.__parameters__]  # type: ignore
        bases = Generic[cls.__parameters__]  # type: ignore
    elif (
        type_name is None
        and callable(fields_and_methods)
        and fields_and_methods.__name__ != "<lambda>"
        and not getattr(cls, "__parameters__", ())
    ):
        type_name = to_pascal_case(fields_and_methods.__name__)

    def __init__(self, obj):
        _, new_init = _fields_and_init(cls, fields_and_methods)
        new_init.__annotations__ = {"obj": generic}
        output_cls.__init__ = new_init
        new_init(self, obj)

    __init__.__annotations__ = {"obj": generic}
    output_cls = new_class(
        f"{cls.__name__}Serialization",
        bases,
        exec_body=lambda ns: ns.update({"__init__": __init__}),
    )
    set_type_name(output_cls, type_name)
    set_object_fields(output_cls, lambda: _fields_and_init(cls, fields_and_methods)[0])

    return output_cls


def object_deserialization(
    func: Callable[..., T],
    type_name: Union[str, TypeNameFactory] = None,
    parameters_metadata: Mapping[str, Mapping] = None,
) -> Callable[[Any], T]:
    parameters_metadata = parameters_metadata or {}
    types = get_type_hints(func, include_extras=True)
    fields = []
    params, kwargs_param = [], None
    for param_name, param in inspect.signature(func).parameters.items():
        if param.kind is inspect.Parameter.POSITIONAL_ONLY:
            raise TypeError("Positional only parameters are not supported")
        param_type = types.get(param_name, Any)
        if param.kind in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }:
            field = ObjectField(
                param_name,
                param_type,
                param.default is inspect.Parameter.empty,
                parameters_metadata.get(param_name, empty_dict),
                default=param.default,
            )
            fields.append(field)
            params.append(param_name)
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            field = ObjectField(
                param_name,
                Mapping[str, param_type],  # type: ignore
                False,
                properties | parameters_metadata.get(param_name, empty_dict),
                default_factory=dict,
            )
            fields.append(field)
            kwargs_param = param_name
    if "return" not in types:
        raise TypeError("Object deserialization must be typed")
    return_type = types["return"]
    bases = ()
    if getattr(return_type, "__parameters__", ()):
        bases = (Generic[return_type.__parameters__],)  # type: ignore
    elif type_name is None and func.__name__ != "<lambda>":
        type_name = to_pascal_case(func.__name__)

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    input_cls = new_class(
        to_pascal_case(func.__name__),
        bases,
        exec_body=lambda ns: ns.update({"__init__": __init__}),
    )
    set_type_name(input_cls, type_name)
    set_object_fields(input_cls, fields)
    if kwargs_param:

        def wrapper(input):
            kwargs = input.kwargs.copy()
            kwargs.update(kwargs.pop(kwargs_param))
            return func(**kwargs)

    else:

        def wrapper(input):
            return func(**input.kwargs)

    wrapper.__annotations__["input"] = input_cls
    wrapper.__annotations__["return"] = return_type
    return wrapper
