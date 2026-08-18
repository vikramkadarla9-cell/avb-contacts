import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.db"
    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
        }
    )

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def contact_payload():
    return {
        "first_name": "Vikram",
        "last_name": "Kadarla",
        "emails": ["vikram@example.com", "vikram@work.com"],
    }

