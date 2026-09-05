#!/usr/bin/env python3
import socket
import math
from datetime import datetime, timedelta, timezone
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseStamped

# ──────────────────────────────────────────────────────────────────────
ATAK_IP            = "239.2.3.1"
ATAK_PORT          = 6969
MULTICAST_IFACE_IP = "192.168.10.85"  # Kaonic USB interface IP
ORIGIN_LAT         = 38.8847
ORIGIN_LON         = -77.1035
ORIGIN_HAE         = 85.0
CALLSIGN           = "Hexsoon450"
UID                = "ROS2-HEXSOON450-1"
COT_TYPE           = "a-f-A-M-F-Q"
PUBLISH_HZ         = 1.0
# ─────────────────────────────────────────────────────────────────────────────

class AtakBridge(Node):
    def __init__(self):
        super().__init__("atak_bridge")
        self.lat = None
        self.lon = None
        self.hae = ORIGIN_HAE
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        if MULTICAST_IFACE_IP:
            self.sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_IF,
                socket.inet_aton(MULTICAST_IFACE_IP)
            )
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.create_subscription(PoseStamped, '/mavros/local_position/pose', self._on_pose, qos)
        self.create_timer(1.0 / PUBLISH_HZ, self._tick)
        self.get_logger().info(f"ATAK bridge started → {ATAK_IP}:{ATAK_PORT} as '{CALLSIGN}'")

    def _on_pose(self, msg):
        east_m  = msg.pose.position.x
        north_m = msg.pose.position.y
        up_m    = msg.pose.position.z
        self.lat = ORIGIN_LAT + (north_m / 111320.0)
        self.lon = ORIGIN_LON + (east_m  / (111320.0 * math.cos(math.radians(ORIGIN_LAT))))
        self.hae = ORIGIN_HAE + up_m

    def _tick(self):
        if self.lat is None:
            self.get_logger().warn("No pose yet...", throttle_duration_sec=5.0)
            return
        cot = self._build_cot()
        try:
            self.sock.sendto(cot.encode(), (ATAK_IP, ATAK_PORT))
        except OSError as exc:
            self.get_logger().warn(f'UDP send failed: {exc}')

    def _build_cot(self):
        now   = datetime.now(timezone.utc)
        stale = now + timedelta(seconds=5)
        fmt   = "%Y-%m-%dT%H:%M:%S.%fZ"
        t, s  = now.strftime(fmt), stale.strftime(fmt)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<event version="2.0" uid="{UID}" type="{COT_TYPE}" how="m-g" '
            f'time="{t}" start="{t}" stale="{s}">'
            f'<point lat="{self.lat:.7f}" lon="{self.lon:.7f}" hae="{self.hae:.1f}" ce="9999999.0" le="9999999.0"/>'
            f'<detail><contact callsign="{CALLSIGN}"/>'
            '<__group name="Cyan" role="Team Member"/>'
            '</detail></event>'
        )

def main():
    rclpy.init()
    node = AtakBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()