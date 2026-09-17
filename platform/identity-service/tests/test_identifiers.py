import pytest

from app.components.identity.identifiers import InvalidIdentifier, mask_email, mask_phone, normalize


@pytest.mark.parametrize(
    "raw",
    ["9876543210", "+919876543210", "09876543210", "919876543210", "98765 43210", "(987) 654-3210"],
)
def test_indian_mobile_forms_normalise_to_e164(raw: str) -> None:
    identifier = normalize(raw)
    assert identifier.kind == "phone"
    assert identifier.value == "+919876543210"
    assert identifier.channel == "sms"


def test_international_e164_is_kept() -> None:
    assert normalize("+14155550123").value == "+14155550123"


@pytest.mark.parametrize("raw", ["12345", "5876543210", "+0123456789", "call me", "+91 98765"])
def test_invalid_numbers_are_rejected(raw: str) -> None:
    with pytest.raises(InvalidIdentifier):
        normalize(raw)


def test_email_is_trimmed_and_lower_cased() -> None:
    identifier = normalize("  Asha.Reddy@Example.IN ")
    assert identifier.kind == "email"
    assert identifier.value == "asha.reddy@example.in"
    assert identifier.channel == "email"


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(InvalidIdentifier):
        normalize("asha@")


def test_masks_never_reveal_the_full_identifier() -> None:
    assert mask_phone("+919876543210") == "+91••••••3210"
    assert mask_email("asha.reddy@example.in") == "a•••@example.in"
