"""
Tests for the core.config module.
"""

import os
from unittest import mock

import pytest
from pydantic import ValidationError

from translator.core.config import Settings, get_settings


class TestSettings:
    """Test cases for the Settings class."""

    def test_default_values(self):
        """Test that default values are correctly loaded."""
        # 注意：这个测试会受到 .env 文件中设置的影响
        # 我们只测试一些基本设置，不测试可能被环境变量覆盖的值
        settings = Settings()
        assert settings.PROJECT_NAME == "Translator"
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_FORMAT == "json"
        assert settings.OPENAI_MODEL == "gpt-4o"
        assert settings.MAX_CONCURRENT_REQUESTS == 5

    def test_env_override(self):
        """Test that environment variables override default values."""
        with mock.patch.dict(
            os.environ,
            {
                "DEBUG": "false",
                "LOG_LEVEL": "DEBUG",
                "LOG_FORMAT": "console",
                "OPENAI_MODEL": "gpt-4o-mini",
                "MAX_CONCURRENT_REQUESTS": "10",
            },
        ):
            settings = Settings()
            assert settings.DEBUG is False
            assert settings.LOG_LEVEL == "DEBUG"
            assert settings.LOG_FORMAT == "console"
            assert settings.OPENAI_MODEL == "gpt-4o-mini"
            assert settings.MAX_CONCURRENT_REQUESTS == 10

    def test_case_sensitivity(self):
        """Test that environment variables are case-sensitive."""
        # 在 model_config 中设置了 case_sensitive=True，所以环境变量是大小写敏感的
        with mock.patch.dict(
            os.environ,
            {
                "DEBUG": "false",  # 正确的大写形式
                "debug": "true",  # 不会被识别的小写形式
            },
        ):
            settings = Settings()
            # 验证只有大写的 DEBUG 被识别
            assert settings.DEBUG is False

    def test_validation(self):
        """Test that validation works for settings."""
        with mock.patch.dict(os.environ, {
                "MAX_CONCURRENT_REQUESTS": "not_an_integer"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_api_keys(self):
        """Test that API keys are properly loaded from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test_openai_key",
                "DEEPSEEK_API_KEY": "test_deepseek_key",
            },
        ):
            settings = Settings()
            assert settings.OPENAI_API_KEY == "test_openai_key"
            assert settings.DEEPSEEK_API_KEY == "test_deepseek_key"


def test_get_settings():
    """Test that get_settings returns the global settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    # Verify it's a singleton
    assert settings is get_settings()
