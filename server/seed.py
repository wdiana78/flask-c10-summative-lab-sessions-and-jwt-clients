from app import app, bcrypt
from models import db, User, JournalEntry


def seed_database():
    with app.app_context():
        demo_username = "demo_user"
        demo_password = "DemoPass123"

        user = User.query.filter_by(username=demo_username).first()

        if user is None:
            user = User(
                username=demo_username,
                password_hash=bcrypt.generate_password_hash(
                    demo_password
                ).decode("utf-8"),
            )
            db.session.add(user)
            db.session.flush()

        if not user.journal_entries:
            entries = [
                JournalEntry(
                    title="Daily Priorities",
                    content="Identify the three most important tasks for today.",
                    mood="Focused",
                    user_id=user.id,
                ),
                JournalEntry(
                    title="A Small Win",
                    content="I made progress on a project I had been postponing.",
                    mood="Proud",
                    user_id=user.id,
                ),
                JournalEntry(
                    title="Reflection",
                    content="Tomorrow I will set aside time for reading and planning.",
                    mood="Hopeful",
                    user_id=user.id,
                ),
            ]

            db.session.add_all(entries)

        db.session.commit()
        print("Database seeding completed successfully.")


if __name__ == "__main__":
    seed_database()