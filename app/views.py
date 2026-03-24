# routes.py

"""
CP Demo Server Routes

This module defines all the routes (endpoints) for the CP Demo Server application.
It handles rendering templates, processing form submissions, managing attacks,
and facilitating file operations.

Modules:
- Flask: Web framework for handling HTTP requests and responses.
- db: Database module for loading and retrieving protection data.
- attack_generator: Module for executing attacks.
- file_generator: Module for generating various file types.
- requests: Library for sending HTTP requests.
- threading: Enables running attacks in separate threads for concurrency.
- mimetypes: Determines the MIME type of files for proper handling.
"""

from . import app
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Single admin account for demo server
_ADMIN_USER = 'admin'
_ADMIN_HASH = generate_password_hash('Cpwins!1@2026!')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


from flask_mail import Mail, Message
from app.attack_generator import execute_attack
from app.db import load_protections, get_protection_by_name
from app.file_generator import (
    generate_file,
    delete_generated_file,
    delete_all_generated_files,
    load_generated_files
)
from flask import (
    render_template,
    jsonify,
    send_file,
    request,
    flash,
    redirect,
    url_for,
    abort,
    session
)
import requests
import os, json
import threading
import mimetypes
import io
from app import crypto_util

# If you're using Flasgger
from flasgger import Swagger
swagger = Swagger(app)

# Global lock for thread-safe access to shared resources
flags_lock = threading.Lock()

# Global dictionaries to track attack progress and stop events
attack_progress = {}
attack_stop_events = {}

@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
@login_required
def index():
    """
    Render the home page.
    ---
    get:
      summary: Home Page
      description: Renders the home page of the application.
      responses:
        200:
          description: A rendered HTML home page.
    """
    return render_template('index.html')


def send_request(method, url, user_agent):
    """
    Send an HTTP request with the specified method, URL, and User-Agent.

    Args:
        method (str): HTTP method ('GET' or 'POST').
        url (str): The target URL for the request.
        user_agent (str): The User-Agent header value.

    Returns:
        int or None or str: HTTP status code if successful, None if error,
        or a string if blocked/connection reset by peer.
    """
    headers = {"User-Agent": user_agent or 'Microsoft IE 8.0'}
    app.logger.debug(f"Sending {method} request to {url} with headers: {headers}")
    try:
        if method == "POST":
            response = requests.post(url, headers=headers)
            app.logger.info(f"POST response from {url}: {response.status_code}")
        elif method == "GET":
            response = requests.get(url, headers=headers)
            app.logger.info(f"GET response from {url}: {response.status_code}")
        else:
            raise ValueError("Unsupported HTTP method")

        return response.status_code

    except requests.exceptions.RequestException as e:
        # Handle specific connection errors
        if isinstance(e, requests.exceptions.ConnectionError):
            if "Connection reset by peer" in str(e):
                app.logger.warning(f"Connection reset by peer when accessing {url}. Possible block detected.")
                return "104 - Connection Reset by Peer (Blocked)"
        app.logger.error(f"Error sending {method} request to {url}: {e}")
        return None


def trigger_protection(protection_name, target_ip):
    """
    Core logic to trigger a protection.
    Returns a dictionary with success status, message, and status code.
    """
    protection = get_protection_by_name(protection_name)

    if not protection:
        return {
            "success": False,
            "message": f"Protection '{protection_name}' not found.",
            "status_code": 404
        }

    # Replace the placeholder in the Resource field with the target IP
    resource = protection['Resource'].replace("{{IP}}", target_ip)

    # Trigger the protection using the updated Resource field
    status_code = send_request(
        protection['Method'],
        resource,
        protection.get('Agent')
    )

    if status_code == 200:
        return {
            "success": True,
            "message": f"Triggered '{protection_name}' successfully.",
            "status_code": 200
        }
    elif isinstance(status_code, int):
        return {
            "success": True, # Technically executed, just non-200 response
            "message": f"Triggered '{protection_name}' with Status Code: {status_code}",
            "status_code": status_code
        }
    elif isinstance(status_code, str):
        return {
            "success": False,
            "message": f"Triggered '{protection_name}'. {status_code}",
            "status_code": 500 # Internal/Network error representation
        }
    else:
        return {
            "success": False,
            "message": f"Triggered '{protection_name}' but received unexpected response.",
            "status_code": 500
        }


