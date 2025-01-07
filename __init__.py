# __init__.py

from flask import Flask
import logging
import os

# Initialize the Flask application
# - The 'static_folder' parameter specifies the folder for static files (CSS, JS, images).
app = Flask(
    __name__,
    static_folder="static",  # Adjust if the static folder path has changed
)

# Set the secret key for session management and CSRF protection
# - It's crucial to keep the secret key secure and not hard-coded in production.
app.secret_key = "Needed for IPS Run function Submit"

# Configure Flask Logging
# - Flask uses the 'app.logger' for logging messages.
# - Setting the log level to INFO to capture informational messages and above.
app.logger.setLevel(logging.INFO)

# Ensure the log directory exists
log_directory = 'app/logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Create a file handler for logging
# - Logs will be written to 'logs/cp_demo_server.log'.
# - Using RotatingFileHandler can prevent log files from growing indefinitely.
handler = logging.FileHandler(os.path.join(log_directory, 'cp_demo_server.log'))
handler.setLevel(logging.INFO)  # Set the handler log level to INFO

# Define the log format
# - This format includes the timestamp, log level, and message.
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# Add the handler to the Flask app's logger
app.logger.addHandler(handler)

# Optionally, prevent Flask's default logger from propagating messages to the root logger
app.logger.propagate = False

# Import the views module to register routes
# - This should be done after configuring the app to ensure routes have access to the app context.
from . import views
