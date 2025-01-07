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
from app import logging
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

# Global lock for thread-safe access to shared resources
flags_lock = threading.Lock()

# Global dictionaries to track attack progress and stop events
attack_progress = {}
attack_stop_events = {}

@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def index():
    """
    Render the home page.

    Routes:
        / or /index

    Methods:
        GET

    Returns:
        Rendered index.html template.
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
        int or None: HTTP status code if the request is successful; otherwise, None.
    """
    headers = {"User-Agent": user_agent or 'Microsoft IE 8.0'}
    logging.debug(f"Sending {method} request to {url} with headers: {headers}")
    try:
        if method == "POST":
            response = requests.post(url, headers=headers)
            logging.info(f"POST response from {url}: {response.status_code}")
        elif method == "GET":
            response = requests.get(url, headers=headers)
            logging.info(f"GET response from {url}: {response.status_code}")
        else:
            raise ValueError("Unsupported HTTP method")
        return response.status_code

    except requests.exceptions.RequestException as e:
        # Handle specific connection errors
        if isinstance(e, requests.exceptions.ConnectionError):
            if "Connection reset by peer" in str(e):
                logging.warning(f"Connection reset by peer when accessing {url}. Possible block detected.")
                return "104 - Connection Reset by Peer (Blocked)"
        logging.error(f"Error sending {method} request to {url}: {e}")
        return None


def handle_post_request(protection_name, target_ip):
    """
    Handle the logic for triggering a protection against a target IP.

    Args:
        protection_name (str): The name of the protection to trigger.
        target_ip (str): The target IP address for the protection.

    Returns:
        None
    """
    protection = get_protection_by_name(protection_name)
    
    if protection:
        # Replace the placeholder in the Resource field with the target IP
        resource = protection['Resource'].replace("{{IP}}", target_ip)

        # Trigger the protection using the updated Resource field
        status_code = send_request(
            protection['Method'],
            resource,
            protection.get('Agent')
        )
        if status_code == 200:
            flash(f"Triggered '{protection_name}' successfully (Status Code 200)", 'success')
        elif isinstance(status_code, int):
            flash(f"Triggered '{protection_name}' with Status Code: {status_code}", 'info')
        elif isinstance(status_code, str):
            flash(f"Triggered '{protection_name}'. {status_code}", 'warning')
        else:
            flash(f"Triggered '{protection_name}' but received unexpected response.", 'warning')
    else:
        flash("Protection not found.", 'warning')


