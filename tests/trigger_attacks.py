#!/usr/bin/env python3
"""
IPS Attack Trigger Script
==========================
Remote testing script for triggering IPS protections sequentially.
Used to simulate attacks and verify firewall blocking/logging capabilities.

Usage:
    python trigger_attacks.py --server http://SERVER_IP:5000 --target TARGET_IP
    
Example:
    python trigger_attacks.py --server http://192.168.1.100:5000 --target 10.0.0.1
"""

import argparse
import requests
import sys
import time
from typing import List, Dict
from datetime import datetime


class IPSAttackTrigger:
    """Remote IPS attack trigger for testing firewall capabilities."""
    
    def __init__(self, server_url: str, target_ip: str, delay: float = 0.1):
        """
        Initialize the attack trigger.
        
        Args:
            server_url: Base URL of the IPS server (e.g., http://192.168.1.100:5000)
            target_ip: Target IP address for the attacks
            delay: Delay in seconds between attacks (default: 0.1)
        """
        self.server_url = server_url.rstrip('/')
        self.target_ip = target_ip
        self.delay = delay
        self.session = requests.Session()
        
    def get_protections(self) -> List[str]:
        """Fetch list of available protections from the server."""
        try:
            response = self.session.get(f"{self.server_url}/ips")
            response.raise_for_status()
            
            # Parse HTML to extract protection names (simple approach)
            # In production, you might want to add an API endpoint that returns JSON
            print(f"✓ Connected to server: {self.server_url}")
            print("⚠ Note: Using API endpoint to trigger attacks\n")
            
            # For now, we'll need to manually maintain the list or use the API
            # Since we have the /api/run_attack endpoint, we can list protections
            # or just return empty and let user specify
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error connecting to server: {e}")
            sys.exit(1)
    
    def trigger_single_attack(self, protection_name: str) -> Dict:
        """
        Trigger a single attack.
        
        Args:
            protection_name: Name of the protection to trigger
            
        Returns:
            Response data from the server
        """
        url = f"{self.server_url}/api/run_attack"
        payload = {
            "protection_name": protection_name,
            "target_ip": self.target_ip
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Request failed: {str(e)}",
                "status_code": 0
            }
    
    def trigger_all_attacks(self, protection_names: List[str]):
        """
        Trigger all attacks sequentially.
        
        Args:
            protection_names: List of protection names to trigger
        """
        total = len(protection_names)
        successful = 0
        failed = 0
        blocked = 0
        
        print(f"{'='*70}")
        print(f"Starting Sequential Attack Execution")
        print(f"{'='*70}")
        print(f"Server: {self.server_url}")
        print(f"Target IP: {self.target_ip}")
        print(f"Total Attacks: {total}")
        print(f"Delay: {self.delay}s between attacks")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        for idx, protection_name in enumerate(protection_names, 1):
            print(f"[{idx}/{total}] Triggering: {protection_name:<50}", end=" ")
            
            result = self.trigger_single_attack(protection_name)
            
            if result.get("success"):
                status_code = result.get("status_code", 0)
                if status_code == 200:
                    print(f"✓ SUCCESS (200)")
                    successful += 1
                elif "blocked" in result.get("message", "").lower() or status_code == 104:
                    print(f"🛡 BLOCKED ({status_code})")
                    blocked += 1
                else:
                    print(f"⚠ Response ({status_code})")
                    successful += 1
            else:
                print(f"✗ FAILED ({result.get('status_code', 0)})")
                failed += 1
                print(f"    └─ {result.get('message', 'Unknown error')}")
            
            # Delay between attacks
            if idx < total:
                time.sleep(self.delay)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*70}")
        print(f"Execution Summary")
        print(f"{'='*70}")
        print(f"Total Attacks:   {total}")
        print(f"Successful:      {successful} ({successful/total*100:.1f}%)")
        print(f"Blocked:         {blocked} ({blocked/total*100:.1f}%)")
        print(f"Failed:          {failed} ({failed/total*100:.1f}%)")
        print(f"Duration:        {duration:.2f}s")
        print(f"Avg per attack:  {duration/total:.3f}s")
        print(f"{'='*70}")


def load_protections_from_file(filepath: str) -> List[str]:
    """Load protection names from a text file (one per line)."""
    try:
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"✗ Error: File not found: {filepath}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Remote IPS Attack Trigger for Firewall Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trigger attacks from a list file
  python trigger_attacks.py --server http://192.168.1.100:5000 --target 10.0.0.1 --file protections.txt
  
  # Trigger specific attacks
  python trigger_attacks.py --server http://192.168.1.100:5000 --target 10.0.0.1 --attacks "Attack1" "Attack2"
  
  # Adjust delay between attacks
  python trigger_attacks.py --server http://192.168.1.100:5000 --target 10.0.0.1 --file protections.txt --delay 0.5

Protection List File Format:
  Create a text file with one protection name per line:
  
    MS_IIS_WebDAV_nPropfind
    CVE-2021-44228_Log4j_JNDI
    SQL_Injection_Generic
    # Comments start with #
        """
    )
    
    parser.add_argument('--server', required=True,
                        help='IPS server URL (e.g., http://192.168.1.100:5000)')
    parser.add_argument('--target', required=True,
                        help='Target IP address for attacks')
    parser.add_argument('--file', '-f',
                        help='File containing protection names (one per line)')
    parser.add_argument('--attacks', '-a', nargs='+',
                        help='Space-separated list of protection names')
    parser.add_argument('--delay', type=float, default=0.1,
                        help='Delay in seconds between attacks (default: 0.1)')
    
    args = parser.parse_args()
    
    # Get protection names
    if args.file:
        protections = load_protections_from_file(args.file)
    elif args.attacks:
        protections = args.attacks
    else:
        print("✗ Error: You must specify either --file or --attacks")
        parser.print_help()
        sys.exit(1)
    
    if not protections:
        print("✗ Error: No protections to trigger")
        sys.exit(1)
    
    # Create trigger and run
    trigger = IPSAttackTrigger(args.server, args.target, args.delay)
    trigger.trigger_all_attacks(protections)


if __name__ == "__main__":
    main()
