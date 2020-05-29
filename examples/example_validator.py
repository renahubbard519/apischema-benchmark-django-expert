from dataclasses import dataclass, field
from pytest import raises

from apischema import (
    ValidationError,
    from_data,
    input_converter,
    output_converter,
    to_data,
    validator,
)


class Password(str):
    pass


# TODO handle inherited primitive
input_converter(Password, str, Password)


@output_converter
def hide_password(_: Password) -> str:
    return "******"


@dataclass
class ChangePasswordForm:
    password: Password = field()
    confirmation: Password

    @validator
    def password_match_confirmation(self):
        if self.password != self.confirmation:
            yield "password and its confirmation don't match"


def test_change_password_form():
    data = {"password": "5tr0ngP455w0rd!", "confirmation": "5tr0ngP455w0rd!"}
    form = from_data(ChangePasswordForm, data)
    assert form == ChangePasswordForm(
        Password("5tr0ngP455w0rd!"), Password("5tr0ngP455w0rd!")
    )
    assert to_data(form) == {
        "password": "******",
        "confirmation": "******",
    }


def test_bad_confirmation():
    data = {
        "password": "password",
        "confirmation": "1234",
    }
    with raises(ValidationError) as err:
        from_data(ChangePasswordForm, data)
    assert err.value == ValidationError(["password and its confirmation don't match"])


def test_missing_confirmation():
    data = {
        "password": "password",
    }
    with raises(ValidationError) as err:
        from_data(ChangePasswordForm, data)
    assert err.value == ValidationError(
        children={"confirmation": ValidationError(["missing field"])}
    )
