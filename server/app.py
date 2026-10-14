
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from models import db, User, JournalEntry

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///productivity.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing. Check your server/.env file."
    )

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)


@app.get("/")
def home():
    return jsonify({"message": "Productivity API is running"}), 200


@app.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "")
    password = data.get("password", "")
    password_confirmation = data.get("password_confirmation", "")

    if not isinstance(username, str) or not username.strip():
        return jsonify({"errors": ["Username is required."]}), 400

    username = username.strip()

    if len(username) > 80:
        return jsonify({
            "errors": ["Username must be 80 characters or fewer."]
        }), 400

    if not isinstance(password, str) or len(password) < 8:
        return jsonify({
            "errors": ["Password must contain at least 8 characters."]
        }), 400

    if password != password_confirmation:
        return jsonify({"errors": ["Passwords do not match."]}), 400

    user = User(
        username=username,
        password_hash=bcrypt.generate_password_hash(
            password
        ).decode("utf-8"),
    )

    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"errors": ["Username is already taken."]}), 409

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": token,
        "user": {"id": user.id, "username": user.username},
    }), 201


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "")
    password = data.get("password", "")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"errors": ["Invalid username or password."]}), 401

    user = User.query.filter_by(username=username.strip()).first()

    if user is None or not bcrypt.check_password_hash(
        user.password_hash, password
    ):
        return jsonify({"errors": ["Invalid username or password."]}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": token,
        "user": {"id": user.id, "username": user.username},
    }), 200


@app.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"errors": ["User not found."]}), 404

    return jsonify({"id": user.id, "username": user.username}), 200


def get_owned_entry(entry_id):
    user_id = int(get_jwt_identity())

    return JournalEntry.query.filter_by(
        id=entry_id,
        user_id=user_id,
    ).first()


def entry_to_dict(entry):
    return {
        "id": entry.id,
        "title": entry.title,
        "content": entry.content,
        "mood": entry.mood,
        "user_id": entry.user_id,
    }


@app.post("/journal_entries")
@jwt_required()
def create_journal_entry():
    data = request.get_json(silent=True) or {}

    title = data.get("title")
    content = data.get("content")
    mood = data.get("mood")

    errors = []

    if not isinstance(title, str) or not title.strip():
        errors.append("Title is required.")
    elif len(title.strip()) > 120:
        errors.append("Title must be 120 characters or fewer.")

    if not isinstance(content, str) or not content.strip():
        errors.append("Content is required.")

    if not isinstance(mood, str) or not mood.strip():
        errors.append("Mood is required.")
    elif len(mood.strip()) > 50:
        errors.append("Mood must be 50 characters or fewer.")

    if errors:
        return jsonify({"errors": errors}), 400

    entry = JournalEntry(
        title=title.strip(),
        content=content.strip(),
        mood=mood.strip(),
        user_id=int(get_jwt_identity()),
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify(entry_to_dict(entry)), 201


@app.get("/journal_entries")
@jwt_required()
def list_journal_entries():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except (TypeError, ValueError):
        return jsonify({
            "errors": ["Page and per_page must be integers."]
        }), 400

    if page < 1 or per_page < 1 or per_page > 100:
        return jsonify({
            "errors": [
                "Page must be at least 1 and per_page must be between 1 and 100."
            ]
        }), 400

    user_id = int(get_jwt_identity())

    pagination = (
        JournalEntry.query
        .filter_by(user_id=user_id)
        .order_by(JournalEntry.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "entries": [
            entry_to_dict(entry) for entry in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_entries": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200


@app.get("/journal_entries/<int:entry_id>")
@jwt_required()
def get_journal_entry(entry_id):
    entry = get_owned_entry(entry_id)

    if entry is None:
        return jsonify({"errors": ["Journal entry not found."]}), 404

    return jsonify(entry_to_dict(entry)), 200


@app.patch("/journal_entries/<int:entry_id>")
@jwt_required()
def update_journal_entry(entry_id):
    entry = get_owned_entry(entry_id)

    if entry is None:
        return jsonify({"errors": ["Journal entry not found."]}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"errors": ["Provide fields to update."]}), 400

    errors = []

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            errors.append("Title cannot be empty.")
        elif len(title.strip()) > 120:
            errors.append("Title must be 120 characters or fewer.")
        else:
            entry.title = title.strip()

    if "content" in data:
        content = data["content"]
        if not isinstance(content, str) or not content.strip():
            errors.append("Content cannot be empty.")
        else:
            entry.content = content.strip()

    if "mood" in data:
        mood = data["mood"]
        if not isinstance(mood, str) or not mood.strip():
            errors.append("Mood cannot be empty.")
        elif len(mood.strip()) > 50:
            errors.append("Mood must be 50 characters or fewer.")
        else:
            entry.mood = mood.strip()

    if errors:
        db.session.rollback()
        return jsonify({"errors": errors}), 400

    db.session.commit()

    return jsonify(entry_to_dict(entry)), 200


@app.delete("/journal_entries/<int:entry_id>")
@jwt_required()
def delete_journal_entry(entry_id):
    entry = get_owned_entry(entry_id)

    if entry is None:
        return jsonify({"errors": ["Journal entry not found."]}), 404

    db.session.delete(entry)
    db.session.commit()

    return jsonify({"message": "Journal entry deleted successfully."}), 200


if __name__ == "__main__":
    app.run(port=5555, debug=True)
