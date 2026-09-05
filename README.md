# ATAK Kaonic Vehicle Bridge

A complete system for displaying any vehicle (drone, UGV, ground robot) on the ATAK tactical map and sending high-level commands to it from ATAK, using Kaonic 1S Sub-GHz mesh radios as the communication link.

## What This Does

- **Vehicle appears on ATAK map** in real time with its position, callsign, and a custom icon
- **Commands sent from ATAK** (ARM, HOLD, DISARM, TAKEOFF, or any custom command) travel wirelessly through the Kaonic mesh and execute on the vehicle
- **Works at range** — the two Kaonics communicate over Sub-GHz radio (869 MHz) without WiFi or cell coverage

## How It Works

Each vehicle has a Kaonic 1S radio connected to its companion computer. The operator has a second Kaonic connected to their ATAK phone via WiFi. The two Kaonics relay traffic between them over Sub-GHz mesh using the Reticulum protocol.

On the vehicle side, a script reads the vehicle's position and broadcasts it as CoT (Cursor on Target) XML to the local Kaonic network every second. The Kaonic picks it up and relays it to the operator's Kaonic, which rebroadcasts it to the ATAK phone. ATAK receives the CoT and displays the vehicle as a marker on the map.

Commands work in reverse — tapping a button in the ATAK plugin sends a CoT command packet, which travels through the mesh to the vehicle's Kaonic, gets rebroadcast locally, and a receiver script on the companion computer picks it up and calls the appropriate vehicle API.

## Repository Structure

    ros2/
        atak_bridge.py
        command_receiver.py
        README.md

    template/
        cot_sender_template.py
        command_receiver_template.py
        README.md

    atak-plugin/
        dronesandorbs/
        README.md


## Which Files Do I Use?

**My vehicle runs ROS 2 and MAVROS** (e.g. ArduPilot drone with Jetson):
→ Use the files in `ros2/`. See `ros2/README.md`.

**My vehicle uses a different stack** (custom firmware, MAVLink direct, proprietary API):
→ Use the files in `template/`. See `template/README.md`. Replace the placeholder functions with your vehicle's actual position source and command API.

**Setting up the operator side:**
→ Build and install the ATAK plugin from `atak-plugin/`. See `atak-plugin/README.md`.

## Hardware Required

- 2x Kaonic 1S tactical mesh radios (one per side)
- A companion computer on the vehicle (Jetson, Raspberry Pi, or any Linux system)
- An Android phone running ATAK-CIV
- Sub-GHz antennas on both Kaonics (869 MHz)



## Supported Commands (out of the box)

| Button in ATAK | Command | What it does |
|----------------|---------|--------------|
| ARM | ARM | Arms the vehicle |
| HOLD | HOLD | Hold position |
| DISARM | DISARM | Disarms the vehicle |
| TAKEOFF | TAKEOFF | Arms and takes off to target altitude |

Additional commands can be added by adding a button in the ATAK plugin and a handler in the receiver script. See `atak-plugin/README.md` for instructions.

## Adding a New Vehicle Type

1. Copy `template/cot_sender_template.py` and `template/command_receiver_template.py` to your vehicle's companion computer
2. Fill in the config variables at the top of each file
3. Replace `get_position()` in the sender with your vehicle's position source
4. Replace the `handle_*()` functions in the receiver with your vehicle's command API
5. Connect a Kaonic 1S to the companion computer via USB
6. Assign a static IP to the Kaonic interface (e.g. `192.168.10.85`)
7. Run both scripts
8. Update the `target_uid` in the ATAK plugin to match your vehicle's UID
