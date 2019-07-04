import dataclasses
from datetime import datetime
from enum import Enum
from functools import singledispatch
from typing import Union, Any


@singledispatch
def convert_value_from_firestore(field_value: Any, field_description: dataclasses.Field) -> Any:
    """This adds support for Enum fields when retrieving a Document from Firestore.
    """
    return field_value


@convert_value_from_firestore.register
def _str_to_enum(field_value: str, field_description: dataclasses.Field) -> Union[str, Enum]:
    """If the string actually belongs to an Enum field, return an instance of that Enum.
    """
    if issubclass(field_description.type, Enum):
        enum_sub_cls = field_description.type
        return enum_sub_cls(field_value)
    else:
        return field_value


@convert_value_from_firestore.register
def _int_to_enum(field_value: int, field_description: dataclasses.Field) -> Union[int, Enum]:
    """If the int actually belongs to an Enum field, return an instance of that Enum.
    """
    if issubclass(field_description.type, Enum):
        enum_sub_cls = field_description.type
        return enum_sub_cls(field_value)
    else:
        return field_value


@singledispatch
def convert_value_to_firestore(field_value: Any) -> Any:
    """This adds support for Enum fields when saving a Document to Firestore.
    """
    return field_value


@convert_value_to_firestore.register
def _dict_to(field_value: dict) -> dict:
    encoded_value = {}
    for key, value in field_value.items():
        encoded_value[key] = convert_value_to_firestore(value)
    return encoded_value


@convert_value_to_firestore.register
def _list_to(field_value: list) -> list:
    return [convert_value_to_firestore(value) for value in field_value]


@convert_value_to_firestore.register
def _enum_to(field_value: Enum) -> Union[int, str]:
    return field_value.value


@convert_value_to_firestore.register
def _datetime_to(field_value: datetime) -> datetime:
    """Always require datetime objects with timezone info.
    """
    if field_value.tzinfo is None or field_value.tzinfo.utcoffset(field_value) is None:
        raise ValueError(f"The supplied datetime has no timezone info: {field_value}")
    return field_value
