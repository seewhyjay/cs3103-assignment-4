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
    pixel = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe5\x27\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82"

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
    app.run(host="0.0.0.0", port=5010)
