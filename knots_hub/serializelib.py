"""
An API for serialization of dataclass to and from disk as JSON.
"""

import dataclasses
import json
import logging
import os
import typing
from typing import Callable
from typing import Optional
from pathlib import Path

from knots_hub._utils import backup_environ
from knots_hub._utils import expand_envvars

LOGGER = logging.getLogger(__name__)


class _Uninitialized:
    """
    Represent a value that is Uninitialized.
    """

    serialized = "<%Uninitialized%>"

    def __bool__(self):
        return False


Uninitialized = _Uninitialized()
UninitializedType = _Uninitialized


@dataclasses.dataclass(frozen=True)
class UnserializeContext:
    """
    Collection of objects that are useful to unserialize an object depending on its type.
    """

    environ: dict[str, str]
    parent_dir: Path


"""-------------------------------------------------------------------------------------
Fields
"""


ArgT = typing.TypeVar("ArgT")
RetT = typing.TypeVar("RetT")


def _serialize_uninitialized_handler(
    caster: Callable[[ArgT], RetT]
) -> Callable[[ArgT], RetT]:
    def _inner(value):
        if value is Uninitialized:
            return Uninitialized.serialized
        return caster(value)

    return _inner


def _unserialize_uninitialized_handler(
    caster: Callable[[ArgT, ...], RetT]
) -> Callable[[ArgT, ...], RetT]:
    def _inner(value, *args, **kwargs):
        if value == Uninitialized.serialized:
            return Uninitialized
        return caster(value, *args, **kwargs)

    return _inner


def mkfield(
    serializer: Callable[[ArgT], RetT],
    unserializer: Callable[[RetT, UnserializeContext], ArgT],
    doc: str = "",
    typehint: str = "",
):
    """
    Create a dataclass field that can be serialized and unserialized.

    It has a default Uninitialized value.

    Args:
        serializer: function to serialize a vlue
        unserializer: function to unserialize a value with a context
        doc: a block of rst formatted text used for static documentation.
        typehint: a string to indicate the expected type of the field once serialized.
    """
    return dataclasses.field(
        metadata={
            # wrap to handle Uninitialized value
            "serialize": _serialize_uninitialized_handler(serializer),
            "unserialize": _unserialize_uninitialized_handler(unserializer),
            "documentation": doc,
            "type_hint_serialized": typehint,
        },
        default=Uninitialized,
    )


def get_field_doc(field: dataclasses.Field) -> str:
    """
    Get the documentation attribute of a Field created with serializelib.
    """
    return field.metadata["documentation"]


def get_field_typehint(field: dataclasses.Field) -> str:
    """
    Get the type hint attribute of a Field created with serializelib.
    """
    return field.metadata["type_hint_serialized"]


# XXX: intentional break of pep8 naming to make them looks like class


def StrField(doc=""):
    def _unserialize(value, context: UnserializeContext):
        return str(value)

    return mkfield(str, _unserialize, doc=doc, typehint="str")


def _to_path(value: str, environ: Optional[dict] = None) -> Path:
    if environ:
        with backup_environ(clear=True):
            os.environ.update(environ)
            value = expand_envvars(value)

    return Path(value)


def PathField(doc="", expandvars=False):
    def _unserialize(value, context: UnserializeContext):
        return _to_path(value, context.environ if expandvars else None)

    return mkfield(str, _unserialize, doc=doc, typehint="str")


def FloatField(doc=""):

    def _unserialize(value, context: UnserializeContext):
        return float(value)

    return mkfield(float, _unserialize, doc=doc, typehint="float")


def PathListField(doc="", expandvars=False):
    def _serialize(src: typing.Iterable[Path]) -> list[str]:
        return [str(path) for path in src]

    def _unserialize(
        src: typing.Iterable[str],
        context: UnserializeContext,
    ) -> list[Path]:
        return [
            _to_path(path, environ=context.environ if expandvars else None)
            for path in src
        ]

    return mkfield(_serialize, _unserialize, doc=doc, typehint="list[str]")


