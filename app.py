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
    upcoming = [today + timedelta(days=i) for i in range(7)]  # Only next 7 days
    db = get_db()
    rows = db.execute("SELECT id, date, visitor, part_of_day FROM visitors WHERE date BETWEEN ? AND ?",
                      (today.isoformat(), (today + timedelta(days=6)).isoformat())).fetchall()
    visitors_by_date = {}
    for row in rows:
        date_str = row["date"]
        if date_str not in visitors_by_date:
            visitors_by_date[date_str] = {}
        visitors_by_date[date_str][row["part_of_day"]] = dict(id=row["id"], visitor=row["visitor"])

    return render_template("index.html", upcoming=upcoming, visitors_by_date=visitors_by_date, today=today)

@app.route("/marja/day/<date_str>")
def get_day(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date format", 400

    db = get_db()
    visitor_rows = db.execute("SELECT id, visitor, part_of_day FROM visitors WHERE date = ?", (date_str,)).fetchall()
    visitors = {}
    for r in visitor_rows:
        visitors[r["part_of_day"]] = dict(id=r["id"], visitor=r["visitor"])

    today = datetime.now(CEST).date()

    return render_template("_day.html", date=date_str, visitors=visitors, today=today)

@app.route("/marja/add_visitor", methods=["POST"])
def add_visitor():
    db = get_db()
    date_str = request.form["date"]
    visitor = request.form["visitor"].strip()
    part_of_day = request.form["part_of_day"]
    if visitor:
        visitor = visitor[:255]
        try:
            db.execute("INSERT INTO visitors (date, visitor, part_of_day) VALUES (?, ?, ?)", (date_str, visitor, part_of_day))
            db.commit()
        except sqlite3.IntegrityError:
            # Visitor for this part of day already exists, ignore.
            print("Visitor for this part of day already exists, ignoring. Date:", date_str, "Visitor:", visitor, "Part of day:", part_of_day)
            pass

    visitor_rows = db.execute("SELECT id, visitor, part_of_day FROM visitors WHERE date = ?", (date_str,)).fetchall()
    visitors = {}
    for row in visitor_rows:
        visitors[row["part_of_day"]] = dict(id=row["id"], visitor=row["visitor"])

    return render_template("_day.html", date=date_str, visitors=visitors, today=datetime.now(CEST).date())

@app.route("/marja/delete_visitor/<int:visitor_id>", methods=["POST"])
def delete_visitor(visitor_id):
    print("Deleting visitor", visitor_id)
    db = get_db()
    row = db.execute("SELECT date FROM visitors WHERE id = ?", (visitor_id,)).fetchone()
    if row:
        date_str = row["date"]
        db.execute("DELETE FROM visitors WHERE id = ?", (visitor_id,))
        db.commit()
        visitor_rows = db.execute("SELECT id, visitor, part_of_day FROM visitors WHERE date = ?", (date_str,)).fetchall()
        visitors = {}
        for r in visitor_rows:
            visitors[r["part_of_day"]] = dict(id=r["id"], visitor=r["visitor"])
        return render_template("_day.html", date=date_str, visitors=visitors, today=datetime.now(CEST).date())
    return "", 204

@app.route("/marja/update_visitor/<int:visitor_id>", methods=["POST"])
def update_visitor(visitor_id):
    db = get_db()
    visitor = request.form["visitor"].strip()
    if not visitor:
        return "Visitor name cannot be empty", 400

    visitor = visitor[:255]
    db.execute("UPDATE visitors SET visitor = ? WHERE id = ?", (visitor, visitor_id))
    db.commit()

    # Return the updated visitor info
    row = db.execute("SELECT date, part_of_day FROM visitors WHERE id = ?", (visitor_id,)).fetchone()
    if row:
        date_str = row["date"]
        visitor_rows = db.execute("SELECT id, visitor, part_of_day FROM visitors WHERE date = ?", (date_str,)).fetchall()
        visitors = {}
        for r in visitor_rows:
            visitors[r["part_of_day"]] = dict(id=r["id"], visitor=r["visitor"])
        return render_template("_day.html", date=date_str, visitors=visitors, today=datetime.now(CEST).date())

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, part_of_day)
    )
    """)
    db.execute("ALTER TABLE visitors ADD COLUMN visitor_long TEXT")
    db.commit()
    click.echo("Initialized the database.")

app.cli.add_command(init_db_command)