def handle_post_request(protection_name, target_ip):
    """
    Handle the logic for triggering a protection against a target IP (Legacy/Form support).
    Uses trigger_protection and flashes messages.
    """
    result = trigger_protection(protection_name, target_ip)
    
    category = 'success' if result['success'] and result['status_code'] == 200 else \
               'info' if result['success'] else \
               'warning'
               
    flash(result['message'], category)


@app.route('/api/run_attack', methods=['POST'])
@login_required
def api_run_attack():
    """
    API Endpoint to run a single attack.
    Expects JSON: { "protection_name": "...", "target_ip": "..." }
    """
    data = request.get_json()
    protection_name = data.get('protection_name')
    target_ip = data.get('target_ip')

    if not protection_name or not target_ip:
        return jsonify({
            "success": False,
            "message": "Missing protection_name or target_ip",
            "status_code": 400
        }), 400

    result = trigger_protection(protection_name, target_ip)
    return jsonify(result)


@app.route('/ips', methods=['GET', 'POST'])
@login_required
def ips():
    """
    Handle IPS (Intrusion Prevention System) protections.
    ---
    get:
      summary: Retrieve IPS Protections
      description: Retrieves available protections and the saved target IP (if any).
      responses:
        200:
          description: Renders the IPS protections page with available protections and the saved target IP.
    post:
      summary: Trigger a specific protection
      description: Processes form submissions to trigger a protection against a target IP. Saves target IP in session.
      parameters:
        - name: target_ip
          in: formData
          type: string
          required: true
          description: Target IP address to protect against
        - name: protection_name
          in: formData
          type: string
          required: true
          description: Name of the protection to trigger
      responses:
        302:
          description: Redirects to the same page after triggering protection.
    """
    if request.method == 'POST':
        target_ip = request.form.get('target_ip')
        if not target_ip:
            flash("Target IP address is required.", 'warning')
            return redirect(url_for('ips'))
        else:
            session['target_ip'] = target_ip

        protection_name = request.form.get('protection_name')

        if not protection_name:
            flash("Protection is unknown.", 'warning')
            return redirect(url_for('ips'))

        handle_post_request(protection_name, target_ip)

    # Retrieve the saved IP from session (default to empty string if not set)
    saved_ip = session.get('target_ip', '')
    data = load_protections()
    return render_template('ips.html', data=data, saved_ip=saved_ip)


@app.route('/clear_target_ip', methods=['POST'])
@login_required
def clear_target_ip():
    """
    Clear the saved target IP address from the session.
    ---
    post:
      summary: Clear Target IP
      description: Removes the target IP from the session for IPS testing.
      responses:
        302:
          description: Redirects to the IPS page after clearing.
    """
    session.pop('target_ip', None)
    flash("Target IP cleared successfully.", "danger")
    return redirect(url_for('ips'))


