import os
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, session, flash, send_from_directory
)
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from werkzeug.utils import secure_filename

from config import Config
from models import (
    db, Report, StatusEvent, StaffUser, CitizenUser, Notification,
    CATEGORY_DEPARTMENTS, CATEGORY_LABELS, STATUS_FLOW, STATUS_LABELS
)
from mistral_service import classify_report


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    _ensure_mysql_database_exists(app)

    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
        except OperationalError as error:
            # Flask's debug reloader can race while creating a new MySQL table.
            if "already exists" not in str(error).lower():
                raise
            db.session.rollback()
        _ensure_citizen_report_column()

    register_routes(app)
    register_cli(app)
    return app


def _ensure_mysql_database_exists(app):
    """XAMPP/phpMyAdmin ships with an empty MySQL server: the schema itself
    (e.g. 'cityreport') has to exist before SQLAlchemy can connect to it.
    This creates it automatically on startup if it's missing, using the
    same credentials as SQLALCHEMY_DATABASE_URI."""
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql"):
        return
    try:
        import pymysql
        conn = pymysql.connect(
            host=app.config["DB_HOST"],
            port=int(app.config["DB_PORT"]),
            user=app.config["DB_USER"],
            password=app.config["DB_PASSWORD"],
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{app.config['DB_NAME']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        conn.close()
    except Exception as e:
        # Don't crash the whole app on import; surface a clear message instead
        print(f"[CityReport] Could not auto-create MySQL database: {e}")
        print("[CityReport] Make sure XAMPP's MySQL/Apache is running, "
              "then create the database manually via phpMyAdmin if needed.")


def _ensure_citizen_report_column():
    columns = {column["name"] for column in inspect(db.engine).get_columns("report")}
    if "citizen_id" not in columns:
        db.session.execute(text("ALTER TABLE report ADD COLUMN citizen_id INTEGER NULL"))
        db.session.commit()


def register_cli(app):
    @app.cli.command("create-admin")
    def create_admin():
        """flask create-admin — creates the staff login using ADMIN_EMAIL /
        ADMIN_PASSWORD from .env."""
        with app.app_context():
            email = app.config["ADMIN_EMAIL"]
            if StaffUser.query.filter_by(email=email).first():
                print(f"Admin '{email}' already exists.")
                return
            admin = StaffUser(email=email, name="City Administrator")
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.commit()
            print(f"Created staff admin: {email} / (password from ADMIN_PASSWORD in .env)")

    @app.cli.command("update-admin")
    def update_admin():
        """Update the existing staff login from ADMIN_EMAIL / ADMIN_PASSWORD."""
        with app.app_context():
            email = app.config["ADMIN_EMAIL"]
            admin = StaffUser.query.filter_by(email=email).first()
            if admin is None:
                admins = StaffUser.query.order_by(StaffUser.id).all()
                if len(admins) != 1:
                    print("Could not identify the existing admin. Use phpMyAdmin or remove extra staff accounts first.")
                    return
                admin = admins[0]

            admin.email = email
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.commit()
            print(f"Updated staff admin: {email}")

    @app.cli.command("init-db")
    def init_db():
        """flask init-db — (re)creates all tables in the configured MySQL database."""
        with app.app_context():
            db.create_all()
            print("Database tables created.")


def allowed_file(filename, app):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("staff_id"):
            return redirect(url_for("staff_login", next=request.path))
        return f(*args, **kwargs)
    return wrapped


def citizen_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("citizen_id"):
            return redirect(url_for("citizen_login", next=request.path))
        return f(*args, **kwargs)
    return wrapped


def make_reference():
    return "CR-" + uuid.uuid4().hex[:7].upper()


def register_routes(app):

    # ---------- Citizen-facing ----------

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            categories=CATEGORY_LABELS,
            default_lat=app.config["DEFAULT_LAT"],
            default_lng=app.config["DEFAULT_LNG"],
        )

    @app.route("/api/reports", methods=["GET"])
    def api_list_reports():
        query = Report.query
        category = request.args.get("category")
        status = request.args.get("status")
        if category:
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status)
        reports = query.order_by(Report.created_at.desc()).all()
        return jsonify([r.to_dict() for r in reports])

    @app.route("/api/reports/<reference>", methods=["GET"])
    def api_get_report(reference):
        r = Report.query.filter_by(reference=reference).first_or_404()
        data = r.to_dict()
        data["history"] = [
            {"status": h.status, "note": h.note, "created_at": h.created_at.isoformat()}
            for h in r.history
        ]
        return jsonify(data)

    @app.route("/api/classify-preview", methods=["POST"])
    def api_classify_preview():
        """Live AI preview while the citizen is still typing/attaching a photo
        in the report modal — mirrors CivicSpot's 'AI does the rest' preview."""
        description = (request.form.get("description") or "").strip()
        if not description:
            return jsonify({"error": "description required"}), 400

        photo = request.files.get("photo")
        photo_path = None
        if photo and photo.filename and allowed_file(photo.filename, app):
            tmp_name = f"preview_{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], tmp_name)
            photo.save(photo_path)

        result = classify_report(description, photo_path)

        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)  # preview only, not stored yet

        return jsonify(result)

    @app.route("/api/reports", methods=["POST"])
    def api_create_report():
        description = (request.form.get("description") or "").strip()
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        if not description or not lat or not lng:
            return jsonify({"error": "description, lat and lng are required"}), 400

        photo = request.files.get("photo")
        photo_filename = None
        photo_path = None
        if photo and photo.filename and allowed_file(photo.filename, app):
            photo_filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], photo_filename)
            photo.save(photo_path)

        # --- Mistral AI agent: classify + draft description + hazard score ---
        ai_result = classify_report(description, photo_path)

        category = ai_result["category"]
        report = Report(
            reference=make_reference(),
            category=category,
            department=CATEGORY_DEPARTMENTS.get(category, "General Services"),
            description=description,
            ai_summary=ai_result.get("summary"),
            hazard_level=ai_result.get("hazard_level", "low"),
            ai_confidence=ai_result.get("confidence", 0.0),
            photo_filename=photo_filename,
            lat=float(lat),
            lng=float(lng),
            address=request.form.get("address"),
            reporter_name=request.form.get("reporter_name"),
            reporter_contact=request.form.get("reporter_contact"),
            citizen_id=session.get("citizen_id"),
            status="received",
        )
        db.session.add(report)
        db.session.flush()
        db.session.add(StatusEvent(report_id=report.id, status="received", note="Report submitted"))
        location = request.form.get("address") or f"{report.lat:.5f}, {report.lng:.5f}"
        db.session.add(Notification(
            user_id=1,
            recipient_type="admin",
            message=f"New {CATEGORY_LABELS.get(category, category)} reported at {location} - REF {report.reference}",
            ref_code=report.reference,
        ))
        db.session.commit()

        return jsonify(report.to_dict()), 201

    @app.route("/track/<reference>")
    def track(reference):
        report = Report.query.filter_by(reference=reference).first_or_404()
        return render_template("track.html", report=report, status_flow=STATUS_FLOW,
                                status_labels=STATUS_LABELS)

    @app.route("/citizen/register", methods=["GET", "POST"])
    def citizen_register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or not email or not password:
                flash("Name, email, and password are required.", "error")
            elif len(password) < 8:
                flash("Password must be at least 8 characters.", "error")
            elif CitizenUser.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
            else:
                citizen = CitizenUser(name=name, email=email)
                citizen.set_password(password)
                db.session.add(citizen)
                db.session.commit()
                session["citizen_id"] = citizen.id
                session["citizen_name"] = citizen.name
                return redirect(url_for("citizen_dashboard"))
        return render_template("citizen_register.html")

    @app.route("/citizen/login", methods=["GET", "POST"])
    def citizen_login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            citizen = CitizenUser.query.filter_by(email=email).first()
            if citizen and citizen.check_password(password):
                session["citizen_id"] = citizen.id
                session["citizen_name"] = citizen.name
                return redirect(request.args.get("next") or url_for("citizen_dashboard"))
            flash("Invalid email or password.", "error")
        return render_template("citizen_login.html")

    @app.route("/citizen/logout")
    def citizen_logout():
        session.pop("citizen_id", None)
        session.pop("citizen_name", None)
        return redirect(url_for("index"))

    @app.route("/citizen/dashboard")
    @citizen_required
    def citizen_dashboard():
        reports = Report.query.filter_by(citizen_id=session["citizen_id"]).order_by(
            Report.created_at.desc()
        ).all()
        return render_template("citizen_dashboard.html", reports=reports,
                               categories=CATEGORY_LABELS, status_labels=STATUS_LABELS)

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ---------- Staff dashboard ----------

    @app.route("/staff/login", methods=["GET", "POST"])
    def staff_login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = StaffUser.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session["staff_id"] = user.id
                session["staff_name"] = user.name
                return redirect(request.args.get("next") or url_for("dashboard"))
            flash("Invalid email or password", "error")
        return render_template("login.html")

    @app.route("/staff/logout")
    def staff_logout():
        session.clear()
        return redirect(url_for("staff_login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        reports = Report.query.order_by(Report.created_at.desc()).all()
        stats = {
            "total": len(reports),
            "received": sum(1 for r in reports if r.status == "received"),
            "in_progress": sum(1 for r in reports if r.status == "in_progress"),
            "resolved": sum(1 for r in reports if r.status == "resolved"),
            "high_hazard": sum(1 for r in reports if r.hazard_level == "high"),
        }
        return render_template(
            "dashboard.html", reports=reports, stats=stats,
            categories=CATEGORY_LABELS, status_labels=STATUS_LABELS,
            status_flow=STATUS_FLOW,
        )

    @app.route("/api/reports/<int:report_id>/status", methods=["POST"])
    @app.route("/admin/update_status/<int:report_id>", methods=["POST"])
    @login_required
    def api_update_status(report_id):
        report = Report.query.get_or_404(report_id)
        payload = request.get_json(silent=True) or {}
        new_status = payload.get("status")
        note = payload.get("note") or payload.get("resolution_note", "")
        if new_status not in STATUS_FLOW:
            return jsonify({"error": "invalid status"}), 400
        report.status = new_status
        report.updated_at = datetime.utcnow()
        db.session.add(StatusEvent(report_id=report.id, status=new_status, note=note))
        if report.citizen_id:
            message = (
                f"Your report {report.reference} has been resolved. Note: {note or 'No additional note.'}"
                if new_status == "resolved" else
                f"Your report {report.reference} is now {new_status}. Note: {note or 'No additional note.'}"
            )
            db.session.add(Notification(
                user_id=report.citizen_id,
                recipient_type="citizen",
                message=message,
                ref_code=report.reference,
            ))
        db.session.commit()
        return jsonify(report.to_dict())

    @app.route("/notifications", methods=["GET"])
    def notifications():
        if session.get("staff_id"):
            user_id, recipient_type = session["staff_id"], "admin"
        elif session.get("citizen_id"):
            user_id, recipient_type = session["citizen_id"], "citizen"
        else:
            return jsonify({"notifications": [], "unread_count": 0}), 401

        items = Notification.query.filter_by(
            user_id=user_id, recipient_type=recipient_type, is_read=False
        ).order_by(Notification.created_at.desc()).all()
        return jsonify({
            "notifications": [
                {"id": item.id, "message": item.message, "ref_code": item.ref_code,
                 "created_at": item.created_at.isoformat()}
                for item in items
            ],
            "unread_count": len(items),
        })

    @app.route("/notifications/mark_read/<int:notification_id>", methods=["POST"])
    def mark_notification_read(notification_id):
        if session.get("staff_id"):
            user_id, recipient_type = session["staff_id"], "admin"
        elif session.get("citizen_id"):
            user_id, recipient_type = session["citizen_id"], "citizen"
        else:
            return jsonify({"error": "login required"}), 401

        item = Notification.query.filter_by(
            id=notification_id, user_id=user_id, recipient_type=recipient_type
        ).first_or_404()
        item.is_read = True
        db.session.commit()
        return jsonify({"ok": True})

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
