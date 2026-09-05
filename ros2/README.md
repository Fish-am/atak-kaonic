# ROS 2 ATAK Bridge

These two nodes integrate a ROS 2 / MAVROS drone with ATAK via Kaonic 1S mesh radios.

## Files

- `atak_bridge.py` — reads position from MAVROS and sends it to ATAK as CoT
- `command_receiver.py` — receives commands from ATAK and calls MAVROS services

## Requirements

- ROS 2 (tested on Humble)
- MAVROS
- A Kaonic 1S radio connected to the companion computer via USB
- The companion computer must have a static IP on the Kaonic network (`192.168.10.x`)

## Installation

Copy both files into your ROS 2 package, then add to `setup.py`:

```python
'console_scripts': [
    'atak_bridge = your_package.atak_bridge:main',
    'command_receiver = your_package.command_receiver:main',
],
```

Add both to your launch file:

```python
Node(package='your_package', executable='atak_bridge', output='screen'),
Node(package='your_package', executable='command_receiver', output='screen'),
```

Rebuild: colcon build --packages-select your_package


## Config

At the top of each file, change these values:

### atak_bridge.py
| Variable | Description |
|----------|-------------|
| `MULTICAST_IFACE_IP` | IP of the interface connected to the Kaonic |
| `ORIGIN_LAT/LON/HAE` | GPS coordinates of your test site origin |
| `CALLSIGN` | Display name shown in ATAK |
| `UID` | Unique ID for this vehicle — must be unique per vehicle |
| `COT_TYPE` | ATAK icon type — `a-f-A-M-F-Q` for UAV, `a-f-G-U-C` for ground |

### command_receiver.py
| Variable | Description |
|----------|-------------|
| `MCAST_IFACE` | IP of the interface connected to the Kaonic |
| `TARGET_UID` | Must match `UID` in atak_bridge.py |
| `TAKEOFF_ALT` | Target hover altitude in meters |

## Adding Custom Commands

To add a new command, add a button in the ATAK plugin and add an `elif` branch in `command_receiver.py`:

```python
elif command == "YOUR_COMMAND":
    # call your MAVROS service or ROS 2 topic here
```