@app.route('/av', defaults={'req_path': ''})
@app.route('/av/<path:req_path>')
@login_required
def dir_listing(req_path):
    """
    List files and directories in the AV (Antivirus) section.
    ---
    get:
      summary: List AV Directory Contents
      description: Returns either a directory listing or a file download based on path.
      parameters:
        - name: req_path
          in: path
          type: string
          required: false
          description: Sub-path within the malware_samples directory
      responses:
        200:
          description: Renders the av.html template with file list or serves a file download
        403:
          description: Forbidden directory traversal attempt
        404:
          description: Path not found
    """
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'malware_samples')
    abs_path = os.path.abspath(os.path.join(BASE_DIR, req_path))

    # Ensure path is within BASE_DIR to prevent directory traversal
    if not abs_path.startswith(BASE_DIR):
        app.logger.warning(f"Directory traversal attempt blocked: {abs_path}")
        return abort(403)

    if not os.path.exists(abs_path) and not os.path.exists(abs_path + crypto_util.ENC_SUFFIX):
        app.logger.warning(f"Path not found: {abs_path}")
        return abort(404)

    # If the path is a file, serve it (decrypt on-the-fly if encrypted)
    if os.path.isfile(abs_path):
        app.logger.info(f"Sending file: {abs_path}")
        enc_path = crypto_util.find_enc(abs_path)
        if enc_path:
            buf = crypto_util.decrypt_to_bytes(enc_path)
            original_name = os.path.basename(abs_path)
            mime_type, _ = mimetypes.guess_type(original_name)
            return send_file(buf, as_attachment=True,
                             download_name=original_name,
                             mimetype=mime_type or 'application/octet-stream')
        return send_file(abs_path, as_attachment=True)

    # File doesn't exist as-is - check for an encrypted-only version
    enc_path = crypto_util.find_enc(abs_path)
    if enc_path and os.path.isfile(enc_path):
        app.logger.info(f"Decrypting and sending: {enc_path}")
        buf = crypto_util.decrypt_to_bytes(enc_path)
        original_name = os.path.basename(abs_path)
        mime_type, _ = mimetypes.guess_type(original_name)
        return send_file(buf, as_attachment=True,
                         download_name=original_name,
                         mimetype=mime_type or 'application/octet-stream')

    # If it's a directory, list contents
    folders = req_path.split('/') if req_path else []
    breadcrumbs = []
    current_path = '/av'
    for folder in folders:
        current_path = os.path.join(current_path, folder)
        breadcrumbs.append({'name': folder, 'url': current_path})

    files_with_paths = []
    try:
        for file in os.listdir(abs_path):
            if file.endswith(crypto_util.ENC_SUFFIX):
                continue  # handled below as the original name
            file_abs = os.path.join(abs_path, file)
            files_with_paths.append({
                'name': file,
                'path': os.path.join(req_path, file) if req_path else file,
                'is_file': os.path.isfile(file_abs),
                'encrypted': bool(crypto_util.find_enc(file_abs)),
            })
        # Surface files that exist only as .enc (original removed after encryption)
        for file in os.listdir(abs_path):
            if not file.endswith(crypto_util.ENC_SUFFIX):
                continue
            original_name = file[:-len(crypto_util.ENC_SUFFIX)]
            if not os.path.exists(os.path.join(abs_path, original_name)):
                files_with_paths.append({
                    'name': original_name,
                    'path': os.path.join(req_path, original_name) if req_path else original_name,
                    'is_file': True,
                    'encrypted': True,
                })
        app.logger.debug(f"Files and directories: {files_with_paths}")
    except Exception as e:
        app.logger.error(f"Error accessing directory {abs_path}: {e}")
        return abort(500)

    return render_template('av.html', files=files_with_paths, breadcrumbs=breadcrumbs)


@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """
    Delete a specific generated file.
    ---
    post:
      summary: Delete Generated File
      description: Deletes a specific file by filename from the generated files.
      parameters:
        - name: filename
          in: path
          type: string
          required: true
          description: The filename to delete
      responses:
        302:
          description: Redirects to the TE page after deletion attempt
    """
    try:
        delete_generated_file(filename)
        flash(f"Deleted the file '{filename}'.", 'danger')
        app.logger.info(f"Deleted file: {filename}")
    except Exception as e:
        app.logger.error(f"Error deleting file '{filename}': {e}")
        flash(f"Error deleting the file '{filename}'.", 'warning')
    return redirect(url_for('te'))


