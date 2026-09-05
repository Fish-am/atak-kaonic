package com.atakmap.android.plugintemplate;

import android.content.Context;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.atak.plugins.impl.PluginLayoutInflater;
import com.atakmap.android.dropdown.DropDown.OnStateListener;
import com.atakmap.android.dropdown.DropDownReceiver;
import com.atakmap.android.maps.MapView;
import com.atakmap.android.plugintemplate.plugin.R;
import com.atakmap.coremap.log.Log;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

public class PluginTemplateDropDownReceiver extends DropDownReceiver implements
        OnStateListener {

    public static final String TAG = PluginTemplateDropDownReceiver.class
            .getSimpleName();

    public static final String SHOW_PLUGIN = "com.atakmap.android.plugintemplate.SHOW_PLUGIN";

    // CoT multicast address and port — same as what the Kaonic bridge listens on
    private static final String COT_MULTICAST_ADDR = "239.2.3.1";
    private static final int COT_PORT = 6969;

    private final Context pluginContext;
    private final View rosterView;

    // Fake data model for a single drone/orb. No real telemetry -- cosmetic only.
    private static class FakeDrone {
        String callsign;
        String type;
        String battery;
        String altitude;
        String speed;
        String link;
        String position;
        boolean connected;

        FakeDrone(String callsign, String type, String battery, String altitude,
                  String speed, String link, String position, boolean connected) {
            this.callsign = callsign;
            this.type = type;
            this.battery = battery;
            this.altitude = altitude;
            this.speed = speed;
            this.link = link;
            this.position = position;
            this.connected = connected;
        }
    }

    private final List<FakeDrone> fakeDrones = new ArrayList<>();

    /**************************** CONSTRUCTOR *****************************/

    public PluginTemplateDropDownReceiver(final MapView mapView,
                                          final Context context) {
        super(mapView);
        this.pluginContext = context;

        // Hardcoded placeholder roster -- replace with real telemetry once
        // the Kaonic bridge integration is wired up.
        fakeDrones.add(new FakeDrone("ORB-01", "blank \u00b7 GPS-denied",
                "87%", "142 ft", "12.4 mph", "Strong",
                "37.4120\u00b0 N, -122.0110\u00b0 W", true));
        fakeDrones.add(new FakeDrone("ORB-02", "blank \u00b7 GPS-denied",
                "63%", "98 ft", "9.1 mph", "Strong",
                "37.4130\u00b0 N, -122.0120\u00b0 W", true));
        fakeDrones.add(new FakeDrone("ORB-03", "blank \u00b7 Recon",
                "21%", "0 ft", "0 mph", "No signal",
                "37.4140\u00b0 N, -122.0130\u00b0 W", false));

        rosterView = PluginLayoutInflater.inflate(context,
                R.layout.main_layout, null);
        buildRoster();
    }

    /**************************** PUBLIC METHODS *****************************/

    @Override
    public void disposeImpl() {
    }

    /**
     * Builds and sends a CoT command packet to the Kaonic bridge multicast address.
     * Runs on a background thread to avoid blocking the UI.
     *
     * @param targetUid  UID of the drone to command (must match atak_bridge.py UID)
     * @param command    Command string: ARM, DISARM, HOLD, RTL
     * @param value      Value string: "true"/"false" for ARM/DISARM, "" for HOLD/RTL
     */
    private void sendCommand(final String targetUid, final String command, final String value) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // Build timestamps
                    SimpleDateFormat fmt = new SimpleDateFormat(
                            "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US);
                    fmt.setTimeZone(TimeZone.getTimeZone("UTC"));
                    String now = fmt.format(new Date());
                    String stale = fmt.format(new Date(System.currentTimeMillis() + 10000));

                    // Build CoT command XML
                    String uid = "cmd-" + command + "-" + targetUid;
                    String cot =
                            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" +
                                    "<event version=\"2.0\" uid=\"" + uid + "\" " +
                                    "type=\"b-c-drone-cmd\" how=\"h-g\" " +
                                    "time=\"" + now + "\" start=\"" + now + "\" stale=\"" + stale + "\">" +
                                    "<point lat=\"0\" lon=\"0\" hae=\"0\" ce=\"0\" le=\"0\"/>" +
                                    "<detail>" +
                                    "<drone_command " +
                                    "target_uid=\"" + targetUid + "\" " +
                                    "command=\"" + command + "\" " +
                                    "value=\"" + value + "\"/>" +
                                    "</detail>" +
                                    "</event>";

                    // Send via UDP multicast
                    DatagramSocket socket = new DatagramSocket();
                    socket.setReuseAddress(true);
                    byte[] data = cot.getBytes("UTF-8");
                    InetAddress addr = InetAddress.getByName(COT_MULTICAST_ADDR);
                    DatagramPacket packet = new DatagramPacket(data, data.length, addr, COT_PORT);
                    socket.send(packet);
                    socket.close();

                    Log.d(TAG, "Sent command: " + command + " to " + targetUid);

                } catch (Exception e) {
                    Log.e(TAG, "Failed to send command: " + e.getMessage());
                }
            }
        }).start();
    }

    private void buildRoster() {
        LinearLayout container = rosterView.findViewById(R.id.droneListContainer);
        container.removeAllViews();

        LayoutInflater inflater = (LayoutInflater) pluginContext
                .getSystemService(Context.LAYOUT_INFLATER_SERVICE);

        for (final FakeDrone drone : fakeDrones) {
            View card = inflater.inflate(R.layout.drone_card_item, container, false);

            TextView callsignText = card.findViewById(R.id.droneCallsign);
            TextView typeText = card.findViewById(R.id.droneType);
            TextView batteryText = card.findViewById(R.id.droneBatteryGlance);
            View statusDot = card.findViewById(R.id.statusDot);

            callsignText.setText(drone.callsign);
            typeText.setText(drone.type);
            batteryText.setText(drone.battery);
            statusDot.setBackgroundColor(drone.connected
                    ? 0xFF39FF88
                    : 0xFF8B949E);

            card.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    showDetail(drone);
                }
            });

            container.addView(card);
        }
    }

    private void showDetail(final FakeDrone drone) {
        LayoutInflater inflater = (LayoutInflater) pluginContext
                .getSystemService(Context.LAYOUT_INFLATER_SERVICE);
        final View detailView = inflater.inflate(R.layout.drone_detail_layout, null);

        ((TextView) detailView.findViewById(R.id.detailCallsign)).setText(drone.callsign);
        ((TextView) detailView.findViewById(R.id.detailType)).setText(drone.type);
        ((TextView) detailView.findViewById(R.id.detailBattery)).setText(drone.battery);
        ((TextView) detailView.findViewById(R.id.detailAltitude)).setText(drone.altitude);
        ((TextView) detailView.findViewById(R.id.detailSpeed)).setText(drone.speed);
        ((TextView) detailView.findViewById(R.id.detailLink)).setText(drone.link);
        ((TextView) detailView.findViewById(R.id.detailPosition)).setText(drone.position);

        View statusDot = detailView.findViewById(R.id.detailStatusDot);
        statusDot.setBackgroundColor(drone.connected ? 0xFF39FF88 : 0xFF8B949E);

        // ARM button — sends ARM command to drone
        detailView.findViewById(R.id.armButton).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Log.d(TAG, "ARM tapped for " + drone.callsign);
                sendCommand("ROS2-HEXSOON450-1", "ARM", "true");
            }
        });

        // HOLD button — sends HOLD command to drone
        detailView.findViewById(R.id.holdButton).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Log.d(TAG, "HOLD tapped for " + drone.callsign);
                sendCommand("ROS2-HEXSOON450-1", "HOLD", "");
            }
        });

        // blank button — sends RTL command to drone
        detailView.findViewById(R.id.rtlButton).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Log.d(TAG, "DISARM tapped for " + drone.callsign);
                sendCommand("ROS2-HEXSOON450-1", "DISARM", "false");
            }
        });

        detailView.findViewById(R.id.backButton).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showDropDown(rosterView, HALF_WIDTH, FULL_HEIGHT, FULL_WIDTH,
                        HALF_HEIGHT, false, PluginTemplateDropDownReceiver.this);
            }
        });

        showDropDown(detailView, HALF_WIDTH, FULL_HEIGHT, FULL_WIDTH,
                HALF_HEIGHT, false, this);
    }

    /**************************** INHERITED METHODS *****************************/

    @Override
    public void onReceive(Context context, Intent intent) {

        final String action = intent.getAction();
        if (action == null)
            return;

        if (action.equals(SHOW_PLUGIN)) {
            Log.d(TAG, "showing plugin drop down");
            buildRoster();
            showDropDown(rosterView, HALF_WIDTH, FULL_HEIGHT, FULL_WIDTH,
                    HALF_HEIGHT, false, this);
        }
    }

    @Override
    public void onDropDownSelectionRemoved() {
    }

    @Override
    public void onDropDownVisible(boolean v) {
    }

    @Override
    public void onDropDownSizeChanged(double width, double height) {
    }

    @Override
    public void onDropDownClose() {
    }

}