from __future__ import annotations

from unittest.mock import patch, MagicMock

from api.upgrade import _get_vcc_dict, _get_account, PLATFORM_UPGRADERS


def test_get_vcc_dict_returns_none_when_no_active():
    with patch("api.upgrade.Session") as mock_session:
        mock_s = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_s)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_s.exec.return_value.first.return_value = None
        result = _get_vcc_dict(None)
        assert result is None


def test_get_vcc_dict_returns_card_data():
    mock_vcc = MagicMock()
    mock_vcc.number = "4111111111111111"
    mock_vcc.exp_month = 12
    mock_vcc.exp_year = 2029
    mock_vcc.cvc = "123"
    mock_vcc.billing_name = "John Smith"
    mock_vcc.billing_country = "US"
    mock_vcc.billing_line1 = "1 Market St"
    mock_vcc.billing_line2 = ""
    mock_vcc.billing_city = "San Francisco"
    mock_vcc.billing_state = "CA"
    mock_vcc.billing_postal_code = "94105"

    with patch("api.upgrade.Session") as mock_session:
        mock_s = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_s)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_s.get.return_value = mock_vcc
        result = _get_vcc_dict(1)
        assert result is not None
        assert result["number"] == "4111111111111111"
        assert result["expMonth"] == 12
        assert result["cvc"] == "123"
        assert result["billing"]["country"] == "US"
        assert result["billing"]["name"] == "John Smith"


def test_platform_upgraders_has_windsurf_and_kiro():
    assert "windsurf" in PLATFORM_UPGRADERS
    assert "kiro" in PLATFORM_UPGRADERS


def test_upgrade_windsurf_calls_generate_link():
    with patch("platforms.windsurf.plugin.WindsurfPlatform") as mock_platform_cls:
        mock_platform = MagicMock()
        mock_platform_cls.return_value = mock_platform
        mock_platform.execute_action.return_value = {"ok": True, "data": {"checkout_url": "https://checkout.stripe.com/test"}}

        from api.upgrade import _upgrade_windsurf
        account_data = {
            "email": "test@test.com",
            "password": "",
            "extra": {"session_token": "token123", "account_id": "acc-1", "org_id": "org-1"},
        }
        result = _upgrade_windsurf(account_data, None, True, 180, "pause")
        assert result["ok"] is True


def test_upgrade_windsurf_with_vcc_calls_generate_link_browser():
    with patch("platforms.windsurf.plugin.WindsurfPlatform") as mock_platform_cls:
        mock_platform = MagicMock()
        mock_platform_cls.return_value = mock_platform
        mock_platform.execute_action.return_value = {"ok": True, "data": {"card_outcome": {"kind": "success"}}}

        from api.upgrade import _upgrade_windsurf
        account_data = {
            "email": "test@test.com",
            "password": "",
            "extra": {"session_token": "token123"},
        }
        vcc = {"number": "4111111111111111", "expMonth": 12, "expYear": 2029, "cvc": "123", "billing": {"country": "US"}}
        result = _upgrade_windsurf(account_data, vcc, True, 180, "pause")
        assert result["ok"] is True


def test_upgrade_kiro_calls_upgrade_kiro_to_pro():
    with patch("platforms.kiro.kiro_upgrade.upgrade_kiro_to_pro") as mock_upgrade:
        mock_upgrade.return_value = {"ok": True, "data": {"message": "Already Pro"}}

        from api.upgrade import _upgrade_kiro
        account_data = {
            "email": "test@kiro.dev",
            "password": "pass123",
            "extra": {"accessToken": "token", "refreshToken": "refresh"},
        }
        result = _upgrade_kiro(account_data, None, True, 180, "pause")
        assert result["ok"] is True
        mock_upgrade.assert_called_once()
