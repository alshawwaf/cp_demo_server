from flask import Flask
import logging
import os

app = Flask(
    __name__,
    static_folder="static",  
)

app.secret_key = "Needed for IPS Run function Submit"

# Configure Flask Logging
app.logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all log levels

# Ensure the log directory exists
log_directory = 'app/logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Create a file handler for logging
file_handler = logging.FileHandler(os.path.join(log_directory, 'cp_demo_server.log'))
file_handler.setLevel(logging.DEBUG)  # Set to DEBUG to capture all log levels

# Define the log format
log_format = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler.setFormatter(log_format)

# Add the file handler to the Flask app's logger
app.logger.addHandler(file_handler)
app.logger.propagate = True  # Ensure logs propagate to Flask's default log handlers


# Import the views module
from . import views

# Import the AI-Factory (AIFF) portal module — the guided cross-blade demo
from . import aiff  # noqa: E402,F401
