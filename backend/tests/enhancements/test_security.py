"""
Tests for StrategyVault - Security Features
Tests JWT configuration, CORS, and rate limiting.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi.testclient import TestClient


class TestJWTConfiguration:
    """Test JWT secret key configuration."""

    def test_default_jwt_secret_warns_in_dev(self):
        """In development mode, default JWT secret is accepted with a warning."""
        # Ensure we're not in production
        os.environ.pop("ENV", None)
        from src.core.config import Settings
        settings = Settings(JWT_SECRET_KEY="change-this-in-production")
        assert settings.JWT_SECRET_KEY == "change-this-in-production"

    def test_production_jwt_secret_must_be_changed(self):
        """In production mode, default JWT secret raises ValueError."""
        os.environ["ENV"] = "production"
        from src.core.config import Settings
        try:
            with pytest.raises(Exception):
                Settings(
                    JWT_SECRET_KEY="change-this-in-production",
                    _env_file=None,  # Don't read .env for this test
                )
        finally:
            os.environ.pop("ENV", None)

    def test_custom_jwt_secret_accepted(self):
        """Custom JWT secret is accepted in any environment."""
        from src.core.config import Settings
        settings = Settings(JWT_SECRET_KEY="my-super-secure-secret-key-2024")
        assert settings.JWT_SECRET_KEY == "my-super-secure-secret-key-2024"


class TestCORSConfiguration:
    """Test CORS origin configuration."""

    def test_single_cors_origin(self):
        """Single CORS origin is parsed correctly."""
        from src.core.config import Settings
        settings = Settings(CORS_ORIGINS="http://localhost:3000")
        assert settings.cors_origins_list == ["http://localhost:3000"]

    def test_multiple_cors_origins(self):
        """Multiple comma-separated CORS origins are parsed correctly."""
        from src.core.config import Settings
        settings = Settings(CORS_ORIGINS="http://localhost:3000,https://app.strategyvault.io")
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "https://app.strategyvault.io",
        ]

    def test_cors_origins_strips_whitespace(self):
        """Whitespace around origins is stripped."""
        from src.core.config import Settings
        settings = Settings(CORS_ORIGINS="  http://localhost:3000 , https://example.com  ")
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "https://example.com",
        ]

    def test_cors_headers_present(self):
        """CORS headers are present in responses for allowed origins."""
        from main import app
        client = TestClient(app)
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestRateLimiting:
    """Test API rate limiting configuration."""

    def test_rate_limit_config_exists(self):
        """Rate limiting configuration is set."""
        from src.core.config import settings
        assert hasattr(settings, "RATE_LIMIT_PER_MINUTE")
        assert settings.RATE_LIMIT_PER_MINUTE > 0

    def test_health_check_accessible(self):
        """Health check endpoint is accessible."""
        from main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200


class TestEnvExample:
    """Test that .env.example does not contain real secrets."""

    def test_env_example_has_no_real_api_key(self):
        """Ensure .env.example has placeholder values, not real API keys."""
        env_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '.env.example'
        )
        if os.path.exists(env_path):
            with open(env_path) as f:
                content = f.read()
            # Should not contain strings that look like real API keys
            assert "AIzaSy" not in content, ".env.example contains a real Google API key!"
            assert "sk-" not in content, ".env.example contains a real OpenAI API key!"
            # Should contain placeholders
            assert "your_gemini_api_key" in content

    def test_gitignore_excludes_env(self):
        """Ensure .gitignore excludes .env files."""
        gitignore_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '.gitignore'
        )
        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                content = f.read()
            assert ".env" in content


class TestConfigDefaults:
    """Test configuration default values."""

    def test_default_config_values(self):
        """Verify key default values are sensible."""
        from src.core.config import settings
        assert settings.APP_NAME == "StrategyVault"
        assert settings.BACKTEST_COMMISSION > 0
        assert settings.BACKTEST_SLIPPAGE >= 0
        assert settings.MAX_PIPELINE_RETRIES >= 1
        assert settings.CACHE_TTL_SECONDS > 0
        assert len(settings.DEFAULT_BACKTEST_ASSETS) > 0

    def test_quality_thresholds_ordered(self):
        """Quality thresholds must be in descending order."""
        from src.core.config import settings
        assert settings.GOLD_SCORE_THRESHOLD > settings.SILVER_SCORE_THRESHOLD
        assert settings.SILVER_SCORE_THRESHOLD > settings.BRONZE_SCORE_THRESHOLD
