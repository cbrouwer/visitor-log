from flask import Flask, render_template, request, redirect, g
import sqlite3
from datetime import datetime, timedelta
import pytz
from babel.dates import format_date

app = Flask(__name__)
DB_PATH = "notes.db"
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


@app.route("/")
def index():
    today = datetime.now(CEST).date()
    days = [today + timedelta(days=i) for i in range(14)]
    db = get_db()
    notes = db.execute("SELECT date, note FROM notes WHERE date BETWEEN ? AND ?",
                       (days[0].isoformat(), days[-1].isoformat())).fetchall()
    notes_by_date = {}
    for row in notes:
        notes_by_date.setdefault(row["date"], []).append(row["note"])
    return render_template("index.html", days=days, notes_by_date=notes_by_date)

@app.route("/add", methods=["POST"])
def add_note():
    date = request.form["date"]
    note = request.form["note"].strip()
    if note:
        db = get_db()
        db.execute("INSERT INTO notes (date, note) VALUES (?, ?)", (date, note))
        db.commit()
    # HTMX: return only the updated day's HTML
    updated_notes = db.execute("SELECT note FROM notes WHERE date = ?", (date,)).fetchall()
    return render_template("_day.html", date=date, notes=[n["note"] for n in updated_notes])

@app.template_filter("format_dutch_date")
def format_dutch_date(value):
    dt = datetime.strptime(value, "%Y-%m-%d") if isinstance(value, str) else value
    return format_date(dt, format="full", locale="nl_NL")

if __name__ == "__main__":
    with app.app_context():
        db = get_db()
        db.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.commit()
    app.run(debug=True)
