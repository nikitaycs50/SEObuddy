"""Tests for shared models."""

from seobuddy.models import DEFAULT_USER_AGENT, AuditConfig


def test_default_user_agent_is_chrome_desktop() -> None:
    assert "Chrome" in DEFAULT_USER_AGENT
    assert "Mozilla/5.0" in DEFAULT_USER_AGENT
    assert AuditConfig().user_agent == DEFAULT_USER_AGENT
