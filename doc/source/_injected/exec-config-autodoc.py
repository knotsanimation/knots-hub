import dataclasses
from typing import Type

import knots_hub

RowType = tuple[str, str, str]


def enforce_col_length(
    row: tuple[str, str, str],
    lengths: list[int],
) -> RowType:
    # noinspection PyTypeChecker
    return tuple(
        col.ljust(lengths[index], col[-1] if col else " ")
        for index, col in enumerate(row)
    )


def unify_columns(table: list[RowType]) -> list[str]:
    """
    Add the columns separator to return a row string.
    """
    new_table = []
    for row in table:
        sep = "+" if row[-1][-1] in ["-", "="] else "|"
        row = sep + sep.join(row) + sep
        new_table.append(row)
    return new_table


def create_field_table(field: dataclasses.Field) -> list[RowType]:
    field_name = field.name
    field_doc = field.metadata["documentation"]
    field_required = field.metadata["environ_required"]

    doc = field_doc.split("\n")

    # typing.Annotated
    if hasattr(field.type, "__metadata__"):
        ftype = field.type.__origin__
    else:
        ftype = field.type

    ftype = str(ftype).replace("typing.", "")

    default_value = repr(None)
    if not field_required:
        default_value = repr(
            field.default_factory()
            if field.default is dataclasses.MISSING
            else field.default
        )

    env_var = field.metadata["environ"]

    rows = [
        (f" .. option:: {field_name} ", " **type** ", f" `{ftype}` "),
        ("-", "-", "-"),
        ("", " **required** ", f" {'yes' if field_required else 'no'} "),
        ("", "-", "-"),
        ("", " **default** ", f" ``{default_value}`` "),
        ("", "-", "-"),
        ("", " **environment variable** ", f" ``{env_var}`` "),
        ("", "-", "-"),
        ("", " **description** ", f" {doc.pop(0)} "),
    ]

    for doc_line in doc:
        rows += [("", "", f" {doc_line} ")]

    rows += [("-", "-", "-")]
    return rows


def replace_character(src_str: str, character: str, substitution: str) -> str:
    index = src_str.rfind(character, 0, -2)
    return src_str[:index] + substitution + src_str[index + 1 :]


def generate_table():
    fields = dataclasses.fields(knots_hub.HubConfig)

    fields_table: list[RowType] = []
    for field in fields:
        fields_table += create_field_table(field=field)

    header_table = [
        ("-", "-", "-"),
        (" key name ", "", ""),
        ("=", "=", "="),
    ]
    table = header_table + fields_table

    col_lens = [max([len(row[index]) for row in table]) for index in range(3)]

    table = [enforce_col_length(row, col_lens) for row in table]
    table = unify_columns(table)

    table[0] = replace_character(table[0], "+", "-")
    table[1] = replace_character(table[1], "|", " ")

    return "\n".join(table)


print(generate_table())
