"""This module shows basics of pydantic validators"""
from typing_extensions import Annotated
from contextlib import suppress
from pydantic import ValidationError, BaseModel, ValidationInfo, Field, ConfigDict, create_model, InstanceOf
from pydantic.functional_validators import AfterValidator, model_validator, field_validator


def check_squares(v: int) -> int:
    assert v**0.5 % 1 == 0, f"{v} is not a squared number!"
    return v


def double(v: int) -> int:
    return v * 2


class MuSquaredNumber(BaseModel):
    num: list[Annotated[int, AfterValidator(double), AfterValidator(check_squares)]]


class DogBreed:
    def __repr__(self):
        return self.__class__.__name__


# noinspection PyNestedDecorators
class DogAccount(BaseModel):
    # to use arbitrary, not python/pydantic field types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    username: str
    password1: str = Field(repr=False, default=None)
    password2: str = Field(repr=False, default=None)
    breed: InstanceOf[DogBreed] = None  # instance validator

    # when only a field validation is required
    @field_validator("username")
    @classmethod
    def validate_username(cls, val: str, field: ValidationInfo) -> str:
        assert val.isalnum(), f"{field.field_name} must be alphanumeric!"
        return val

    # when validation of the whole model is required before or after init
    @model_validator(mode="after")
    def validate_passwords_match(self) -> "DogAccount":
        assert self.password1 == self.password2, "passwords don't match!"
        return self


if __name__ == "__main__":
    try:
        print(MuSquaredNumber(num=[2, 8]))
        # > MuSquaredNumber(num=4, 16])
        print(MuSquaredNumber(num=[2, 4]))
        """
        1 validation error for MuSquaredNumber
        num.1
          Assertion failed, 8 is not a squared number! [type=assertion_error, input_value=4, input_type=int]
            For further information visit https://errors.pydantic.dev/2.5/v/assertion_error
        """

    except ValidationError as err:
        print(err)

    with suppress(ValidationError):
        DogAccount(username="$Barky$")
        """
        1 validation error for DogAccount
        username
          Assertion failed, username must be alphanumeric!
            [type=assertion_error, input_value='$Barky$', input_type=str]
        """
        DogAccount(username="Barky12", password1="some_p4$s", password2="p4$s_some")
        """
        1 validation error for DogAccount
          Assertion failed, passwords don't match!
            [
                type=assertion_error,
                input_value={'username': 'Alex12', 'p...password2': 'p4$s_some'},
                input_type=dict
            ]
        """
        DogAccount(
            username="kitty",
            # yep, one more cool pydantic feature: dynamic model creation
            breed=create_model("CatBreed", name=(str, ...))(name="Bombay"),
        )
        """
        1 validation error for DogAccount
        breed
          Input should be an instance of DogBreed
            [type=is_instance_of, input_value=CatBreed(name='Bombay'), input_type=CatBreed]
        """
