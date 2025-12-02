# CP Demo Server - Threat Prevention Showcase

![Flask](https://img.shields.io/badge/Flask-3.1.0-blue.svg)
![SQLite](https://img.shields.io/badge/SQLite-3.36.0-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

The **CP Demo Server** is a Flask-based web application designed to showcase advanced IPS (Intrusion Prevention System) protections, file generation, and attack simulation capabilities. This server allows users to interact with a feature-rich web interface for generating files, testing intrusion protection mechanisms, and simulating network attacks.


![](https://github.com/alshawwaf/cp_demo_server/blob/GA/app/data/readme_assets/cp_demo_server_demo.gif)

---

## Features

### IPS Protections
- **Dynamic Target Selection:** Customize the target IP for IPS testing scenarios.  
- **Comprehensive Protections:** Simulate and validate industry-standard IPS measures.  
- **Configurable Parameters:** Set confidence levels, severity, and performance impact metrics.

### Malware Files
- **Malware Samples:** Download from a list of malware families, including viruses, ransomware, etc.

### File Generation
- **Diverse File Formats:** Generate files in formats like PDF, DOCX, PPTX, JPG, and more.  
- **Feature Inclusion:** Embed scripts, URLs, multimedia, or malicious payloads.  
- **Payload Simulation:** Include benign or simulated malicious payloads for testing.

---

## Technologies Used

- **Backend:**
  - [Flask](https://flask.palletsprojects.com/) – A lightweight WSGI web application framework.
  - [SQLite](https://www.sqlite.org/index.html) – A C library that provides a lightweight disk-based database.

- **Frontend:**
  - [Bootstrap](https://getbootstrap.com/) – A CSS framework for building responsive and mobile-first websites.
  - [Bootstrap Icons](https://icons.getbootstrap.com/) – A growing library of open source icons.

- **Programming Languages:**
  - [Python](https://www.python.org/) – A high-level, interpreted programming language.

- **Others:**
  - [Gunicorn](https://gunicorn.org/) – A Python WSGI HTTP server for UNIX.
  - [PyInstaller](https://www.pyinstaller.org/) – Converts Python applications into stand-alone executables.

---

## Explanation of Key Directories

- **`app/`**: Main application directory containing routes, database logic, and file generation.
  - **`data/`**: Contains databases, log files, and CSV data used by `db.py`.  
  - **`data/malware_samples/`**: Directory where the malware sample files are stored.  
  - **`data/generated_files/`**: Directory where generated/downloadable files are stored.  
  - **`data/ioc_files/`**: Contains CSV and PDF test files for the IoC demo.  
  - **`data/certificate/`**: Directory containing TLS/SSL certificates (e.g., `cp_demo_server.p12`).  
  - **`data/email_config/`**: Stores JSON configuration files for email settings.  
  - **`templates/`**: Holds HTML templates for rendering web pages.  
  - **`static/`**: Stores static assets like CSS, JavaScript, and site images.
- **`tests/`**: Remote testing scripts for firewall and security appliance validation.
  - **`trigger_attacks.py`**: IPS attack trigger script for testing firewall blocking.
  - **`test_malware_downloads.py`**: Malware download tester (streams & flushes safely).
  - See [`tests/README.md`](tests/README.md) for detailed usage instructions.

---

## Testing Scripts

The project includes remote testing scripts for validating firewall and security appliance functionality. These scripts are located in the `tests/` directory.

### Quick Start

```bash
# Test IPS protections
cd tests
python trigger_attacks.py --server http://SERVER_IP:5000 --target TARGET_IP --file protections_example.txt

# Test malware download blocking
python test_malware_downloads.py --server http://SERVER_IP:5000 --file malware_files_example.txt
```

For detailed documentation, see [`tests/README.md`](tests/README.md).


---

## Installation

### Prerequisites

Ensure the following are installed on your system:

1. **Python 3.8+**  
2. **Pip** (Python package manager)  
3. **Virtualenv** (to create isolated Python environments)  
4. **System Dependencies** (see below)

### Setup Instructions

**Clone the Repository:**
```bash
git clone https://github.com/alshawwaf/cp_demo_server.git
```

**Install System-Level Dependencies (Linux Example):**

```bash
sudo apt update
sudo apt install -y python3-virtualenv libpcap-dev libffi-dev build-essential gcc ghostscript imagemagick libcurl4-openssl-dev mingw-w64
```

**Set Up a Virtual Environment:**

```bash
virtualenv venv
source venv/bin/activate
```

**Install Python Dependencies:**

```bash
pip install -r requirements.txt
```

### Deploy with Docker

```bash
docker build -t cp_demo_server_image:latest .
docker run -d --name cp_demo_server_container -p 8080:8080 cp_demo_server_image:latest
```

**Optional: Generate new SSL Certificates:**

```bash
touch certificate/openssl.cnf
cat >> certificate/openssl.cnf <<EOF
[ req ]
prompt = no
distinguished_name = americas-ses.com

[ americas-ses.com ]
countryName=            CA
stateOrProvinceName=    ON
localityName=           Ottawa
organizationName=       server.Americas-ses
organizationalUnitName= Demo TLS Web Server
commonName=             server-22.americas-ses.ca
emailAddress = siteadmin@domain.com
EOF
```

Generate self-signed certificates if needed:

```bash
sudo apt install openssl -y
openssl req -x509 --config certificate/openssl.cnf -newkey rsa:4096 -nodes -out certificate/cert.pem -keyout certificate/key.pem -days 365

openssl pkcs12 -export -out certificate/cp_demo_server.p12 -inkey certificate/key.pem -in certificate/cert.pem -passout pass:vpn123!
```

**Run the Application:**

```bash
python run.py
```

### Access the Application

Open your browser and navigate to http://127.0.0.1:8080.

### Run as a Service (Optional)

To run the application as a service using systemd, follow these steps:

**Create the Service File:**

```bash
sudo nano /etc/systemd/system/cp_demo_server.service
```

**Add the Following Content:**

```ini
[Unit]
Description=CP Demo Server
After=network.target

[Service]
User=kali
WorkingDirectory=/home/kali/Desktop/cp_demo_server/
ExecStart=/home/kali/Desktop/cp_demo_server/venv/bin/python3 /home/kali/Desktop/cp_demo_server/run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cp_demo_server.service
sudo systemctl start cp_demo_server.service
```

## API Documentation

You can reach the API documentation under the apidocs path. flasgger library is sued to generate the docs
```
http://localhost:8080/apidocs/
```

✨ Thank you for using CP Demo Server! ✨

---
