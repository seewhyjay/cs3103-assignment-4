import smtplib
import csv
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sqlite3
from flask import Flask, send_file, jsonify
import threading

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


class SmartMailer:
    def __init__(self, smtp_server, smtp_port, username, password):
        """Initialize mailer with SMTP server details"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.tracking_url = (
            "http://your-domain.com/pixel.png"  # Replace with actual domain
        )

    def read_csv_data(self, filename):
        """Read email data from CSV file"""
        data = []
        with open(filename, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data

    def read_template(self, subject_file, body_file):
        """Read email template from files"""
        with open(subject_file, "r") as file:
            subject = file.read().strip()

        with open(body_file, "r") as file:
            body = file.read().strip()

        return subject, body

    def personalize_content(self, template, replacements):
        """Replace placeholders in template with actual values"""
        content = template
        for key, value in replacements.items():
            placeholder = f"#{key}#"
            content = content.replace(placeholder, value)
        return content

    def add_tracking_pixel(self, html_content):
        """Add tracking pixel to HTML content"""
        pixel_tag = f'<img src="{self.tracking_url}" width="1" height="1" />'
        return html_content + pixel_tag

    def send_email(self, to_email, subject, body):
        """Send single email with HTML content"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.username
        msg["To"] = to_email

        html_part = MIMEText(body, "html")
        msg.attach(html_part)

        try:
            print(msg)
            # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            #     server.starttls()
            #     server.login(self.username, self.password)
            #     server.send_message(msg)
            # return True
        except Exception as e:
            print(f"Error sending to {to_email}: {str(e)}")
            return False

    def send_bulk_mail(self, csv_file, subject_file, body_file, department_code="all"):
        """Send bulk emails with department filtering"""
        # Read data and templates
        email_data = self.read_csv_data(csv_file)
        subject_template, body_template = self.read_template(subject_file, body_file)

        # Initialize department statistics
        dept_stats = {}

        for entry in email_data:
            # Skip if department doesn't match (unless 'all' is specified)
            if department_code != "all" and entry["department"] != department_code:
                continue

            # Personalize content
            personalized_subject = self.personalize_content(subject_template, entry)
            personalized_body = self.personalize_content(body_template, entry)
            tracked_body = self.add_tracking_pixel(personalized_body)

            # Send email
            success = self.send_email(
                entry["email"], personalized_subject, tracked_body
            )

            # Update statistics
            dept = entry["department"]
            if dept not in dept_stats:
                dept_stats[dept] = {"sent": 0, "failed": 0}
            if success:
                dept_stats[dept]["sent"] += 1
            else:
                dept_stats[dept]["failed"] += 1

            # Add random delay (2-5 seconds) to avoid spam detection
            time.sleep(random.uniform(2, 5))

        return dept_stats


def main():
    # Initialize tracking database
    init_tracking_db()

    # Start tracking server in a separate thread
    tracking_thread = threading.Thread(
        target=app.run, kwargs={"host": "0.0.0.0", "port": 5000}
    )
    tracking_thread.start()

    # Initialize mailer
    mailer = SmartMailer(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="your-email@gmail.com",  # Replace with actual email
        password="your-password",  # Replace with actual password
    )

    # Example usage
    stats = mailer.send_bulk_mail(
        csv_file="maildata.csv",
        subject_file="subject.txt",
        body_file="body.html",
        department_code="IT",  # Or 'all' for all departments
    )

    # Print report
    print("\nEmail Sending Report:")
    print("-" * 40)
    for dept, counts in stats.items():
        print(f"Department: {dept}")
        print(f"Sent: {counts['sent']}")
        print(f"Failed: {counts['failed']}")
        print("-" * 40)


if __name__ == "__main__":
    main()
