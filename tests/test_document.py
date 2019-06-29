from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from fireclass.document import Document


class UserMembershipLevelEnum(Enum):
    NONE = 1
    INTERMEDIATE = 2
    FULL = 3


@dataclass
class User(Document):
    """The model we use for our tests; it has a field of each type.
    """
    email_address: str = 'test@test.com'
    family_members_count : int = 5
    last_login_date: datetime = datetime.utcnow()
    membership: UserMembershipLevelEnum = UserMembershipLevelEnum.FULL
    is_active: bool = True


class TestDocument:

    def test_document_create_get_and_delete(self):
        pass

    def test_document_update(self):
        pass

    def test_get_document(self):
        pass

    def test_delete_document(self):
        pass

    def test_get(self):
        pass

    def test_where(self):
        pass
