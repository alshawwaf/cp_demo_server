# CP Demo Server

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.0-lightgrey.svg)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Auth](https://img.shields.io/badge/Auth-Login%20Protected-green.svg)
![Encryption](https://img.shields.io/badge/Samples-AES--128%20Encrypted-red.svg)

A Flask-based threat prevention demo server for testing Check Point security controls locally — IPS triggers, real malware downloads, and threat emulation file generation.

![Demo](https://github.com/alshawwaf/cp_demo_server/blob/GA/app/data/readme_assets/cp_demo_server_demo.gif)

---

## Features

| Module | Description |
|--------|-------------|
| **IPS Attacks** | Trigger 25+ IPS protection signatures against a target IP |
| **Malware Samples** | Browse and download 225+ real malware samples (encrypted at rest) |
| **Threat Emulation** | Generate malicious files in 14 formats with configurable payloads |
| **Attack Simulator** | Launch network attacks: SYN flood, UDP flood, Slowloris, and more |
| **Email Delivery** | Send generated files as email attachments via SMTP |
| **REST API** | Full API with Swagger docs at `/apidocs/` |

---

## Security Design

### Login Protection

All routes require authentication. Default credentials:

| Username | Password |
|----------|----------|
| `admin` | `Cpwins!1@2026!` |

### Malware Samples — Encrypted at Rest

All 225 malware samples are stored as **AES-128-CBC encrypted** (`.enc`) files — both on disk and in this repository. The host antivirus never sees plaintext signatures.

- Files are decrypted **in memory only** at download time — plaintext never touches the filesystem
- Encryption key is stored at `app/data/.secret.key`
- To encrypt newly added samples: `python scripts/encrypt_samples.py`

---

## Quick Start — Docker (Recommended)

```bash
git clone -b GA https://github.com/alshawwaf/cp_demo_server.git
cd cp_demo_server
docker build -t cp_demo_server:latest .
docker run -d --name cp_demo_server -p 8080:8080 --restart unless-stopped cp_demo_server:latest
```

Open **http://localhost:8080** and log in with `admin / Cpwins!1@2026!`

> Malware samples are pre-encrypted in the repo. No extra steps needed — clone, build, run.

---

## Quick Start — Local Python

```bash
# Install system dependencies (Debian/Ubuntu)
sudo apt update && sudo apt install -y \
  python3-virtualenv libpcap-dev libffi-dev \
  build-essential gcc libcurl4-openssl-dev mingw-w64

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python run.py
```

Open **http://127.0.0.1:8080**

---

## Project Structure

```
cp_demo_server/
├── app/
│   ├── data/
│   │   ├── .secret.key              # AES encryption key for malware samples
│   │   ├── malware_samples/         # 225+ samples stored as .enc files
│   │   ├── generated_files/         # TE-generated downloadable files
│   │   ├── ioc_files/               # IoC CSV and PDF test files
│   │   ├── certificate/             # TLS/SSL certificates
│   │   └── email_config/            # SMTP configuration (JSON)
│   ├── templates/
│   │   ├── login.html               # Login page
│   │   ├── base.html                # Base layout
│   │   ├── index.html               # Home
│   │   ├── ips.html                 # IPS module
│   │   ├── av.html                  # Malware browser
│   │   └── te.html                  # Threat emulation
│   ├── static/                      # CSS, JS, favicon
│   ├── crypto_util.py               # At-rest encryption/decryption module
│   ├── views.py                     # All route handlers
│   ├── file_generator.py            # TE file generation logic
│   ├── attack_generator.py          # Network attack simulation
│   ├── db.py                        # SQLite helpers
│   └── email_service.py             # Flask-Mail wrapper
├── scripts/
│   └── encrypt_samples.py           # Encrypt new malware samples in-place
├── tests/
│   ├── trigger_attacks.py           # Remote IPS trigger script
│   ├── test_malware_downloads.py    # Remote malware download tester
│   └── README.md
├── Dockerfile
├── requirements.txt
└── run.py
```

---

## Modules

### IPS Attacks (`/ips`)

Trigger Check Point IPS signatures against a configured target IP. Supports 25+ protections. Also available via REST API:

```bash
curl -X POST http://localhost:8080/api/run_attack \
  -H "Content-Type: application/json" \
  -d '{"protection_name": "SQL Injection", "target_ip": "192.168.1.1"}'
```

### Malware Browser (`/av`)

Browse and download real malware samples across 14 families. Files are decrypted in memory on download — your AV only scans the encrypted blobs on disk:

```
Banking-Malware  Email-Worm  Net-Worm  Pony       RAT       Ransomware
Spyware          Stealer     Trojan    Virus       Worm      eicar      rogues
```

### Threat Emulation (`/te`)

Generate malicious test files in these formats:

```
pdf  docx  pptx  xlsx  rtf  exe  exe-64bit  elf  dylib  jpg  png  bmp  gif  tiff
```

Optional payload embeddings: URLs, scripts, images, video, audio, 3D content, sensitive links, data submission forms.

### Attack Simulator (`/attack_generators`)

```
ICMP Flood   SYN Flood    UDP Flood     Ping of Death  ARP Poisoning
DNS Spoofing DHCP Starvation HTTP Flood NTP Amplification Slowloris
```

---

## Remote Testing Scripts

```bash
# Test IPS protections against a firewall
python tests/trigger_attacks.py \
  --server http://SERVER_IP:8080 \
  --target TARGET_IP \
  --file tests/protections_example.txt

# Test malware download blocking
python tests/test_malware_downloads.py \
  --server http://SERVER_IP:8080 \
  --file tests/malware_files_example.txt
```

See [tests/README.md](tests/README.md) for full documentation.

---

## Adding New Malware Samples

```bash
# Copy files into the appropriate category directory
docker cp ./new_samples/. cp_demo_server:/usr/src/app/app/data/malware_samples/Category/

# Encrypt in-place inside the container
docker exec cp_demo_server python scripts/encrypt_samples.py

# Copy encrypted files back and commit (never commit plaintext)
docker cp cp_demo_server:/usr/src/app/app/data/malware_samples/. app/data/malware_samples/
git add app/data/malware_samples/
git commit -m "Add new encrypted samples"
```

---

## API Documentation

Swagger UI available at:

```
http://localhost:8080/apidocs/
```

---

## Optional: SSL Certificate

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out app/data/certificate/cert.pem \
  -keyout app/data/certificate/key.pem -days 365 \
  -subj "/C=CA/ST=ON/L=Ottawa/O=Demo/CN=localhost"

openssl pkcs12 -export \
  -out app/data/certificate/cp_demo_server.p12 \
  -inkey app/data/certificate/key.pem \
  -in app/data/certificate/cert.pem \
  -passout pass:vpn123!
```

---

## Optional: Run as a systemd Service

```bash
sudo tee /etc/systemd/system/cp_demo_server.service > /dev/null << EOF
[Unit]
Description=CP Demo Server
After=network.target

[Service]
User=YOUR_USER
WorkingDirectory=/path/to/cp_demo_server
ExecStart=/path/to/venv/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now cp_demo_server
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Web framework | Flask 3.1 |
| Encryption | cryptography (Fernet / AES-128-CBC) |
| UI | Bootstrap 5 + Bootstrap Icons |
| Database | SQLite |
| API docs | Flasgger (Swagger) |
| File generation | ReportLab, python-docx, Pillow, openpyxl, python-pptx |
| Network simulation | Scapy |
| Container | Docker (python:3.12-slim) |

---

## License

MIT
