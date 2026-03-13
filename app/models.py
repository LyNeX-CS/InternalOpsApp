# app/models.py
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    exclusions_created: so.Mapped[list['Exclusion']] = so.relationship(
        back_populates='created_by'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size
        )

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Policy(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255), nullable=True)

    exclusions: so.Mapped[list['Exclusion']] = so.relationship(
        back_populates='policy'
    )

    def __repr__(self):
        return f'<Policy {self.name}>'


class Exclusion(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    excluded_email: so.Mapped[str] = so.mapped_column(sa.String(254), index=True, nullable=False)
    until: so.Mapped[datetime.date] = so.mapped_column(sa.Date, nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    is_deleted: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, nullable=False)

    created_by_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), nullable=False)
    created_by: so.Mapped['User'] = so.relationship(back_populates='exclusions_created')

    policy_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('policy.id'), nullable=False)
    policy: so.Mapped['Policy'] = so.relationship(back_populates='exclusions')

    def __repr__(self):
        return f'<Exclusion {self.excluded_email} -> {self.policy.name}>'