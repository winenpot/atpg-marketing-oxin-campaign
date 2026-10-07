import pytest

from app.core.config import Settings


def test_settings_use_typed_defaults() -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.db_connect_timeout_seconds == 5
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.allowed_cors_origins == ["http://localhost:3000"]


def test_wildcard_cors_origin_is_supported() -> None:
    settings = Settings(cors_origins="*")

    assert settings.allowed_cors_origins == ["*"]


def test_development_can_use_local_database() -> None:
    settings = Settings(
        environment="development",
        database_url="postgresql+asyncpg://local:local@postgres:5432/lottery_passport",
    )

    assert settings.environment == "development"


def test_postgresql_database_urls_use_async_driver() -> None:
    settings = Settings(
        database_url="postgresql://user:password@db.example/lottery_passport"
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_demo_rejects_loopback_database() -> None:
    with pytest.raises(ValueError, match="external database"):
        Settings(
            environment="demo",
            database_url="postgresql+asyncpg://local:local@localhost:5432/lottery_passport",
            _env_file=None,
        )


def test_production_accepts_compose_service_database() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://app:secret@postgres:5432/lottery_passport",
        api_key="test-api-key",
        redemption_code_pepper="p" * 48,
        _env_file=None,
    )

    assert settings.environment == "production"


def test_production_rejects_a_short_or_blank_pepper() -> None:
    for pepper in ("too-short", "   "):
        with pytest.raises(ValueError, match="REDEMPTION_CODE_PEPPER"):
            Settings(
                environment="production",
                database_url="postgresql+asyncpg://app:secret@postgres:5432/db",
                api_key="test-api-key",
                redemption_code_pepper=pepper,
                _env_file=None,
            )


def test_blank_secrets_are_treated_as_unset() -> None:
    settings = Settings(redemption_code_pepper="", api_key=" ", _env_file=None)

    assert settings.redemption_code_pepper is None
    assert settings.api_key is None


def test_unknown_campaign_timezone_is_rejected() -> None:
    with pytest.raises(ValueError, match="time zone"):
        Settings(campaign_timezone="Mars/Olympus", _env_file=None)


def test_demo_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ValueError, match="API_KEY"):
        Settings(
            environment="demo",
            database_url="postgresql+asyncpg://user:password@db.example/lottery_passport",
            _env_file=None,
        )
