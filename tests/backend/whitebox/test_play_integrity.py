"""Tests del verificador Play Integrity (servidor)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.play_integrity import verify_play_integrity_token


@pytest.fixture
def sa_path(tmp_path):
    p = tmp_path / "sa.json"
    p.write_text("{}", encoding="utf-8")
    return str(p)


def test_verify_rejects_empty_token(sa_path):
    r = verify_play_integrity_token("", "nonce", "com.app", sa_path)
    assert r.verdict == "FAIL"
    assert r.reason == "MISSING_INTEGRITY_TOKEN"


def test_verify_rejects_empty_nonce(sa_path):
    r = verify_play_integrity_token("token", "", "com.app", sa_path)
    assert r.verdict == "FAIL"
    assert r.reason == "MISSING_NONCE"


def test_verify_missing_sa_file():
    r = verify_play_integrity_token("t", "n", "com.app", "/no/such/file.json")
    assert r.verdict == "UNAVAILABLE"
    assert r.reason == "SERVICE_ACCOUNT_FILE_MISSING"


@patch("app.play_integrity.requests.post")
@patch("app.play_integrity.service_account.Credentials.from_service_account_file")
def test_verify_pass(mock_from_file, mock_post, sa_path):
    creds = MagicMock()
    creds.token = "access-token"
    mock_from_file.return_value = creds
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "tokenPayloadExternal": {
            "requestDetails": {"nonce": "abc"},
            "appIntegrity": {"appRecognitionVerdict": "PLAY_RECOGNIZED"},
            "deviceIntegrity": {"deviceRecognitionVerdict": ["MEETS_DEVICE_INTEGRITY"]},
        }
    }
    mock_post.return_value = mock_resp

    r = verify_play_integrity_token("integrity-jwt", "abc", "com.app", sa_path)
    assert r.verdict == "PASS"
    assert r.reason is None


@patch("app.play_integrity.requests.post")
@patch("app.play_integrity.service_account.Credentials.from_service_account_file")
def test_verify_nonce_mismatch(mock_from_file, mock_post, sa_path):
    creds = MagicMock()
    creds.token = "access-token"
    mock_from_file.return_value = creds
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "tokenPayloadExternal": {
            "requestDetails": {"nonce": "other"},
            "appIntegrity": {"appRecognitionVerdict": "PLAY_RECOGNIZED"},
            "deviceIntegrity": {"deviceRecognitionVerdict": ["MEETS_DEVICE_INTEGRITY"]},
        }
    }
    mock_post.return_value = mock_resp

    r = verify_play_integrity_token("integrity-jwt", "abc", "com.app", sa_path)
    assert r.verdict == "FAIL"
    assert r.reason == "NONCE_MISMATCH"


@patch("app.play_integrity.requests.post")
@patch("app.play_integrity.service_account.Credentials.from_service_account_file")
def test_verify_app_not_recognized(mock_from_file, mock_post, sa_path):
    creds = MagicMock()
    creds.token = "access-token"
    mock_from_file.return_value = creds
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "tokenPayloadExternal": {
            "requestDetails": {"nonce": "abc"},
            "appIntegrity": {"appRecognitionVerdict": "UNRECOGNIZED_VERSION"},
            "deviceIntegrity": {"deviceRecognitionVerdict": ["MEETS_DEVICE_INTEGRITY"]},
        }
    }
    mock_post.return_value = mock_resp

    r = verify_play_integrity_token("integrity-jwt", "abc", "com.app", sa_path)
    assert r.verdict == "FAIL"
    assert "APP_INTEGRITY" in (r.reason or "")