@app.route('/ips', methods=['GET', 'POST'])
def ips():
    """
    Handle IPS (Intrusion Prevention System) protections.

    Route:
        /ips

    Methods:
        GET, POST

    GET:
        - Renders the IPS protections page with available protections and the saved target IP.

    POST:
        - Processes form submissions to trigger a specific protection against a target IP.
        - Saves the target IP in the session for persistence across requests.

    Returns:
        Rendered ips.html template with protection data and saved target IP.
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
        

    # Retrieve the saved IP from the session, defaulting to an empty string
    saved_ip = session.get('target_ip', '')
    # Load IPS protections data from the database
    data = load_protections()
    return render_template('ips.html', data=data, saved_ip=saved_ip)


@app.route('/clear_target_ip', methods=['POST'])
def clear_target_ip():
    """
    Clear the saved target IP address from the session.

    Returns:
        Redirect to the IPS page with the target IP cleared.
    """
    session.pop('target_ip', None)  # Remove the target IP from the session
    flash("Target IP cleared successfully.", "danger")
    return redirect(url_for('ips'))


@app.route('/attack_generators', methods=['GET', 'POST'])
def attack_generators():
    """
    Handle Attack Generators functionality.

    Route:
        /attack_generators

    Methods:
        GET, POST

    GET:
        - Renders the attack generators page without any attack results.

    POST:
        - Processes form submissions to initiate a specific attack.
        - Gathers attack parameters from the form and executes the attack.
        - Renders the attack generators page with the result of the attack.

    Returns:
        Rendered attack_generators.html template with attack results or without.
    """
    if request.method == 'POST':
        # Retrieve form data
        attack_type = request.form.get('attack_type')
        target_ip = request.form.get('target_ip')
        port = int(request.form.get('port', 0)) if request.form.get('port') else None
        gateway_ip = request.form.get('gateway_ip')
        spoofed_domain = request.form.get('spoofed_domain')
        spoofed_ip = request.form.get('spoofed_ip')
        custom_payload = request.form.get('custom_payload')
        attack_id = f"{target_ip}-{attack_type}"

        # Execute the attack with the provided parameters
        result = execute_attack(
            attack_id, attack_type, target_ip, port,
            gateway_ip=gateway_ip, spoofed_domain=spoofed_domain,
            spoofed_ip=spoofed_ip, custom_payload=custom_payload
        )
        return render_template('attack_generators.html', result=result, attack_type=attack_type)

    # For GET requests, render the attack generators page without any results
    return render_template('attack_generators.html', result=None)


@app.route('/start_attack', methods=['POST'])
def start_attack():
    """
    Start an attack based on JSON payload.

    Route:
        /start_attack

    Methods:
        POST

    Payload:
        JSON containing attack parameters:
            - attack_type (str)
            - target_ip (str)
            - port (int, optional)
            - custom_payload (str, optional)
            - gateway_ip (str, optional)
            - spoofed_domain (str, optional)
            - spoofed_ip (str, optional)

    Functionality:
        - Extracts attack parameters from the JSON payload.
        - Generates a unique attack_id.
        - Initiates the attack in a separate thread for concurrency.
        - Returns a JSON response with the attack_id.

    Returns:
        JSON response containing the attack_id and HTTP status 200.
    """
    data = request.json
    attack_type = data.get('attack_type')
    target_ip = data.get('target_ip')
    port = int(data.get('port', 0)) if data.get('port') else None
    custom_payload = data.get('custom_payload')
    gateway_ip = data.get('gateway_ip')
    spoofed_domain = data.get('spoofed_domain')
    spoofed_ip = data.get('spoofed_ip')
    attack_id = f"{target_ip}-{attack_type}"

    # Start the attack in a new thread to allow concurrent executions
    attack_thread = threading.Thread(
        target=execute_attack,
        args=(attack_id, attack_type, target_ip, port),
        kwargs={
            "custom_payload": custom_payload,
            "gateway_ip": gateway_ip,
            "spoofed_domain": spoofed_domain,
            "spoofed_ip": spoofed_ip
        }
    )
    attack_thread.start()

    # Optionally, store thread references or manage them as needed
    return jsonify({"attack_id": attack_id}), 200


@app.route('/stop_attack/<attack_id>', methods=['POST'])
def stop_attack(attack_id):
    """
    Stop an ongoing attack based on the attack_id.

    Route:
        /stop_attack/<attack_id>

    Methods:
        POST

    Args:
        attack_id (str): The unique identifier of the attack to stop.

    Functionality:
        - Checks if the attack_id exists in the attack_stop_events dictionary.
        - If found, signals the attack thread to stop using threading.Event.
        - Logs the attack termination.
        - Returns a JSON response indicating the result.

    Returns:
        JSON response with a success message and HTTP status 200 if stopped.
        JSON response with an error message and HTTP status 404 if attack not found.
    """
    with flags_lock:
        if attack_id in attack_stop_events:
            attack_stop_events[attack_id].set()  # Signal the thread to stop
            logging.info(f"Attack {attack_id} stopping initiated.")
            return jsonify({"message": f"Attack {attack_id} stopped."}), 200
        else:
            return jsonify({"message": f"Attack {attack_id} not found."}), 404


@app.route('/progress/<attack_id>', methods=['GET'])
def progress(attack_id):
    """
    Retrieve the progress of an ongoing attack.

    Route:
        /progress/<attack_id>

    Methods:
        GET

    Args:
        attack_id (str): The unique identifier of the attack.

    Functionality:
        - Fetches the current progress status of the attack from the attack_progress dictionary.
        - Returns the progress as a JSON response.

    Returns:
        JSON response containing the progress message and HTTP status 200.
    """
    progress = attack_progress.get(attack_id, "No progress available")
    return jsonify({"progress": progress}), 200


@app.route('/details/<attack_id>', methods=['GET'])
def attack_details(attack_id):
    """
    Retrieve detailed information about an attack.

    Route:
        /details/<attack_id>

    Methods:
        GET

    Args:
        attack_id (str): The unique identifier of the attack.

    Functionality:
        - Fetches detailed information about the attack from the attack_progress dictionary.
        - Returns the details as a JSON response.

    Returns:
        JSON response containing the attack details and HTTP status 200.
    """
    details = f"Details for attack {attack_id}:\n" \
              f"Progress: {attack_progress.get(attack_id, 'No progress available')}."
    return jsonify({"details": details})


@app.route('/av', defaults={'req_path': ''})
@app.route('/av/<path:req_path>')
def dir_listing(req_path):
    """
    List files and directories for the Antivirus (AV) section.

    Routes:
        /av or /av/<req_path>

    Methods:
        GET

    Args:
        req_path (str): The requested subpath within the AV directory.

    Functionality:
        - Resolves the requested path relative to the malware_samples directory.
        - If the path is a file, sends it as a downloadable attachment.
        - If the path is a directory, lists all files and subdirectories.
        - Generates breadcrumbs for navigation.

    Returns:
        - Rendered av.html template with files and breadcrumbs.
        - Sends the file directly if the path is a file.
        - Returns a 404 error if the path does not exist.
    """
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'malware_samples')
    abs_path = os.path.abspath(os.path.join(BASE_DIR, req_path))

    # Ensure the resolved path is within the BASE_DIR to prevent directory traversal
    if not abs_path.startswith(BASE_DIR):
        logging.warning(f"Directory traversal attempt blocked: {abs_path}")
        return abort(403)

    logging.info(f"Resolved absolute path: {abs_path}")

    if not os.path.exists(abs_path):
        logging.warning(f"Path not found: {abs_path}")
        return abort(404)

    # If the path is a file, send it as a downloadable attachment
    if os.path.isfile(abs_path):
        logging.info(f"Sending file: {abs_path}")
        return send_file(abs_path, as_attachment=True)

    # Generate breadcrumbs for navigation
    folders = req_path.split('/') if req_path else []
    breadcrumbs = []
    current_path = '/av'
    for folder in folders:
        current_path = os.path.join(current_path, folder)
        breadcrumbs.append({'name': folder, 'url': current_path})

    # List files and directories in the current directory
    files_with_paths = []
    try:
        for file in os.listdir(abs_path):
            file_path = os.path.join(abs_path, file)
            files_with_paths.append({
                'name': file,
                'path': os.path.join(req_path, file) if req_path else file,
                'is_file': os.path.isfile(file_path)
            })
        logging.debug(f"Files and directories: {files_with_paths}")
    except Exception as e:
        logging.error(f"Error accessing directory {abs_path}: {e}")
        return abort(500)

    return render_template('av.html', files=files_with_paths, breadcrumbs=breadcrumbs)


@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """
    Delete a specific generated file.

    Route:
        /delete/<filename>

    Methods:
        POST

    Args:
        filename (str): The name of the file to delete.

    Functionality:
        - Attempts to delete the specified file using the file_generator module.
        - Flashes a success message upon successful deletion.
        - Logs any errors encountered during deletion.
        - Redirects to the 'te' (Threat Emulation) page.

    Returns:
        Redirect to the 'te' route after deletion attempt.
    """
    try:
        delete_generated_file(filename)
        flash(f"Deleted the file '{filename}'.", 'danger')
        logging.info(f"Deleted file: {filename}")
    except Exception as e:
        logging.error(f"Error deleting file '{filename}': {e}")
        flash(f"Error deleting the file '{filename}'.", 'warning')
    return redirect(url_for('te'))


@app.route('/delete_all', methods=['POST'])
def delete_all_files():
    """
    Delete all generated files.

    Route:
        /delete_all

    Methods:
        POST

    Functionality:
        - Attempts to delete all generated files using the file_generator module.
        - Flashes a success message upon successful deletion.
        - Logs any errors encountered during deletion.
        - Redirects to the 'te' (Threat Emulation) page.

    Returns:
        Redirect to the 'te' route after deletion attempt.
    """
    try:
        delete_all_generated_files()
        flash("Deleted all generated files.", 'danger')
        logging.info("Deleted all generated files.")
    except Exception as e:
        logging.error(f"Error deleting all files: {e}")
        flash("Error deleting all generated files.", 'warning')
    return redirect(url_for('te'))


@app.route('/te')
def te():
    """
    Render the Threat Emulation (TE) page.

    Route:
        /te

    Methods:
        GET

    Functionality:
        - Loads all generated files and the supported file types.
        - Renders the te.html template with the loaded files and file types.

    Returns:
        Rendered te.html template with generated files and supported file types.
    """
    file_types = ['pdf', 'docx', 'pptx', 'xlsx', 'exe', 'dylib', 'elf', 'rtf', 'jpg', 'png', 'bmp', 'gif', 'tiff']
    generated_files = load_generated_files()
    # Load existing email configuration
    email_config = load_email_config() or {}

    # Render the template with the required context
    return render_template(
        'te.html',
        files=generated_files,
        file_types=file_types,
        email_config=email_config
    )



@app.route('/generate', methods=['POST'])
def generate():
    """
    Generate files based on user-selected parameters.

    Route:
        /generate

    Methods:
        POST

    Functionality:
        - Retrieves selected file types and other generation parameters from the form.
        - Validates that at least one file type is selected.
        - Iterates over each selected file type and generates the corresponding file using the file_generator module.
        - Logs any errors encountered during file generation.
        - Flashes a success message upon successful generation.
        - Redirects to the 'te' (Threat Emulation) page.

    Returns:
        Redirect to the 'te' route after file generation.
    """
    # Retrieve selected file types from the form
    file_types = request.form.getlist('file_types')
    if not file_types:
        flash("Please select at least one file type.", 'warning')
        return redirect(url_for('te'))

    # Retrieve additional generation parameters
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

    # Iterate over each selected file type and generate the file
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
                logging.info(f"File of type '{file_type}' generated successfully.")
            else:
                logging.warning(f"File of type '{file_type}' failed to generate.")
                flash(f"Error generating file of type '{file_type}'.", 'warning')
        except Exception as e:
            logging.error(f"Error generating file of type '{file_type}': {e}", exc_info=True)
            flash(f"Error generating file of type '{file_type}'.", 'warning')

    flash("File(s) generated successfully!", 'success')
    return redirect(url_for('te'))


@app.route('/download/<filename>')
def download_file(filename):
    """
    Serve a file for download from the generated files directory.
    """
    # Define the directory for file storage
    FILE_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'generated_files')

    # Resolve the absolute path for the requested file
    file_path = os.path.abspath(os.path.join(FILE_STORAGE, filename))

    # Prevent directory traversal by ensuring the file is within the FILE_STORAGE directory
    if not file_path.startswith(FILE_STORAGE):
        logging.warning(f"Directory traversal attempt blocked: {file_path}")
        return abort(403)

    # Check if the file exists
    if not os.path.exists(file_path):
        logging.warning(f"Requested file does not exist: {file_path}")
        return abort(404)

    # Determine the MIME type of the file
    mime_type, _ = mimetypes.guess_type(file_path)

    # Override MIME type for specific file extensions
    if filename.lower().endswith('.exe'):
        mime_type = 'application/x-msdownload'

    logging.info(f"Serving file for download: {file_path} with MIME type: {mime_type}")
    return send_file(file_path, as_attachment=True, mimetype=mime_type)

@app.route('/download_ioc')
def download_ioc():
    """
    Serve the IOC (Indicators of Compromise) demo CSV file for download.

    Route:
        /download_ioc

    Methods:
        GET

    Functionality:
        - Sends the 'ioc_demo.csv' file as an attachment for download.

    Returns:
        The 'ioc_demo.csv' file as a downloadable attachment.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ioc_files', 'ioc_demo.csv')
    if not os.path.exists(path):
        logging.warning(f"IOC demo file does not exist: {path}")
        return abort(404)
    return send_file(path, as_attachment=True)