@app.route('/delete_all', methods=['POST'])
@login_required
def delete_all_files():
    """
    Delete all generated files.
    ---
    post:
      summary: Delete All Generated Files
      description: Attempts to delete all generated files in the system.
      responses:
        302:
          description: Redirects to the TE page after deletion attempt
    """
    try:
        delete_all_generated_files()
        flash("Deleted all generated files.", 'danger')
        app.logger.info("Deleted all generated files.")
    except Exception as e:
        app.logger.error(f"Error deleting all files: {e}")
        flash("Error deleting all generated files.", 'warning')
    return redirect(url_for('te'))


@app.route('/te')
@login_required
def te():
    """
    Render the Threat Emulation (TE) page.
    ---
    get:
      summary: Threat Emulation Page
      description: Displays a list of generated files and provides file generation options.
      responses:
        200:
          description: Renders the te.html template with available generated files
    """
    file_types = [
        'pdf', 'docx', 'pptx', 'xlsx', 'exe', 'exe-64bit',
        'dylib', 'elf', 'rtf', 'jpg', 'png', 'bmp',
        'gif', 'tiff'
    ]
    generated_files = load_generated_files()
    # Load existing email configuration
    email_config = load_email_config() or {}

    return render_template(
        'te.html',
        files=generated_files,
        file_types=file_types,
        email_config=email_config
    )


@app.route('/generate', methods=['POST'])
@login_required
def generate():
    """
    Generate files based on user-selected parameters.
    ---
    post:
      summary: Generate Threat Emulation Files
      description: Generate various file types based on selected parameters.
      parameters:
        - name: file_types
          in: formData
          type: array
          items:
            type: string
          required: true
          description: List of file types to generate
        - name: url_type
          in: formData
          type: string
          required: false
          description: Type of URL to embed
        - name: include_image
          in: formData
          type: string
          required: false
          description: Include image
        - name: include_script
          in: formData
          type: string
          required: false
          description: Include script
        - name: include_video
          in: formData
          type: string
          required: false
          description: Include video
        - name: include_audio
          in: formData
          type: string
          required: false
          description: Include audio
        - name: include_sensitive_link
          in: formData
          type: string
          required: false
          description: Include sensitive link
        - name: include_3d
          in: formData
          type: string
          required: false
          description: Include 3D content
        - name: include_pdf
          in: formData
          type: string
          required: false
          description: Include embedded PDF
        - name: include_external_app
          in: formData
          type: string
          required: false
          description: Include external application link
        - name: include_data_submission
          in: formData
          type: string
          required: false
          description: Include data submission form
      responses:
        302:
          description: Redirects back to the TE page after file generation
    """
    file_types = request.form.getlist('file_types')
    if not file_types:
        flash("Please select at least one file type.", 'warning')
        return redirect(url_for('te'))

    url_type = request.form.get('url_type')
    include_image = 'on' if request.form.get('include_image') else 'off'
    include_script = 'on' if request.form.get('include_script') else 'off'
    include_video = 'on' if request.form.get('include_video') else 'off'
    include_audio = 'on' if request.form.get('include_audio') else 'off'
    include_sensitive_link = 'on' if request.form.get('include_sensitive_link') else 'off'
    include_3d = 'on' if request.form.get('include_3d') else 'off'
    include_pdf = 'on' if request.form.get('include_pdf') else 'off'
    include_external_app = 'on' if request.form.get('include_external_app') else 'off'
    include_data_submission = 'on' if request.form.get('include_data_submission') else 'off'

    for file_type in file_types:
        try:
            success = generate_file(
                file_type,
                url_type,
                include_image,
                include_script,
                include_video,
                include_audio,
                include_sensitive_link,
                include_3d,
                include_pdf,
                include_external_app,
                include_data_submission
            )
            if success:
                app.logger.info(f"File of type '{file_type}' generated successfully.")
            else:
                app.logger.warning(f"File of type '{file_type}' failed to generate.")
                flash(f"Error generating file of type '{file_type}'.", 'warning')
        except Exception as e:
            app.logger.error(f"Error generating file of type '{file_type}': {e}", exc_info=True)
            flash(f"Error generating file of type '{file_type}'.", 'warning')

    flash("File(s) generated successfully!", 'success')
    return redirect(url_for('te'))


