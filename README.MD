# CP Demo Server - Threat Prevention Showcase

![Flask](https://img.shields.io/badge/Flask-3.1.0-blue.svg)
![SQLite](https://img.shields.io/badge/SQLite-3.36.0-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup Instructions](#setup-instructions)
- [Usage](#usage)
  - [IPS Protections](#ips-protections)
  - [File Generation](#file-generation)
  - [Attack Simulation](#attack-simulation)
- [Docker Deployment](#docker-deployment)
  - [Dockerfile Content](#dockerfile-content)
  - [Build and Run](#build-and-run)


- [Requirements](#requirements)
  - [Python Libraries](#python-libraries)
  - [System-Level Dependencies](#system-level-dependencies)
  - [Docker-Specific Requirements](#docker-specific-requirements)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Logging](#logging)
- [Logging](#logging-1)
  - [Key Features](#key-features)
  - [Viewing Logs](#viewing-logs)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

The **CP Demo Server** is a Flask-based web application designed to showcase advanced IPS (Intrusion Prevention System) protections, file generation, and attack simulation capabilities. This server allows users to interact with a feature-rich web interface for generating files, testing intrusion protection mechanisms, and simulating network attacks.

---

## Features

### IPS Protections

- **Dynamic Target Selection:** Customize the target IP for IPS testing scenarios.
- **Comprehensive Protections:** Simulate and validate industry-standard IPS measures.
- **Configurable Parameters:** Set confidence levels, severity, and performance impact metrics.

### File Generation

- **Diverse File Formats:** Generate files in formats like PDF, DOCX, PPTX, JPG, and more.
- **Feature Inclusion:** Embed scripts, URLs, multimedia, or malicious payloads.
- **Payload Simulation:** Include benign or simulated malicious payloads for testing.

### Attack Simulation

- **Protocol-Specific Attacks:** Launch ICMP Flood, SYN Flood, DNS Attacks, and more.
- **Custom Payloads:** Create and execute user-defined attack payloads.
- **Real-Time Status:** Track attack progress and monitor simulation details.

---

## Technologies Used

- **Backend:**
  - [Flask](https://flask.palletsprojects.com/) - A lightweight WSGI web application framework.
  - [SQLite](https://www.sqlite.org/index.html) - A C library that provides a lightweight disk-based database.
  
- **Frontend:**
  - [Bootstrap](https://getbootstrap.com/) - A CSS framework for building responsive and mobile-first websites.
  - [Bootstrap Icons](https://icons.getbootstrap.com/) - A growing library of open source icons.
  
- **Programming Languages:**
  - [Python](https://www.python.org/) - A high-level, interpreted programming language.
  
- **Others:**
  - [Gunicorn](https://gunicorn.org/) - A Python WSGI HTTP Server for UNIX.
  - [PyInstaller](https://www.pyinstaller.org/) - Converts Python applications into stand-alone executables.

---

## Project Structure

```bash
CP-Demo-Server/
│
├── attack_generator.py               # Script to generate attack simulations
├── certificate/                      # Directory for SSL certificates
│   ├── cert.pem                      # Public certificate
│   ├── cp_demo_server.p12            # PKCS#12 archive containing cert and key
│   ├── key.pem                       # Private key
│   └── openssl.cnf                   # OpenSSL configuration file
├── data/                             # Data storage directory
│   ├── cp_demo_server.log            # Server log file
│   ├── db.log                        # Database log file
│   ├── secret_key = super secret key  # Configuration for Flask secret key
│   ├── generated_files.db            # Database for generated files
│   ├── ioc_files/                    # Indicators of Compromise (IoC) files
│   │   ├── docx_ioc_demo.docx        # Sample DOCX IoC file
│   │   ├── endpoint_security_datasheet.pdf # Sample PDF IoC file
│   │   └── ioc_demo.csv               # Sample CSV IoC file
│   ├── ips_protections_demo.csv      # IPS protections data
│   ├── protections.db                # Database for IPS protections
│   └── run_script.log                # Log for run scripts
├── db.py                             # Database setup and management script
├── file_generator.py                 # Script for generating files
├── files/                            # Directory for various files
│   ├── generated_files/              # Directory for generated/downloadable files
│   ├── malicious_urls.txt            # List of malicious URLs
│   └── pdf_assets/                   # Assets used in PDF generation
│       ├── sample_mp3_file.mp3        # Sample MP3 file
│       ├── sample_mp4_file.mp4        # Sample MP4 file
│       ├── sample_pdf_file.pdf        # Sample PDF file
│       └── sample_png_img.png         # Sample PNG image
├── __init__.py                       # Python package initializer
├── Install_script.sh                 # Shell script for installation
├── __pycache__/                      # Compiled Python files
│   ├── attack_generator.cpython-312.pyc
│   ├── db.cpython-312.pyc
│   ├── file_generator.cpython-312.pyc
│   ├── __init__.cpython-312.pyc
│   ├── run.cpython-312.pyc
│   └── views.cpython-312.pyc
├── README.MD                         # Current README file
├── README.MD.old                     # Previous version of README
├── requirements.txt                  # Python dependencies
├── run.py                            # Entry point for running the application
├── scripts/                          # Directory for auxiliary scripts
│   ├── css/                           # CSS assets
│   │   ├── bootstrap-toggle.css        # Bootstrap toggle styles
│   │   ├── dark-mode.css               # Dark mode styles
│   │   ├── datatables.css               # DataTables styles
│   │   └── styles.css                   # Custom styles
│   ├── js/                            # JavaScript assets
│   │   ├── bootstrap_toggle.js          # Bootstrap toggle scripts
│   │   └── dark-mode-switch.js          # Dark mode switch scripts
│   └── random_files/                  # Directory for random file generation
│       ├── random_file_generator.py     # Script to generate random files
│       └── words_list.txt               # List of words for file generation
├── static/                           # Static assets for the web app
│   ├── check-point-logo-large.webp    # Check Point logo (large)
│   ├── check_point.png                 # Check Point logo
│   ├── favicon.ico                     # Favicon for the website
│   ├── favicons/                       # Additional favicon assets
│   │   ├── android-chrome-192x192.png
│   │   ├── android-chrome-512x512.png
│   │   ├── apple-touch-icon.png
│   │   ├── favicon-16x16.png
│   │   ├── favicon-32x32.png
│   │   └── site.webmanifest             # Web manifest for PWA support
│   ├── loadingimage.gif                # Loading animation image
│   └── quantum_logo.jpg                 # Quantum logo image
├── templates/                        # HTML templates for the web app
│   ├── attack_generators.html          # Attack generators page
│   ├── av.html                         # Antivirus (AV) page
│   ├── base.html                       # Base HTML template
│   ├── footbar.html                    # Footer bar template
│   ├── index.html                      # Home page
│   ├── ips.html                        # Intrusion Prevention System (IPS) page
│   ├── navbar.html                     # Navigation bar template
│   └── te.html                         # TE page (specific purpose)
├── tree.txt                          # Text file containing the project directory tree
└── views.py                          # View functions for the web app

```

**Explanation of Key Directories:**

- **`data/`:** Contains databases, log files, and CSV data used by `db.py`.
- **`data/ioc_files/`:** Contains the CSV and PDF Test FIles for the IoC demo.
- **`templates/`:** Holds HTML templates for rendering web pages.
- **`static/`:** Stores static assets like CSS, JavaScript, and site images.
- **`files/generated_files/`:** Directory where generated/downloadable files are stored.
- **`files/malware_samples/`:** Directory where the Malware Files files are stored.
- **`files/pdf_assets/`:** Contains files used by the PDF generator.
---

## Installation

### Prerequisites

Ensure the following are installed on your system:

1. **Python 3.8+**
2. **Pip**: Python package manager.
3. **Virtualenv**: To create isolated Python environments.
4. **System Dependencies** (see below).

### Setup Instructions


**Clone the Repository:**

```bash
git clone https://github.com/alshawwaf/cp_demo_server.git
```

Install System-Level Dependencies (Linux Example):

```bash
sudo apt update
sudo apt install -y python3-virtualenv libpcap-dev libffi-dev build-essential gcc ghostscript imagemagick libcurl4-openssl-dev mingw-w64
```
Set Up a Virtual Environment:

```bash
virtualenv venv
source venv/bin/activate
```

Install Python Dependencies:

```bash
pip install flask flask-wtf requests scapy
```

Grant Network Permissions for Scapy:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip venv/bin/python3
```

Generate SSL Certificates:

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
emailAddress = kalshaww@checkpoint.com
EOF
```
Generate Self-Signed Certificates:

```bash
sudo apt install openssl -y
openssl req -x509 --config certificate/openssl.cnf -newkey rsa:4096 -nodes -out certificate/cert.pem -keyout certificate/key.pem -days 365

openssl pkcs12 -export -out certificate/cp_demo_server.p12 -inkey certificate/key.pem -in certificate/cert.pem -passout pass:vpn123!
```

Run the Application:

```bash
python run.py
```
### Access the Application:

Open your browser and navigate to http://127.0.0.1:8080.

Run as a Service (Optional):

To run the application as a service using systemd, follow these steps:

Create the Service File:

```bash
sudo nano /etc/systemd/system/cp_demo_server.service
```

Add the Following Content:

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

Reload systemd and Enable the Service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cp_demo_server.service
sudo systemctl start cp_demo_server.service
```

## License
Licensed under the MIT License. See the LICENSE file for details.

## Contact
For any inquiries or support, please contact:

- Author: Khalid Alshawwaf
- Email: kalshaww@checkpoint.com
- GitHub: alshawwaf

✨ Thank you for using CP Demo Server! ✨

---
