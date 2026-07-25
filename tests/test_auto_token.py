from scripts.auto_token import extract_auth


def test_extract_auth_lowercase_keys():
    headers = {
        "authorization": "Bearer abc123",
        "xi-csrf-token": "csrf-xyz",
        "x-appid": "3",
    }
    assert extract_auth(headers) == {
        "authorization": "Bearer abc123",
        "xi-csrf-token": "csrf-xyz",
        "x-appid": "3",
    }


def test_extract_auth_mixed_case_keys():
    headers = {
        "Authorization": "Bearer abc123",
        "Xi-Csrf-Token": "csrf-xyz",
    }
    result = extract_auth(headers)
    assert result["authorization"] == "Bearer abc123"
    assert result["xi-csrf-token"] == "csrf-xyz"
    assert result["x-appid"] == "3"  # 缺省值


def test_extract_auth_missing_authorization():
    assert extract_auth({"xi-csrf-token": "csrf-xyz"}) is None


def test_extract_auth_missing_csrf():
    assert extract_auth({"authorization": "Bearer abc123"}) is None


def test_extract_auth_empty():
    assert extract_auth({}) is None
