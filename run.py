# run.py

"""
Run Script for CP Demo Server

This script initializes the necessary databases, loads CSV data into them,
and starts the Flask application. It serves as the entry point for running
the CP Demo Server.

Usage:
    python run.py

Ensure that the required environment variables and configurations are set
before running the application.
"""

# Import necessary modules and functions

from app.db import init_db, load_csv_to_db, init_db_for_generated_files
import os
import sys


# Modify the system path to include the parent directory
# This allows importing the 'app' object from the 'cp_demo_server' package
# Note: Modifying sys.path is generally discouraged. Consider using
# a proper package structure or virtual environments.
sys.path.append(os.path.dirname(os.getcwd()))
from app import app  # Import the Flask application instance
from app import logging
# Set up basic logging configuration

# Log the start of the application
logging.info("Starting CP Demo Server...")

try:
    # Initialize the main database
    logging.info("Initializing the main database...")
    init_db()

    # Initialize the database for generated files
    logging.info("Initializing the database for generated files...")
    init_db_for_generated_files()

    # Load data from CSV files into the databases
    logging.info("Loading CSV data into the databases...")
    load_csv_to_db()

    logging.info("Database initialization and data loading completed successfully.")

except Exception as e:
    # Log any exceptions that occur during initialization
    logging.error(f"An error occurred during initialization: {e}", exc_info=True)
    sys.exit(1)  # Exit the script with a non-zero status to indicate failure

if __name__ == '__main__':
    """
    Entry point for running the Flask application.
    
    To enable HTTPS (SSL), uncomment the ssl_context parameter and ensure that
    the certificate and key files are correctly specified.
    
    Example:
        app.run(host='0.0.0.0', port=8080, debug=True, ssl_context=('certificate/cert.pem', 'certificate/key.pem'))
    """
    try:
        logging.info("Starting the Flask application...")
        # Start the Flask development server
        app.run(
            host='0.0.0.0',      # Listen on all available network interfaces
            port=8080,           # Port number to listen on
            debug=True,          # Enable debug mode (disable in production)
            # ssl_context=('certificate/cert.pem', 'certificate/key.pem')  # Uncomment for HTTPS
        )
    except Exception as e:
        # Log any exceptions that occur while running the server
        logging.error(f"An error occurred while running the server: {e}", exc_info=True)
        sys.exit(1)  # Exit the script with a non-zero status to indicate failure
