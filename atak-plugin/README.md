# Drones and Orbs — ATAK Plugin

An ATAK plugin for displaying drone telemetry and sending high-level commands (ARM, HOLD, DISARM, TAKEOFF) to vehicles over the Kaonic mesh network.

## Requirements

- Android Studio
- ATAK-CIV SDK (tested with 5.5.0.7) — download from tak.gov (free account required)
- An Android phone running ATAK-CIV

## Setup

### 1. Get the ATAK SDK

Download `ATAK-CIV-5.5.0.7-SDK` from tak.gov and unzip it. Place the `dronesandorbs` plugin folder inside the SDK's `plugins/` directory:

    ATAK-CIV-5.5.0.7-SDK/
        plugins/
            dronesandorbs/


### 2. Open in Android Studio

Open Android Studio → Open → select the `dronesandorbs` folder. Let Gradle sync finish.

### 3. Build and install on phone

Connect your Android phone via USB cable. In Android Studio:
- Set build variant to `civDebug` (bottom left of Android Studio)
- Click the green Run button (or Shift+F10)
- Select your phone as the target device

Android Studio will build and install the plugin directly on the phone. ATAK must already be installed for the plugin to work.

### 4. Enable the plugin in ATAK

On the phone, open ATAK → hamburger menu (top right) → Plugins → find Drones and Orbs → enable it. The plugin icon will appear in the ATAK toolbar.

## How Commands Work

When a button is tapped in the plugin, it sends a CoT XML packet to `239.2.3.1:6969`:

```xml
<event type="b-c-drone-cmd">
    <detail>
        <drone_command target_uid="VEHICLE-UID" command="ARM" value="true"/>
    </detail>
</event>
```

The Kaonic bridge picks this up and relays it through the mesh to the vehicle's companion computer, where `command_receiver.py` (or `command_receiver_template.py`) receives and executes it.

## Adding a New Button

### Step 1 — Add the button to the layout

Open `app/src/main/res/layout/drone_detail_layout.xml` and add a new button inside the button container:

```xml
<Button
    android:id="@+id/yourCommandButton"
    android:layout_width="0dp"
    android:layout_weight="1"
    android:layout_height="wrap_content"
    android:text="YOUR COMMAND"
    android:backgroundTint="#FF6600"
    android:textColor="#FFFFFF"/>
```

### Step 2 — Wire up the button in Java

Open `app/src/main/java/com/atakmap/android/plugintemplate/PluginTemplateDropDownReceiver.java` and find the `showDetail()` method. Add your button handler alongside the existing ones:

```java
detailView.findViewById(R.id.yourCommandButton).setOnClickListener(new View.OnClickListener() {
    @Override
    public void onClick(View v) {
        sendCommand("YOUR-VEHICLE-UID", "YOUR_COMMAND", "");
    }
});
```

### Step 3 — Handle the command on the vehicle

In `command_receiver.py` or `command_receiver_template.py`, add a new branch:

```python
elif command == "YOUR_COMMAND":
    your_vehicle_api.do_something()
```

### Step 4 — Rebuild and reinstall

In Android Studio click Run (Shift+F10) to rebuild and push to the phone. No need to manually uninstall first — Android Studio replaces the existing version.

## Changing the Target Vehicle UID

The UID tells the command receiver which vehicle to control. It's hardcoded in `PluginTemplateDropDownReceiver.java` inside the `sendCommand()` calls:

```java
sendCommand("ROS2-HEXSOON450-1", "ARM", "true");
```

Change `"ROS2-HEXSOON450-1"` to match the `UID` constant in your `cot_sender_template.py` or `atak_bridge.py`.

## Changing the Drone Roster

Currently the plugin shows three hardcoded fake drone cards (ORB-01, ORB-02, ORB-03). These are defined in the `PluginTemplateDropDownReceiver` constructor:

```java
fakeDrones.add(new FakeDrone("ORB-01", ...));
```

Change the callsigns, battery values, and other fields there to match your actual vehicles. Real-time telemetry population from CoT data is a planned future feature.

## File Reference

| File | Purpose |
|------|---------|
| `app/src/main/java/.../PluginTemplateDropDownReceiver.java` | Main plugin logic, button handlers, command sending |
| `app/src/main/res/layout/main_layout.xml` | Drone roster panel layout |
| `app/src/main/res/layout/drone_detail_layout.xml` | Individual drone detail view with buttons |
| `app/src/main/res/layout/drone_card_item.xml` | Single drone card in the roster |
| `app/src/main/res/values/strings.xml` | String resources |