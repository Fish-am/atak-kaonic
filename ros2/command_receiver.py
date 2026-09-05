#!/usr/bin/env python3
import socket
import struct
import xml.etree.ElementTree as ET
import rclpy
from rclpy.node import Node
from mavros_msgs.srv import CommandBool, SetMode, CommandTOL

# ──────────────────────────────────────────────────────────────────────
MCAST_GRP    = "239.2.3.1"
MCAST_PORT   = 6969
MCAST_IFACE  = "192.168.10.85"  # Kaonic USB interface IP
TARGET_UID   = "ROS2-HEXSOON450-1"
COT_CMD_TYPE = "b-c-drone-cmd"
TAKEOFF_ALT  = 2.0
# ─────────────────────────────────────────────────────────────────────────────

class CommandReceiver(Node):
    def __init__(self):
        super().__init__("command_receiver")
        self.arming_client  = self.create_client(CommandBool, "/mavros/cmd/arming")
        self.mode_client    = self.create_client(SetMode,     "/mavros/set_mode")
        self.takeoff_client = self.create_client(CommandTOL,  "/mavros/cmd/takeoff")
        self.get_logger().info("Waiting for MAVROS services...")
        self.arming_client.wait_for_service(timeout_sec=10.0)
        self.mode_client.wait_for_service(timeout_sec=10.0)
        self.takeoff_client.wait_for_service(timeout_sec=10.0)
        self.get_logger().info("MAVROS services ready")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", MCAST_PORT))
        mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(MCAST_IFACE))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.setblocking(False)
        self.create_timer(0.1, self._poll)
        self.get_logger().info(f"Listening on {MCAST_GRP}:{MCAST_PORT} for '{TARGET_UID}'")

    def _poll(self):
        try:
            data, _ = self.sock.recvfrom(65535)
            self._handle_packet(data.decode("utf-8", errors="ignore"))
        except BlockingIOError:
            pass
        except Exception as e:
            self.get_logger().warn(f"Socket error: {e}")

    def _handle_packet(self, xml_str):
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
        self.get_logger().info(f"Received command: {command} value={value}")
        if command == "ARM":
            self._send_arm(True)
        elif command == "DISARM":
            self._send_arm(False)
        elif command == "HOLD":
            self._send_mode("LOITER")
        elif command == "RTL":
            self._send_mode("RTL")
        elif command == "TAKEOFF":
            self._send_takeoff()
        else:
            self.get_logger().warn(f"Unknown command: {command}")

    def _send_arm(self, arm: bool):
        req = CommandBool.Request()
        req.value = arm
        future = self.arming_client.call_async(req)
        future.add_done_callback(
            lambda f: self.get_logger().info(
                f"ARM={arm} result: {f.result().success if f.result() else 'failed'}"
            )
        )

    def _send_mode(self, mode: str):
        req = SetMode.Request()
        req.custom_mode = mode
        future = self.mode_client.call_async(req)
        future.add_done_callback(
            lambda f: self.get_logger().info(
                f"SET_MODE={mode} result: {f.result().mode_sent if f.result() else 'failed'}"
            )
        )

    def _send_takeoff(self):
        mode_req = SetMode.Request()
        mode_req.custom_mode = "GUIDED"
        mode_future = self.mode_client.call_async(mode_req)

        def on_mode_set(f):
            if f.result() and f.result().mode_sent:
                self.get_logger().info("GUIDED mode set, arming...")
                arm_req = CommandBool.Request()
                arm_req.value = True
                arm_future = self.arming_client.call_async(arm_req)

                def on_armed(f2):
                    if f2.result() and f2.result().success:
                        self.get_logger().info(f"Armed, taking off to {TAKEOFF_ALT}m...")
                        to_req = CommandTOL.Request()
                        to_req.altitude  = TAKEOFF_ALT
                        to_req.latitude  = 0.0
                        to_req.longitude = 0.0
                        to_req.min_pitch = 0.0
                        to_req.yaw       = 0.0
                        to_future = self.takeoff_client.call_async(to_req)
                        to_future.add_done_callback(
                            lambda f3: self.get_logger().info(
                                f"TAKEOFF result: {f3.result().success if f3.result() else 'failed'}"
                            )
                        )
                    else:
                        self.get_logger().warn("Arm failed — aborting takeoff")

                arm_future.add_done_callback(on_armed)
            else:
                self.get_logger().warn("GUIDED mode failed — aborting takeoff")

        mode_future.add_done_callback(on_mode_set)

    def destroy_node(self):
        self.sock.close()
        super().destroy_node()

def main():
    rclpy.init()
    node = CommandReceiver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()