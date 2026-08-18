from app.extensions import db
import csv
from io import StringIO

from app.models import Email


def create_contact(
    client,
    first_name="Vikram",
    last_name="Kadarla",
    emails=None,
    company="",
    phone="",
    birthday="",
):
    return client.post(
        "/api/contacts",
        json={
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "phone": phone,
            "birthday": birthday,
            "emails": emails or [],
        },
    )


def test_home_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Contacts" in response.data


def test_contact_list_starts_empty(client):
    response = client.get("/api/contacts")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_contact_with_multiple_emails(client, contact_payload):
    response = client.post("/api/contacts", json=contact_payload)
    body = response.get_json()

    assert response.status_code == 201
    assert body["first_name"] == "Vikram"
    assert body["emails"] == ["vikram@example.com", "vikram@work.com"]
    assert body["id"] > 0


def test_create_contact_trims_names_and_normalizes_emails(client):
    response = client.post(
        "/api/contacts",
        json={
            "first_name": "  Ana ",
            "last_name": " Li  ",
            "emails": [" ANA@EXAMPLE.COM "],
        },
    )

    assert response.status_code == 201
    assert response.get_json()["first_name"] == "Ana"
    assert response.get_json()["emails"] == ["ana@example.com"]


def test_optional_contact_details_are_saved(client):
    response = create_contact(
        client,
        company="AVB Marketing",
        phone="513-555-0123",
        birthday="1995-06-14",
    )
    body = response.get_json()

    assert response.status_code == 201
    assert body["company"] == "AVB Marketing"
    assert body["phone"] == "513-555-0123"
    assert body["birthday"] == "1995-06-14"


def test_invalid_phone_and_future_birthday_are_rejected(client):
    response = create_contact(
        client,
        phone="call me",
        birthday="2999-01-01",
    )
    errors = response.get_json()["errors"]

    assert response.status_code == 400
    assert errors["phone"] == "Enter a valid phone number."
    assert errors["birthday"] == "Birthday cannot be in the future."


def test_first_and_last_names_are_required(client):
    response = client.post(
        "/api/contacts",
        json={"first_name": "", "last_name": "", "emails": []},
    )
    errors = response.get_json()["errors"]

    assert response.status_code == 400
    assert errors["first_name"] == "First name is required."
    assert errors["last_name"] == "Last name is required."


def test_invalid_json_is_rejected(client):
    response = client.post(
        "/api/contacts",
        data="not json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "form" in response.get_json()["errors"]


def test_invalid_and_duplicate_emails_are_rejected(client):
    invalid_response = create_contact(client, emails=["not-an-email"])
    duplicate_response = create_contact(
        client,
        emails=["same@example.com", "SAME@example.com"],
    )

    assert invalid_response.status_code == 400
    assert invalid_response.get_json()["errors"]["email_fields"]["0"]
    assert duplicate_response.status_code == 400
    assert duplicate_response.get_json()["errors"]["email_fields"]["1"]


def test_contacts_are_sorted_and_searchable(client):
    create_contact(client, "Zara", "Young")
    create_contact(
        client,
        "Ana",
        "Bell",
        company="AVB Marketing",
        phone="513-555-0199",
    )
    create_contact(client, "Mike", "Smith")

    all_contacts = client.get("/api/contacts").get_json()
    search_results = client.get("/api/contacts?search=mike%20smith").get_json()
    company_results = client.get("/api/contacts?search=avb").get_json()
    phone_results = client.get("/api/contacts?search=0199").get_json()

    assert [contact["first_name"] for contact in all_contacts] == ["Ana", "Mike", "Zara"]
    assert len(search_results) == 1
    assert search_results[0]["last_name"] == "Smith"
    assert company_results[0]["first_name"] == "Ana"
    assert phone_results[0]["first_name"] == "Ana"


def test_get_unknown_contact_returns_404(client):
    response = client.get("/api/contacts/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Contact not found."


def test_update_contact_replaces_email_collection(client):
    created = create_contact(
        client,
        emails=["keep@example.com", "remove@example.com"],
    ).get_json()
    response = client.put(
        f"/api/contacts/{created['id']}",
        json={
            "first_name": "Updated",
            "last_name": "Person",
            "company": "New Company",
            "phone": "+1 (513) 555-0100",
            "birthday": "1990-02-03",
            "emails": ["keep@example.com", "new@example.com"],
        },
    )

    assert response.status_code == 200
    assert response.get_json()["first_name"] == "Updated"
    assert response.get_json()["company"] == "New Company"
    assert response.get_json()["birthday"] == "1990-02-03"
    assert response.get_json()["emails"] == [
        "keep@example.com",
        "new@example.com",
    ]


def test_delete_hides_contact_and_restore_brings_it_back(client, app):
    created = create_contact(client, emails=["one@example.com", "two@example.com"]).get_json()
    response = client.delete(f"/api/contacts/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/contacts/{created['id']}").status_code == 404
    assert client.get("/api/contacts").get_json() == []

    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Email.id))) == 2

    restored = client.post(f"/api/contacts/{created['id']}/restore")

    assert restored.status_code == 200
    assert restored.get_json()["emails"] == ["one@example.com", "two@example.com"]
    assert client.get(f"/api/contacts/{created['id']}").status_code == 200


def test_favorites_sort_first_and_can_be_unpinned(client):
    alpha = create_contact(client, "Ana", "Bell").get_json()
    zara = create_contact(client, "Zara", "Young").get_json()

    favorite_response = client.patch(
        f"/api/contacts/{zara['id']}/favorite",
        json={"is_favorite": True},
    )
    favorites_first = client.get("/api/contacts").get_json()

    assert favorite_response.status_code == 200
    assert favorite_response.get_json()["is_favorite"] is True
    assert [contact["id"] for contact in favorites_first] == [zara["id"], alpha["id"]]

    unpinned = client.patch(
        f"/api/contacts/{zara['id']}/favorite",
        json={"is_favorite": False},
    )

    assert unpinned.status_code == 200
    assert unpinned.get_json()["is_favorite"] is False


def test_favorite_endpoint_requires_a_boolean(client):
    created = create_contact(client).get_json()
    response = client.patch(
        f"/api/contacts/{created['id']}/favorite",
        json={"is_favorite": "yes"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "is_favorite must be true or false."


def test_csv_export_includes_active_contacts_and_all_emails(client):
    active = create_contact(
        client,
        first_name="Ana",
        last_name="Bell",
        emails=["ana@example.com", "ana@work.com"],
        company="AVB Marketing",
        birthday="1995-06-14",
    ).get_json()
    deleted = create_contact(client, "Hidden", "Person").get_json()
    client.patch(
        f"/api/contacts/{active['id']}/favorite",
        json={"is_favorite": True},
    )
    client.delete(f"/api/contacts/{deleted['id']}")

    response = client.get("/api/contacts/export")
    rows = list(csv.DictReader(StringIO(response.get_data(as_text=True))))

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert response.headers["Content-Disposition"] == "attachment; filename=contacts.csv"
    assert len(rows) == 1
    assert rows[0]["First Name"] == "Ana"
    assert rows[0]["Emails"] == "ana@example.com; ana@work.com"
    assert rows[0]["Favorite"] == "Yes"
