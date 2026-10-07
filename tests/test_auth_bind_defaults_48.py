"""Secure bind/auth defaults (#48)."""
import importlib
import os


def test_defaults_are_loopback_auth_on(monkeypatch):
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("AUTH_DISABLED", raising=False)
    import app.config as cfg
    importlib.reload(cfg)
    assert cfg.settings.HOST == "127.0.0.1"
    assert cfg.settings.AUTH_DISABLED is False
