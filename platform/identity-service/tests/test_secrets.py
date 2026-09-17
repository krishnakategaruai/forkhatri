from uuid import uuid4

from app.components.identity.secrets import (
    constant_time_equal,
    hash_password,
    new_otp_code,
    new_session_token,
    otp_mac,
    token_digest,
    verify_password,
)


def test_session_tokens_are_unique_and_stored_as_32_byte_digests() -> None:
    first, second = new_session_token(), new_session_token()
    assert first != second
    assert len(first) >= 43
    assert len(token_digest(first)) == 32
    assert token_digest(first) != token_digest(second)


def test_otp_codes_are_six_digits() -> None:
    for _ in range(50):
        code = new_otp_code()
        assert len(code) == 6 and code.isdigit()


def test_otp_mac_is_bound_to_the_challenge_and_the_pepper() -> None:
    challenge = uuid4()
    mac = otp_mac("pepper", challenge, "123456")
    assert constant_time_equal(mac, otp_mac("pepper", challenge, "123456"))
    assert not constant_time_equal(mac, otp_mac("pepper", uuid4(), "123456"))
    assert not constant_time_equal(mac, otp_mac("other", challenge, "123456"))


def test_password_round_trip_and_missing_account_path() -> None:
    stored = hash_password("correct horse")
    assert stored.startswith("$argon2id$")
    assert verify_password(stored, "correct horse")
    assert not verify_password(stored, "wrong")
    assert not verify_password(None, "correct horse")
    assert not verify_password("not-a-hash", "correct horse")
