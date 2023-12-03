"""Module that contains basic presentation for the pydantic models."""
import pprint
import uuid
import json
from enum import IntEnum

from pydantic import BaseModel, EmailStr, SecretStr, Field


class FacultyCode(IntEnum):
    architecture = 1
    media_arts = 2
    computer_science = 3


class Account(BaseModel):
    email: EmailStr
    password: SecretStr


class Student(BaseModel):
    age: int = Field(ge=17)
    name: str = Field(pattern=r"^[a-zA-Z]+$", description="Sorry, E.Mask, no `Æ A-12` students are allowed!")
    account: Account
    title: str = Field(default="Student")
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    faculty: FacultyCode | None = None
    gender: str = Field(repr=False, strict=True, default=None)


if __name__ == "__main__":
    my_account_creds = Account(email="some@local.mail", password="s3cr3t_p@$s")
    student = Student(age=70, name="Alex", account=my_account_creds, gender="m")  # it's never too late to study!
    print(student)
    """>> Student(
        age=70 name='Alex'
        account=Account(email='some@local.mail', password=SecretStr('**********'))
        title='Student'
        id='53e259ce95434a7288e91458da609641'.
        faculty=None
    )
    """
    pprint.pp(student.model_dump(), sort_dicts=True)
    """
    >> {
        'account': {'email': 'some@local.mail', 'password': SecretStr('**********')},
        'age': 70,
        'faculty': None,
        'gender': 'm',
        'id': '53e259ce95434a7288e91458da609641',
        'name': 'Alex',
        'title': 'Student'
    }
    """
    print(student.model_dump_json(exclude={"gender"}))
    """>> '{
        "age": 70,
        "name": "Alex",
        "account": {"email": "some@local.mail", "password": "**********"},
        "title": "Student",
        "id": "53e259ce95434a7288e91458da609641",
        "faculty": null
    }'
    """

    # Here comes The Error
    wrong_json_model = json.dumps(
        dict(
            age=7,
            name="Æ A-12",
            account=dict(email="not_existing.email"),
            gender=True,
        )
    )
    student = Student.model_validate_json(json_data=wrong_json_model)