@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """
    Serve a file for download from the generated files directory.
    ---
    get:
      summary: Download Generated File
      description: Provides an endpoint to download a file by name from the generated files directory.
      parameters:
        - name: filename
          in: path
          type: string
          required: true
          description: Name of the file to download
      responses:
        200:
          description: The requested file is returned
        403:
          description: Forbidden directory traversal attempt
        404:
          description: File not found
    """
    FILE_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'generated_files')
    file_path = os.path.abspath(os.path.join(FILE_STORAGE, filename))

    if not file_path.startswith(FILE_STORAGE):
        app.logger.warning(f"Directory traversal attempt blocked: {file_path}")
        return abort(403)

    if not os.path.exists(file_path):
        app.logger.warning(f"Requested file does not exist: {file_path}")
        return abort(404)

    mime_type, _ = mimetypes.guess_type(file_path)

    # Override MIME type for .exe
    if filename.lower().endswith('.exe'):
        mime_type = 'application/x-msdownload'

    enc_path = crypto_util.find_enc(file_path)
    if enc_path:
        app.logger.info(f"Decrypting and serving: {enc_path}")
        buf = crypto_util.decrypt_to_bytes(enc_path)
        return send_file(buf, as_attachment=True, download_name=filename, mimetype=mime_type)

    app.logger.info(f"Serving file for download: {file_path} with MIME type: {mime_type}")
    return send_file(file_path, as_attachment=True, mimetype=mime_type)


@app.route('/download_ioc')
def download_ioc():
    """
    Serve the IOC (Indicators of Compromise) demo CSV file for download.
    ---
    get:
      summary: Download IOC CSV
      description: Serves the ioc_demo.csv file for download.
      responses:
        200:
          description: The CSV file is returned as an attachment
        404:
          description: File not found
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ioc_files', 'ioc_demo.csv')
    if not os.path.exists(path):
        app.logger.warning(f"IOC demo file does not exist: {path}")
        return abort(404)
    return send_file(path, as_attachment=True)


@app.route('/download_ioc_pdf')
def download_ioc_pdf():
    """
    Serve the IOC PDF datasheet for download.
    ---
    get:
      summary: Download IOC PDF Datasheet
      description: Serves the endpoint_security_datasheet.pdf file as an attachment.
      responses:
        200:
          description: PDF file downloaded
        404:
          description: File not found
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ioc_files', 'endpoint_security_datasheet.pdf')
    if not os.path.exists(path):
        app.logger.warning(f"IOC PDF datasheet does not exist: {path}")
        return abort(404)
    return send_file(path, as_attachment=True)


@app.route("/https_inspection", methods=["GET"])
def https_inspection():
    """
    Render the HTTPS inspection page.
    ---
    get:
      summary: HTTPS Inspection Page
      description: Renders an informational page about HTTPS inspection.
      responses:
        200:
          description: Renders the https_inspection.html template
    """
    return render_template('https_inspection.html')


@app.route('/download_cert')
def download_cert():
    """
    Serve the CP Demo Server certificate for download.
    ---
    get:
      summary: Download CP Demo Server Certificate
      description: Downloads the cp_demo_server.p12 certificate file.
      responses:
        200:
          description: Certificate file as attachment
        404:
          description: File not found
    """
    path = "data/certificate/cp_demo_server.p12"
    if not os.path.exists(path):
        app.logger.warning(f"Certificate file does not exist: {path}")
        return abort(404)
    return send_file(path, as_attachment=True)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == _ADMIN_USER and check_password_hash(_ADMIN_HASH, password):
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))
        error = 'Invalid credentials'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Load email configuration
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'email_config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'email_config.json')

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


