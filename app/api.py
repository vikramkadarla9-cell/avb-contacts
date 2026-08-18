import csv
from io import StringIO

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Contact, Email, utc_now
from .validation import validate_contact


api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/contacts")
def list_contacts():
    search = request.args.get("search", "").strip()
    # Soft-deleted rows stay out of every normal address-book view.
    statement = db.select(Contact).where(Contact.deleted_at.is_(None))

    if search:
        pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Contact.first_name.ilike(pattern),
                Contact.last_name.ilike(pattern),
                (Contact.first_name + " " + Contact.last_name).ilike(pattern),
                Contact.company.ilike(pattern),
                Contact.phone.ilike(pattern),
            )
        )

    statement = statement.order_by(
        Contact.is_favorite.desc(),
        func.lower(Contact.first_name),
        func.lower(Contact.last_name),
    )
    contacts = db.session.scalars(statement).all()
    return jsonify([contact.to_summary() for contact in contacts])


@api.get("/contacts/<int:contact_id>")
def get_contact(contact_id):
    contact = get_active_contact(contact_id)
    if contact is None:
        return jsonify({"error": "Contact not found."}), 404
    return jsonify(contact.to_dict())


@api.post("/contacts")
def create_contact():
    data, errors = validate_contact(request.get_json(silent=True))
    if errors:
        return jsonify({"errors": errors}), 400

    contact = Contact(
        first_name=data["first_name"],
        last_name=data["last_name"],
        company=data["company"],
        phone=data["phone"],
        birthday=data["birthday"],
        emails=[Email(address=address) for address in data["emails"]],
    )
    db.session.add(contact)

    if not commit_changes():
        return jsonify({"error": "The contact could not be saved."}), 409

    return jsonify(contact.to_dict()), 201


@api.put("/contacts/<int:contact_id>")
def update_contact(contact_id):
    contact = get_active_contact(contact_id)
    if contact is None:
        return jsonify({"error": "Contact not found."}), 404

    data, errors = validate_contact(request.get_json(silent=True))
    if errors:
        return jsonify({"errors": errors}), 400

    contact.first_name = data["first_name"]
    contact.last_name = data["last_name"]
    contact.company = data["company"]
    contact.phone = data["phone"]
    contact.birthday = data["birthday"]
    # Reuse unchanged rows so an edit does not delete and recreate every email.
    existing_emails = {email.address: email for email in contact.emails}
    contact.emails = [
        existing_emails.get(address, Email(address=address))
        for address in data["emails"]
    ]

    if not commit_changes():
        return jsonify({"error": "The contact could not be saved."}), 409

    return jsonify(contact.to_dict())


@api.delete("/contacts/<int:contact_id>")
def delete_contact(contact_id):
    contact = get_active_contact(contact_id)
    if contact is None:
        return jsonify({"error": "Contact not found."}), 404

    # Mark the row as deleted instead of removing it, allowing a later restore.
    contact.deleted_at = utc_now()
    db.session.commit()
    return "", 204


@api.post("/contacts/<int:contact_id>/restore")
def restore_contact(contact_id):
    contact = db.session.get(Contact, contact_id)
    if contact is None:
        return jsonify({"error": "Contact not found."}), 404
    if contact.deleted_at is None:
        return jsonify({"error": "Contact is not deleted."}), 409

    contact.deleted_at = None
    db.session.commit()
    return jsonify(contact.to_dict())


@api.patch("/contacts/<int:contact_id>/favorite")
def set_favorite(contact_id):
    contact = get_active_contact(contact_id)
    if contact is None:
        return jsonify({"error": "Contact not found."}), 404

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or type(payload.get("is_favorite")) is not bool:
        return jsonify({"error": "is_favorite must be true or false."}), 400

    contact.is_favorite = payload["is_favorite"]
    db.session.commit()
    return jsonify(contact.to_dict())


@api.get("/contacts/export")
def export_contacts():
    statement = (
        db.select(Contact)
        .where(Contact.deleted_at.is_(None))
        .order_by(
            Contact.is_favorite.desc(),
            func.lower(Contact.first_name),
            func.lower(Contact.last_name),
        )
    )
    contacts = db.session.scalars(statement).all()

    # csv.writer safely escapes commas and quotes in user-entered values.
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "First Name",
        "Last Name",
        "Company",
        "Phone",
        "Birthday",
        "Emails",
        "Favorite",
    ])
    for contact in contacts:
        writer.writerow(
            [
                contact.first_name,
                contact.last_name,
                contact.company or "",
                contact.phone or "",
                contact.birthday.isoformat() if contact.birthday else "",
                "; ".join(email.address for email in contact.emails),
                "Yes" if contact.is_favorite else "No",
            ]
        )

    return Response(
        output.getvalue(),
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


def get_active_contact(contact_id):
    statement = db.select(Contact).where(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    )
    return db.session.scalar(statement)


def commit_changes():
    # Keep a failed write from leaving the SQLAlchemy session unusable.
    try:
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
