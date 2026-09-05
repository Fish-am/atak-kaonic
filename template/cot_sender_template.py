#!/usr/bin/env python3
"""
CoT Position Sender Template
Sends vehicle position to ATAK via Kaonic 1S mesh radio.
Replace get_position() with however your vehicle reports position.
Works with any vehicle — no ROS 2 required.
"""
import socket
import time
import math
from datetime import datetime, timedelta, timezone

# ──change these for your vehicle ────────────────────────────────────
ATAK_IP            = "239.2.3.1"
ATAK_PORT          = 6969
MULTICAST_IFACE_IP = "192.168.10.85"  # IP of interface connected to Kaonic
ORIGIN_LAT         = 0.0              # GPS lat of your test site origin
ORIGIN_LON         = 0.0              # GPS lon of your test site origin
ORIGIN_HAE         = 0.0             # Altitude of origin in meters
CALLSIGN           = "VEHICLE-01"     # Display name in ATAK
UID                = "VEHICLE-01-UID" # Unique ID — must be unique per vehicle
COT_TYPE           = "a-f-A-M-F-Q"   # a-f-A-M-F-Q=UAV, a-f-G-U-C=ground
PUBLISH_HZ         = 1.0             # How often to send position (Hz)
# ─────────────────────────────────────────────────────────────────────────────


def get_position():
    """
    Replace this function with however your vehicle reports position.
    Must return (east_meters, north_meters, up_meters) relative to origin.

    Examples:
    - Read from a GPS module
    - Read from a MAVLink stream
    - Read from a ROS topic
    - Read from a custom telemetry API
    """
    # REPLACE THIS with your actual position source
    east_m  = 0.0
    north_m = 0.0
    up_m    = 0.0
    return east_m, north_m, up_m


def enu_to_latlon(east_m, north_m, up_m):
    lat = ORIGIN_LAT + (north_m / 111320.0)
    lon = ORIGIN_LON + (east_m / (111320.0 * math.cos(math.radians(ORIGIN_LAT))))
    hae = ORIGIN_HAE + up_m
    return lat, lon, hae


def build_cot(lat, lon, hae):
    now   = datetime.now(timezone.utc)
    stale = now + timedelta(seconds=5)
    fmt   = "%Y-%m-%dT%H:%M:%S.%fZ"
    t, s  = now.strftime(fmt), stale.strftime(fmt)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<event version="2.0" uid="{UID}" type="{COT_TYPE}" how="m-g" '
        f'time="{t}" start="{t}" stale="{s}">'
        f'<point lat="{lat:.7f}" lon="{lon:.7f}" hae="{hae:.1f}" ce="9999999.0" le="9999999.0"/>'
        f'<detail><contact callsign="{CALLSIGN}"/>'
        '<__group name="Cyan" role="Team Member"/>'
        '</detail></event>'
    )


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    if MULTICAST_IFACE_IP:
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(MULTICAST_IFACE_IP)
        )
    print(f"Sending position to {ATAK_IP}:{ATAK_PORT} as '{CALLSIGN}'")
    interval = 1.0 / PUBLISH_HZ
    while True:
        try:
            east_m, north_m, up_m = get_position()
            lat, lon, hae = enu_to_latlon(east_m, north_m, up_m)
            cot = build_cot(lat, lon, hae)
            sock.sendto(cot.encode(), (ATAK_IP, ATAK_PORT))
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    main()