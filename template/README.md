# Vehicle Integration Template

Use these templates to integrate any vehicle with ATAK via Kaonic 1S mesh radios.

## Files

- `cot_sender_template.py` — sends vehicle position to ATAK map
- `command_receiver_template.py` — receives commands from ATAK and calls your vehicle's API

## How It Works

Both scripts communicate over UDP multicast on `239.2.3.1:6969` its the same address ATAK uses natively. The Kaonic bridge picks up that traffic and relays it through the Sub-GHz mesh to the operator's Kaonic, which rebroadcasts it to the ATAK phone.

## Setup

1. Connect your vehicle's companion computer to a Kaonic 1S via USB
2. Assign a static IP to the Kaonic interface (e.g. `192.168.10.85`)
3. Run both scripts on the companion computer
4. Connect the operator's ATAK phone to the operator Kaonic's WiFi

## What To Change

### cot_sender_template.py
- `MULTICAST_IFACE_IP` — IP of the interface connected to the Kaonic
- `ORIGIN_LAT/LON/HAE` — GPS coordinates of your test site origin
- `CALLSIGN` — display name shown in ATAK
- `UID` — unique ID for this vehicle
- `COT_TYPE` — `a-f-A-M-F-Q` for UAV, `a-f-G-U-C` for ground vehicle
- The `get_position()` function — replace with however your vehicle reports position

### command_receiver_template.py
- `MCAST_IFACE` — IP of the interface connected to the Kaonic
- `TARGET_UID` — must match `UID` in cot_sender_template.py
- The command handlers — replace the `pass` statements with your vehicle's actual API calls

## Adding More Commands

Add a button in the ATAK plugin and add a handler in `command_receiver_template.py`:

```python
elif command == "YOUR_COMMAND":
    your_vehicle_api.do_something()
```
