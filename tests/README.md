# Testing Scripts

This directory contains remote testing scripts for validating firewall and security appliance functionality.

## Scripts

### 1. `trigger_attacks.py`
Triggers IPS (Intrusion Prevention System) attacks sequentially to test firewall blocking and generate logs.

**Usage:**
```bash
python trigger_attacks.py --server http://SERVER_IP:8080 --target TARGET_IP --file protections_example.txt
```

**Features:**
- Sequential attack execution
- Real-time progress with visual indicators (✓ success, 🛡 blocked, ✗ failed)
- Detailed statistics (success rate, block rate, duration)
- Configurable delay between attacks

### 2. `test_malware_downloads.py`
Tests malware file downloads to validate anti-virus/URL filtering blocking.

**Usage:**
```bash
python test_malware_downloads.py --server http://SERVER_IP:8080 --file malware_files_example.txt
```

**Features:**
- Stream & flush (files never saved to disk)
- Detects firewall blocks (connection resets/timeouts)
- Download statistics with byte counts
- Safe testing (no infection risk)

## Example Files

- `protections_example.txt` - Sample IPS protection names
- `malware_files_example.txt` - Sample malware file paths

## Requirements

```bash
pip install requests beautifulsoup4
```

> **Note:** The server's `/api/run_attack` and `/av/*` routes require an authenticated session (see the login credentials in the top-level README). These scripts issue plain requests and do not log in on their own, so run them against a server instance that is reachable with a valid session, or add the login step before use.

## Safety Notes

⚠️ **Malware Download Testing:**
- All files are streamed but never saved to disk
- Data is immediately flushed for safety
- Designed for firewall testing only

🛡️ **Firewall Testing:**
- Generates real attack traffic
- Use only in controlled lab environments
- Requires proper authorization
