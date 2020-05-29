from abc import ABC
import dataclasses
from typing import TypeVar, Type, Any, Optional, Iterator, Union

from google.cloud import firestore, firestore_v1
from google.cloud.firestore_v1.proto.write_pb2 import WriteResult
from google.protobuf.timestamp_pb2 import Timestamp
from typing_extensions import Literal

from fireclass.values_conversion import convert_value_to_firestore, convert_value_from_firestore

_firestore_client: Optional[firestore.Client] = None


def initialize_with_firestore_client(db: firestore.Client) -> None:
    global _firestore_client
    _firestore_client = db


def _discard_firestore_client() -> None:
    """Only to be used by the test suite.
    """
    global _firestore_client
    _firestore_client = None


class FirestoreClientNotConfigured(Exception):
    pass


def _get_firestore_client() -> firestore.Client:
    if _firestore_client is None:
        raise FirestoreClientNotConfigured(
            f"Fireclass has not been initialized with a firestore.Client;"
            f" see {initialize_with_firestore_client.__name__}() for more details."
        )
    return _firestore_client


class DocumentNotFound(Exception):
    pass


class DocumentNotCreatedInDatabase(Exception):
    pass


class DocumentAlreadyCreatedInDatabase(Exception):
    pass


_DocumentSubclassTypeVar = TypeVar("_DocumentSubclassTypeVar", bound="Document")
FirestoreOperator = Literal["<", "<=", "==", ">=", ">", "array_contains"]


class _DocumentQuery:
    def __init__(self, document_cls: Type[_DocumentSubclassTypeVar], firestore_query: firestore_v1.Query) -> None:
        self._document_cls = document_cls
        self._firestore_query = firestore_query

    def limit(self, count: int) -> "_DocumentQuery":
        new_query = self._firestore_query.limit(count)
        return _DocumentQuery(self._document_cls, new_query)

    def stream(self, transaction: Optional[firestore_v1.Transaction] = None) -> Iterator[_DocumentSubclassTypeVar]:
        for firestore_document in self._firestore_query.stream(transaction):
            yield self._document_cls._from_firestore_document(firestore_document)

    def where(
        self, field_path: str, op_string: FirestoreOperator, value: Any
    ) -> "_DocumentQuery":
        return _DocumentQuery(self._document_cls, self._firestore_query.where(field_path, op_string, value))


@dataclasses.dataclass
class Document(ABC):
    def __post_init__(self) -> None:
        self._id: Optional[str] = None  # Set when the document was saved to the DB or retrieved from the DB

    @property
    def id(self) -> Optional[str]:
        return self._id

    def create(self, document_id: Optional[str] = None) -> WriteResult:
        if self.id is not None:
            raise DocumentAlreadyCreatedInDatabase()
        document_ref = self._collection().document(document_id)
        encoded_dict = convert_value_to_firestore(dataclasses.asdict(self))
        write_result = document_ref.create(encoded_dict)
        self._id = document_ref.id
        return write_result

    def update(self) -> WriteResult:
        if self.id is None:
            raise DocumentNotCreatedInDatabase()
        document_ref = self._collection().document(self.id)
        encoded_dict = convert_value_to_firestore(dataclasses.asdict(self))
        write_result = document_ref.update(encoded_dict)
        self._id = document_ref.id
        return write_result

    def delete(self) -> Timestamp:
        if self.id is None:
            raise DocumentNotCreatedInDatabase()
        return self.delete_document(self.id)

    @classmethod
    def _find_field(cls, field_name: str) -> dataclasses.Field:
        corresponding_field = None
        for defined_field in dataclasses.fields(cls):
            if defined_field.name == field_name:
                corresponding_field = defined_field

        if not corresponding_field:
            raise TypeError(f"The supplied field_path '{field_name}' does not exist on '{cls.__name__}'")

        return corresponding_field

    @classmethod
    def _from_firestore_document(
        cls: Type[_DocumentSubclassTypeVar], firestore_document: firestore_v1.DocumentSnapshot
    ) -> _DocumentSubclassTypeVar:
        """Convert a document as returned by the Firestore client to the corresponding fireclass.Document instance.
        """
        decoded_dict = {}
        for field_name, value in firestore_document.to_dict().items():
            field_description = cls._find_field(field_name)
            decoded_dict[field_name] = convert_value_from_firestore(value, field_description)

        document = cls(**decoded_dict)  # type: ignore
        document._id = firestore_document.id
        return document

    @classmethod
    def _collection(cls: Type[_DocumentSubclassTypeVar]) -> firestore_v1.CollectionReference:
        return _get_firestore_client().collection(cls.__name__)

    @classmethod
    def get_document(cls: Type[_DocumentSubclassTypeVar], document_id: str) -> _DocumentSubclassTypeVar:
        firestore_document = cls._collection().document(document_id).get()
        if not firestore_document or not firestore_document.exists:
            raise DocumentNotFound()
        return cls._from_firestore_document(firestore_document)

    @classmethod
    def delete_document(cls: Type[_DocumentSubclassTypeVar], document_id: str) -> Timestamp:
        return cls._collection().document(document_id).delete()

    @classmethod
    def stream(cls: Type[_DocumentSubclassTypeVar]) -> Iterator[_DocumentSubclassTypeVar]:
        for firestore_document in cls._collection().stream():
            yield cls._from_firestore_document(firestore_document)

    @classmethod
    def where(
        cls: Type[_DocumentSubclassTypeVar], field_path: str, op_string: FirestoreOperator, value: Any
    ) -> _DocumentQuery:
        # TODO: Add support for .
        # Check that the field exists
        corresponding_field = cls._find_field(field_path)

        # Check that the value has the right type
        should_raise_type_error = False
        if hasattr(corresponding_field.type, "__origin__") and corresponding_field.type.__origin__ == Union:
            # Special processing for Optional fields
            if corresponding_field.type.__args__[1] != type(None):  # noqa: E721
                # Sanity check as this should never happen: we only support Union when used for Optional[T]
                raise TypeError(f"Unsupported field type: {corresponding_field.name}: {corresponding_field.type}")

            if corresponding_field.type.__args__[0] != type(value) and value is not None:
                # The value is not None and is not of the expected type
                should_raise_type_error = True

        elif corresponding_field.type != type(value):
            should_raise_type_error = True

        if should_raise_type_error:
            raise TypeError(
                f"The supplied value '{value}' has type {type(value)} but the corresponding field"
                f" '{corresponding_field.name}' requires values of type {corresponding_field.type}."
            )

        # Support enum fields too
        final_value = convert_value_to_firestore(value)

        return _DocumentQuery(cls, cls._collection().where(field_path, op_string, final_value))
