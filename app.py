from flask import Flask, render_template, request, g
import sqlite3
from datetime import datetime, timedelta
import pytz
from babel.dates import format_date
import click
from flask.cli import with_appcontext

app = Flask(__name__)
DB_PATH = "db/visitors.db"
CEST = pytz.timezone("Europe/Amsterdam")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.template_filter("format_dutch_date")
def format_dutch_date(value):
    from datetime import date
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return value
    if not isinstance(value, (datetime, date)):
        return value
    return format_date(value, format="full", locale="nl_NL")

@app.route("/marja/")
def index():
    today = datetime.now(CEST).date()
    upcoming = [today + timedelta(days=i) for i in range(14)]
    past = [today - timedelta(days=i) for i in range(1, 8)]

    db = get_db()
    # Get all visitors for the date range
    rows = db.execute("""
        SELECT id, date, visitor, part_of_day, status
        FROM visitors
        WHERE date BETWEEN ? AND ?
        AND (status = 'active' OR status = 'canceled')
        ORDER BY date, part_of_day, status = 'active' DESC, id DESC
    """, ((today - timedelta(days=7)).isoformat(), (today + timedelta(days=13)).isoformat())).fetchall()

    visitors_by_date = {}
    for row in rows:
        date_str = row["date"]
        if date_str not in visitors_by_date:
            visitors_by_date[date_str] = {}

        part_of_day = row["part_of_day"]
        if part_of_day not in visitors_by_date[date_str]:
            visitors_by_date[date_str][part_of_day] = []

        visitors_by_date[date_str][part_of_day].append({
            "id": row["id"],
            "visitor": row["visitor"],
            "status": row["status"]
        })

    return render_template("index.html", upcoming=upcoming, past=past, visitors_by_date=visitors_by_date, today=today)

@app.route("/marja/day/<date_str>")
def get_day(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date format", 400

    db = get_db()
    # Get all visitors for the day
    visitor_rows = db.execute("""
        SELECT id, visitor, part_of_day, status
        FROM visitors
        WHERE date = ? AND (status = 'active' OR status = 'canceled')
        ORDER BY part_of_day, status = 'active' DESC, id DESC
    """, (date_str,)).fetchall()

    visitors = {}
    for r in visitor_rows:
        part_of_day = r["part_of_day"]
        if part_of_day not in visitors:
            visitors[part_of_day] = []
        visitors[part_of_day].append({
            "id": r["id"],
            "visitor": r["visitor"],
            "status": r["status"]
        })

    today = datetime.now(CEST).date()
    return render_template("_day.html", date=date_str, visitors=visitors, today=today)

@app.route("/marja/add_visitor", methods=["POST"])
def add_visitor():
    db = get_db()
    date_str = request.form["date"]
    visitor = request.form["visitor"].strip()
    part_of_day = request.form["part_of_day"]
    if visitor:
        visitor = visitor[:60]
        try:
            # Check if there's an active visitor for this timeslot
            existing_active = db.execute(
                "SELECT id FROM visitors WHERE date = ? AND part_of_day = ? AND visitor = ? AND status = 'active'",
                (date_str, part_of_day, visitor)
            ).fetchone()

            if not existing_active:
                db.execute(
                    "INSERT INTO visitors (date, visitor, part_of_day, status) VALUES (?, ?, ?, 'active')",
                    (date_str, visitor, part_of_day)
                )
                db.commit()
        except sqlite3.IntegrityError as e:
            # Handle case where the same visitor is being added again
            print(f"Error adding visitor: {e}")
            pass

    # Return the updated day view
    return get_day(date_str)

@app.route("/marja/delete_visitor/<int:visitor_id>", methods=["POST"])
def delete_visitor(visitor_id):
    db = get_db()
    row = db.execute("SELECT date, part_of_day FROM visitors WHERE id = ?", (visitor_id,)).fetchone()
    if row:
        date_str = row["date"]
        part_of_day = row["part_of_day"]
        # Mark as canceled instead of deleting
        db.execute("UPDATE visitors SET status = 'canceled' WHERE id = ?", (visitor_id,))
        db.commit()

        # Return all visitors for the day, with active ones taking precedence
        return get_day(date_str)
    return "", 204

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initializes the database."""
    db = get_db()
    #db.execute("DROP TABLE IF EXISTS visitors")
    db.execute("""
    CREATE TABLE IF NOT EXISTS visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        visitor TEXT NOT NULL,
        part_of_day TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, part_of_day, status, visitor)
    )
    """)
    db.commit()
    click.echo("Initialized the database.")

app.cli.add_command(init_db_command)
