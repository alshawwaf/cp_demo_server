import smtplib
import json, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'email_config')
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

CONFIG_FILE = os.path.join(CONFIG_DIR, 'email_config')    

import ssl

def send_email(
    smtp_server, port, sender_email, sender_password, recipient_email, subject, body, 
    encryption_type="STARTTLS", tls_ssl_version=None, attachment_path=None
):
    """
    Sends an email using the provided configuration with an optional attachment.

    :param smtp_server: SMTP server address
    :param port: SMTP server port
    :param sender_email: Sender's email address
    :param sender_password: Sender's email password
    :param recipient_email: Recipient's email address
    :param subject: Email subject
    :param body: Email body
    :param encryption_type: Type of encryption ("STARTTLS", "SSL", or "None")
    :param tls_ssl_version: SSL/TLS version to use (e.g., ssl.PROTOCOL_TLSv1_2)
    :param attachment_path: Path to the file to attach (optional)
    """
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))



        # Set up the SSL/TLS context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        server = smtplib.SMTP(smtp_server, port)

        if encryption_type.upper() == "STARTTLS":
            server.starttls(context=context)

        # Login to the server
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        return {"status": "success", "message": f"Email sent successfully to {recipient_email}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def save_email_config(config):
    """
    Saves email configuration to a JSON file.
    :param config: A dictionary containing email configuration.
    """
    with open(CONFIG_FILE, "w") as config_file:
        json.dump(config, config_file, indent=4)


def load_email_config():
    """
    Loads email configuration from a JSON file.
    :return: A dictionary containing email configuration, or None if the file doesn't exist.
    """
    try:
        with open(CONFIG_FILE, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        return None
