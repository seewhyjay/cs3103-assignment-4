import smtplib
import csv
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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

    def read_template(self, filename):
        """Read template file with UTF-8 encoding"""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # If UTF-8 fails, try with utf-8-sig
            with open(filename, "r", encoding="utf-8-sig") as file:
                return file.read().strip()

    def read_templates(self, subject_file, body_file):
        """Read email template from files"""
        subject = self.read_template(subject_file)
        body = self.read_template(body_file)
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
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending to {to_email}: {str(e)}")
            return False

    def send_bulk_mail(self, csv_file, subject_file, body_file, department_code="all"):
        """Send bulk emails with department filtering"""
        # Read data and templates
        email_data = self.read_csv_data(csv_file)
        subject_template, body_template = self.read_templates(subject_file, body_file)

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


def main(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    csv_file: str,
    department: str,
):
    # Initialize mailer
    mailer = SmartMailer(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=password,
    )

    # Example usage
    stats = mailer.send_bulk_mail(
        csv_file=csv_file,
        subject_file="subject.txt",
        body_file="body.html",
        department_code=department,  # Or 'all' for all departments
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
    smtp_server = input("Enter SMTP server: ")
    smtp_port = int(input("Enter SMTP port: "))
    username = input("Enter username: ")
    password = input("Enter password: ")
    csv_file = input("Enter CSV file path: ")
    department = input("Enter department code or 'all': ")
    main(smtp_server, smtp_port, username, password, csv_file, department)
