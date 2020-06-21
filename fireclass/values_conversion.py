import dataclasses
from enum import Enum
from functools import singledispatch
from typing import Union, Any, Optional


@singledispatch
def convert_value_from_firestore(field_value: Any, field_description: dataclasses.Field) -> Any:
    """This adds support for Enum fields when retrieving a Document from Firestore.
    """
    return field_value


@convert_value_from_firestore.register
def _bool(field_value: bool, field_description: dataclasses.Field) -> bool:
    if field_description.type in [bool, Optional[bool]]:
        return field_value
    else:
        raise TypeError(f"Received a value '{field_value}' for field '{field_description.name}'")


@convert_value_from_firestore.register
def _str_to_enum(field_value: str, field_description: dataclasses.Field) -> Union[str, Enum]:
    """If the string actually belongs to an Enum field, return an instance of that Enum.
    """
    if field_description.type == str:
        return field_value
    elif field_description.type == Optional[str]:
        # We received a string value for a field that may be a string or None
        return field_value
    elif issubclass(field_description.type, Enum):
        enum_sub_cls = field_description.type
        return enum_sub_cls(field_value)
    else:
        raise TypeError(f"Received a value '{field_value}' for field '{field_description.name}'")


@convert_value_from_firestore.register
def _int_to_enum(field_value: int, field_description: dataclasses.Field) -> Union[int, Enum]:
    """If the int actually belongs to an Enum field, return an instance of that Enum.
    """
    enum_cls = None

    if field_description.type == int:
        return field_value
    elif hasattr(field_description.type, "__origin__") and field_description.type.__origin__ == Union:
        # Special processing for Optional[T] fields
        if field_description.type.__args__ == Optional[int].__args__:  # type: ignore
            # We received an int value for an Optional[int] field
            return field_value
        elif issubclass(field_description.type.__args__[0], Enum):
            # We received an int value for an Optional[SomeEnum] field
            enum_cls = field_description.type.__args__[0]

    elif issubclass(field_description.type, Enum):
        # We received an int value for an Enum field
        enum_cls = field_description.type

    if enum_cls:
        # We received an int value that should be parsed as an Enum
        return enum_cls(field_value)

    raise TypeError(f"Received a value '{field_value}' for field '{field_description.name}'")


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