@app.route('/download_ioc_pdf')
def download_ioc_pdf():
    """
    Serve the IOC PDF datasheet for download.

    Route:
        /download_ioc_pdf

    Methods:
        GET

    Functionality:
        - Sends the 'endpoint_security_datasheet.pdf' file as an attachment for download.

    Returns:
        The 'endpoint_security_datasheet.pdf' file as a downloadable attachment.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ioc_files', 'endpoint_security_datasheet.pdf')
    if not os.path.exists(path):
        logging.warning(f"IOC PDF datasheet does not exist: {path}")
        return abort(404)
    return send_file(path, as_attachment=True)


@app.route("/https_inspection", methods=["GET"])
def https_inspection():
    """
    Render the HTTPS inspection page.

    Route:
        /https_inspection

    Methods:
        GET

    Returns:
        Rendered https_inspection.html template.
    """
    return render_template('https_inspection.html')


@app.route('/download_cert')
def download_cert():
    """
    Serve the CP Demo Server certificate for download.

    Route:
        /download_cert

    Methods:
        GET

    Functionality:
        - Sends the 'cp_demo_server.p12' certificate file as an attachment for download.

    Returns:
        The 'cp_demo_server.p12' file as a downloadable attachment.
    """
    path = "data/certificate/cp_demo_server.p12"
    if not os.path.exists(path):
        logging.warning(f"Certificate file does not exist: {path}")
        return abort(404)
    return send_file(path, as_attachment=True)


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

# Flask-Mail configuration
app.config['MAIL_SERVER'] = email_config['smtp_server']
app.config['MAIL_PORT'] = email_config['port']
#app.config['MAIL_USERNAME'] = email_config['sender_email']
#app.config['MAIL_PASSWORD'] = email_config['sender_password']
app.config['MAIL_USE_TLS'] = email_config['encryption_type'].upper() == "STARTTLS"
app.config['MAIL_USE_SSL'] = False  # We're not using SSL
app.config['MAIL_DEFAULT_SENDER'] = email_config['sender_email']

mail = Mail(app)


@app.route('/send_email/<filename>', methods=['POST'])
def send_email_route(filename):
    """Route to send an email with a specified file as an attachment."""
    FILE_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'generated_files')
    file_path = os.path.join(FILE_STORAGE, filename)

    if not os.path.exists(file_path):
        flash("File not found.", "warning")
        logging.info("File NOT Found to Attach")
        return redirect(url_for('te'))  # Redirect to 'te' page

    # Load email configuration
    email_config = load_email_config()
    if not email_config:
        flash("Email configuration not found.", "warning")
        logging.info("Email configuration not found")
        return redirect(url_for('te'))

    recipient_email = email_config.get('default_recipient')
    if not recipient_email:
        flash("No default recipient configured.", "danger")
        logging.info("No default recipient configured")
        return redirect(url_for('te'))

    subject = email_config.get('email_subject', f"File: {filename}")
    body = email_config.get('email_body', f"Please find the attached file: {filename}")

    # Determine the MIME type of the file
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'  # Fallback if detection fails

    main_type, sub_type = mime_type.split('/')

    try:
        msg = Message(subject, recipients=[recipient_email])
        msg.body = body

        # Attach the file with correct MIME type
        with app.open_resource(file_path) as fp:
            msg.attach(filename, f"{main_type}/{sub_type}", fp.read())

        mail.send(msg)
        logging.info(f"Email sent successfully to {recipient_email}.")
        flash(f"Email sent successfully to {recipient_email}.", "success")
        return redirect(url_for('te')) 

    except Exception as e:
        logging.error(f"Error sending email: {e}")
        flash(f"Error sending email: {str(e)}", "danger")
        return redirect(url_for('te'))  

@app.route('/email_config', methods=['GET', 'POST'])
def email_config():
    if request.method == 'POST':
        config_data = request.form.to_dict()
        save_email_config(config_data)  # Save the config using your existing function
        flash("Email configuration saved successfully!", "success")
        return redirect(url_for('te'))  # Redirect to the main page or wherever needed

    # Load existing configuration to pre-fill the modal
    email_config = load_email_config() or {}
    return render_template('te.html', email_config=email_config)
