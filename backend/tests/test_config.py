"""Settings parsing: database URL normalisation for managed Postgres providers."""

import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///./booking.db", "sqlite:///./booking.db"),
    ],
)
def test_database_url_is_normalised_to_psycopg(given: str, expected: str) -> None:
    settings = Settings(database_url=given, _env_file=None)
    assert settings.database_url == expected


def test_cors_origins_accept_comma_separated_string() -> None:
    settings = Settings(cors_origins="http://a.test, http://b.test", _env_file=None)
    assert settings.cors_origins == ["http://a.test", "http://b.test"]
