from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Contact(db.Model):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    is_favorite: Mapped[bool] = mapped_column(default=False, nullable=False)
    # A timestamp hides deleted contacts while keeping them available for Undo.
    deleted_at: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    # delete-orphan removes an email row when it is removed from this collection.
    emails: Mapped[list["Email"]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
        order_by="Email.id",
    )

    def to_summary(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "phone": self.phone,
            "is_favorite": self.is_favorite,
        }

    def to_dict(self):
        return {
            **self.to_summary(),
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "emails": [email.address for email in self.emails],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Email(db.Model):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint("contact_id", "address", name="uq_contact_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    address: Mapped[str] = mapped_column(String(254), nullable=False)

    contact: Mapped[Contact] = relationship(back_populates="emails")