email_config = load_email_config()
if not email_config:
    raise Exception("Email configuration not found. Please configure email settings.")


@app.route('/send_email/<filename>', methods=['POST'])
@login_required
def send_email_route(filename):
    """
    Send an email with a specified file as an attachment.
    ---
    post:
      summary: Send Email with Attachment
      description: Sends an email with a given file from generated files as an attachment, using the configured email settings.
      parameters:
        - name: filename
          in: path
          type: string
          required: true
          description: Name of the file to attach
      responses:
        302:
          description: Redirects to the 'te' page after sending or failing to send an email
    """
    FILE_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'generated_files')
    file_path = os.path.join(FILE_STORAGE, filename)

    if not os.path.exists(file_path):
        flash("File not found.", "warning")
        app.logger.info("File NOT Found to Attach")
        return redirect(url_for('te'))

    email_config = load_email_config()
    if not email_config:
        flash("Email configuration not found.", "warning")
        app.logger.info("Email configuration not found")
        return redirect(url_for('te'))

    recipient_email = email_config.get('default_recipient')
    if not recipient_email:
        flash("No default recipient configured.", "danger")
        app.logger.info("No default recipient configured")
        return redirect(url_for('te'))

    # Flask-Mail configuration
    app.config['MAIL_SERVER'] = email_config['smtp_server']
    app.config['MAIL_PORT'] = email_config['port']
    # app.config['MAIL_USERNAME'] = email_config['sender_email']
    # app.config['MAIL_PASSWORD'] = email_config['sender_password']
    app.config['MAIL_USE_TLS'] = email_config['encryption_type'].upper() == "STARTTLS"
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_DEFAULT_SENDER'] = email_config['sender_email']

    mail = Mail(app)

    subject = email_config.get('email_subject', f"File: {filename}")
    body = email_config.get('email_body', f"Please find the attached file: {filename}")

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'  # fallback if detection fails

    main_type, sub_type = mime_type.split('/')

    try:
        msg = Message(subject, recipients=[recipient_email])
        msg.body = body

        with app.open_resource(file_path) as fp:
            msg.attach(filename, f"{main_type}/{sub_type}", fp.read())

        mail.send(msg)
        app.logger.info(f"Email sent successfully to {recipient_email}.")
        flash(f"Email sent successfully to {recipient_email}.", "success")
        return redirect(url_for('te'))

    except Exception as e:
        app.logger.error(f"Error sending email: {e}")
        flash(f"Error sending email: {str(e)}", "danger")
        return redirect(url_for('te'))


@app.route('/email_config', methods=['GET', 'POST'])
@login_required
def email_config():
    """
    Configure or display the current email settings.
    ---
    get:
      summary: Display Email Configuration
      description: Displays the current email configuration in the te.html template.
      responses:
        200:
          description: Renders the te.html with the email configuration form.
    post:
      summary: Save Email Configuration
      description: Updates and saves the email configuration to a JSON file.
      parameters:
        - name: sender_email
          in: formData
          type: string
          required: false
          description: Email account used as sender
        - name: smtp_server
          in: formData
          type: string
          required: false
          description: SMTP server address
        - name: port
          in: formData
          type: string
          required: false
          description: SMTP port
        - name: encryption_type
          in: formData
          type: string
          required: false
          description: Encryption type (e.g., STARTTLS)
        - name: default_recipient
          in: formData
          type: string
          required: false
          description: Default recipient email address
        - name: email_subject
          in: formData
          type: string
          required: false
          description: Default subject for emails
        - name: email_body
          in: formData
          type: string
          required: false
          description: Default body for emails
      responses:
        302:
          description: Redirects back to te page upon successful save
    """
    if request.method == 'POST':
        config_data = request.form.to_dict()
        save_email_config(config_data)
        flash("Email configuration saved successfully!", "success")
        return redirect(url_for('te'))

    current_config = load_email_config() or {}
    return render_template('te.html', email_config=current_config)
