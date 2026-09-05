#!/usr/bin/env python3
"""
ATAK Command Receiver Template
Receives commands from ATAK via Kaonic 1S mesh radio.
Replace the command handlers with your vehicle's actual API calls.
Works with any vehicle — no ROS 2 required.
"""
import socket
import struct
import xml.etree.ElementTree as ET

# ──change these for your vehicle ────────────────────────────────────
MCAST_GRP    = "239.2.3.1"
MCAST_PORT   = 6969
MCAST_IFACE  = "192.168.10.85"  # IP of interface connected to Kaonic
TARGET_UID   = "VEHICLE-01-UID" # Must match UID in cot_sender_template.py
COT_CMD_TYPE = "b-c-drone-cmd"
# ─────────────────────────────────────────────────────────────────────────────


def handle_arm():
    """Replace with your vehicle's arm command."""
    print("ARM received")
    pass


def handle_disarm():
    """Replace with your vehicle's disarm command."""
    print("DISARM received")
    pass


def handle_hold():
    """Replace with your vehicle's hold/loiter command."""
    print("HOLD received")
    pass


def handle_takeoff():
    """Replace with your vehicle's takeoff command."""
    print("TAKEOFF received")
    pass


def handle_packet(xml_str):
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return
    if root.get("type") != COT_CMD_TYPE:
        return
    cmd_el = root.find(".//drone_command")
    if cmd_el is None:
        return
    if cmd_el.get("target_uid") != TARGET_UID:
        return
    command = cmd_el.get("command", "").upper()
    value   = cmd_el.get("value", "").lower()
    print(f"Received command: {command} value={value}")
    if command == "ARM":
        handle_arm()
    elif command == "DISARM":
        handle_disarm()
    elif command == "HOLD":
        handle_hold()
    elif command == "TAKEOFF":
        handle_takeoff()
    else:
        print(f"Unknown command: {command}")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MCAST_PORT))
    mreq = struct.pack("4s4s",
        socket.inet_aton(MCAST_GRP),
        socket.inet_aton(MCAST_IFACE)
    )
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print(f"Listening on {MCAST_GRP}:{MCAST_PORT} for '{TARGET_UID}'")
    while True:
        try:
            data, _ = sock.recvfrom(65535)
            handle_packet(data.decode("utf-8", errors="ignore"))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()