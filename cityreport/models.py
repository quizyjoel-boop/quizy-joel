from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Category -> department routing table, mirrors the "Department Routing"
# feature: each category is auto-assigned to a city department.
CATEGORY_DEPARTMENTS = {
    "pothole": "Roads & Infrastructure",
    "streetlight": "Public Lighting",
    "waste": "Sanitation & Waste Management",
    "other": "General Services",
}

CATEGORY_LABELS = {
    "pothole": "Pothole / Road damage",
    "streetlight": "Broken streetlight",
    "waste": "Uncollected waste",
    "other": "Other / Uncategorised",
}

STATUS_FLOW = ["received", "in_progress", "resolved"]

STATUS_LABELS = {
    "received": "Received",
    "in_progress": "In progress",
    "resolved": "Resolved",
}


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(12), unique=True, nullable=False)

    category = db.Column(db.String(30), nullable=False, default="pothole")
    department = db.Column(db.String(80), nullable=False, default="Roads & Infrastructure")

    description = db.Column(db.Text, nullable=False)
    ai_summary = db.Column(db.Text)  # AI-polished description
    hazard_level = db.Column(db.String(10), default="low")  # low / medium / high
    ai_confidence = db.Column(db.Float, default=0.0)

    photo_filename = db.Column(db.String(255))

    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255))

    reporter_name = db.Column(db.String(120))
    reporter_contact = db.Column(db.String(120))
    citizen_id = db.Column(db.Integer, db.ForeignKey("citizen_user.id"), nullable=True)

    status = db.Column(db.String(20), default="received")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    history = db.relationship(
        "StatusEvent", backref="report", cascade="all, delete-orphan",
        order_by="StatusEvent.created_at"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "category": self.category,
            "category_label": CATEGORY_LABELS.get(self.category, "Other"),
            "department": self.department,
            "description": self.description,
            "ai_summary": self.ai_summary,
            "hazard_level": self.hazard_level,
            "ai_confidence": self.ai_confidence,
            "photo_filename": self.photo_filename,
            "lat": self.lat,
            "lng": self.lng,
            "address": self.address,
            "reporter_name": self.reporter_name,
            "status": self.status,
            "status_label": STATUS_LABELS.get(self.status, self.status),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class StatusEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("report.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    recipient_type = db.Column(db.String(20), nullable=False, default="citizen")
    message = db.Column(db.Text, nullable=False)
    ref_code = db.Column(db.String(12))
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StaffUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CitizenUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    reports = db.relationship("Report", backref="citizen", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
