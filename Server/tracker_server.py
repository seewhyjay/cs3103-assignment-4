from flask import Flask, send_file, jsonify
import sqlite3
import io
from datetime import datetime

# Flask app for tracking pixel and view counter
app = Flask(__name__)
DB_NAME = "email_tracking.db"


def init_tracking_db():
    """Initialize SQLite database for email tracking"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS email_opens
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT,
                  timestamp DATETIME)"""
    )
    conn.commit()
    conn.close()


@app.route("/pixel.png")
def tracking_pixel():
    """Serve 1x1 transparent pixel and log access"""
    # Create a 1x1 transparent PNG
    with open("1x1.png", "rb") as f:
        pixel = f.read()
    # Log the access
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO email_opens (timestamp) VALUES (?)", (datetime.now(),))
    conn.commit()
    conn.close()

    return send_file(io.BytesIO(pixel), mimetype="image/png")


@app.route("/stats")
def get_stats():
    """Return email open statistics"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM email_opens")
    count = c.fetchone()[0]
    conn.close()
    return jsonify({"opens": count})


if __name__ == "__main__":
    init_tracking_db()
    app.run(host="0.0.0.0", port=5182)
