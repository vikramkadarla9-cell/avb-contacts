import os
from datetime import date
from pathlib import Path

from flask import Flask, render_template

from .api import api
from .extensions import db
from .models import Contact, Email


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # SQLite is the local default; deployment can provide another database URL.
    database_path = Path(app.instance_path) / "contacts.db"
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{database_path}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    app.register_blueprint(api)

    @app.get("/")
    def index():
        return render_template("index.html")

    # create_all keeps first-time setup simple for this self-contained assessment.
    with app.app_context():
        db.create_all()

    register_commands(app)
    return app


def register_commands(app):
    @app.cli.command("seed")
    def seed():
        """Add sample contacts when the database is empty."""
        if db.session.scalar(db.select(db.func.count(Contact.id))):
            print("The database already contains contacts.")
            return

        sample_contacts = [
            Contact(
                first_name="Andra",
                last_name="Inde",
                company="Northstar Design",
                phone="513-555-0101",
                birthday=date(1992, 4, 18),
                emails=[Email(address="andra.inde@example.com")],
            ),
            Contact(
                first_name="Archibald",
                last_name="Burns",
                emails=[Email(address="archibald.burns@example.com")],
            ),
            Contact(
                first_name="Berk",
                last_name="Carruth",
                emails=[Email(address="berk.carruth@example.com")],
            ),
            Contact(
                first_name="Craggy",
                last_name="Bramble",
                company="Marcham & Co.",
                phone="212-555-0138",
                birthday=date(1988, 10, 7),
                emails=[
                    Email(address="craggy.bramble@gmail.com"),
                    Email(address="cbramble@marcham.com"),
                    Email(address="craggy3029@yahoo.com"),
                ],
            ),
            Contact(
                first_name="Davita",
                last_name="de Juares",
                emails=[Email(address="davita@example.com")],
            ),
            Contact(
                first_name="Dione",
                last_name="Gibbett",
                emails=[Email(address="dione.gibbett@example.com")],
            ),
        ]

        db.session.add_all(sample_contacts)
        db.session.commit()
        print(f"Added {len(sample_contacts)} sample contacts.")