def DictOfStrNPathField(doc="", expandvars=False):
    def _serialize(src: dict[str, Path]) -> dict[str, str]:
        return {str(key): str(value) for key, value in src.items()}

    def _unserialize(
        src: dict[str, str],
        context: UnserializeContext,
    ) -> dict[str, Path]:
        return {
            str(key): _to_path(value, environ=context.environ if expandvars else None)
            for key, value in src.items()
        }

    return mkfield(_serialize, _unserialize, doc=doc, typehint="dict[str, str]")


"""-------------------------------------------------------------------------------------
IO
"""

DCT = typing.TypeVar("DCT")
DictT = typing.TypeVar("DictT", bound=dict)


def unserialize(
    serialized: str,
    data_class: typing.Type[DCT],
    context: UnserializeContext,
    pre_process: Optional[Callable[[DictT], DictT]] = None,
) -> DCT:
    """
    Create a dataclass instance from a serialized string representation.

    Args:
        serialized: a serialized representation of an instance of the data_class arg.
        data_class: a dataclass Class with serializelib fields that must match the serialized arg.
        context: a datastructure that help resolving the instance fields values.
        pre_process: optional function to call on the json dict before it is converted to an instance.
    """
    content = json.loads(serialized)

    if pre_process:
        content = pre_process(content)

    kwargs = {}
    for field in dataclasses.fields(data_class):
        caster = field.metadata["unserialize"]
        kwargs[field.name] = caster(content[field.name], context)

    return data_class(**kwargs)


def serialize(
    unserialized,
    post_process: Optional[Callable[[DictT], DictT]] = None,
) -> str:
    """
    Convert a dataclass instance to a serialized string representation.

    Args:
        unserialized: a dataclass instance with serializelib fields.
        post_process: optional function to call on the dict before it is saved to json
    """
    content = {}

    for field in dataclasses.fields(unserialized):
        caster = field.metadata["serialize"]
        value = getattr(unserialized, field.name)
        content[field.name] = caster(value)

    if post_process:
        content = post_process(content)

    return json.dumps(content, indent=4, sort_keys=True)


def read_from_disk(
    data_class: typing.Type[DCT],
    path: Path,
    pre_process: Optional[Callable[[DictT], DictT]] = None,
) -> DCT:
    """
    Create a dataclass instance from a serialized disk file.

    Args:
        data_class: a dataclass class object which use serializelib fields.
        path: filesystem path to an existing file
        pre_process:
            a callable called directly with the read json content,
            before its being processed to an instance.
    """
    context = UnserializeContext(
        environ=os.environ.copy(),
        parent_dir=path.parent,
    )
    return unserialize(
        serialized=path.read_text(encoding="utf-8"),
        data_class=data_class,
        context=context,
        pre_process=pre_process,
    )


def write_to_disk(
    data_class,
    path: Path,
    post_process: Optional[Callable[[DictT], DictT]] = None,
):
    """
    Write the given dataclass instance as a serialized disk file.

    Args:
        data_class: a dataclass instance object which use serializelib fields.
        path: filesystem path to file that may exist
        post_process:
            a callable called with the dict that is about to be written to disk,
            before the data_class is added.
    """
    path.write_text(
        serialize(data_class, post_process=post_process),
        encoding="utf-8",
    )


def update_disk(
    data_class,
    path: Path,
    write_post_process: Optional[Callable[[DictT], DictT]] = None,
    read_pre_process: Optional[Callable[[DictT], DictT]] = None,
):
    """
    Write the given dataclass instance as a serialized disk file, updating if the file already exists.

    Updating means only writing non-Uninitialized value of this instance.

    Args:
        data_class: a dataclass instance object which use serializelib fields.
        path: filesystem path to file that may exist
        write_post_process: pre-process for file read call
        read_pre_process: pre-process for file write call
    """
    if path.exists():
        new = read_from_disk(data_class.__class__, path, pre_process=read_pre_process)
        for field in dataclasses.fields(data_class):
            value = getattr(data_class, field.name)
            if value is not Uninitialized:
                setattr(new, field.name, value)
    else:
        new = data_class

    write_to_disk(new, path, post_process=write_post_process)
