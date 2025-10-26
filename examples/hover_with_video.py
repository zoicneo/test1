#!/usr/bin/env python3
"""
Hover with Video Example - Maintains altitude using PID controller while showing video
"""

import asyncio
import sys
import os
import cv2
from simple_pid import PID

# Add parent directory to path to import dremian_sim_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dremian_sim_sdk import DroneClient, DroneState

# Target altitude in meters
TARGET_ALTITUDE = 50.0

async def main():
    client = DroneClient("ws://localhost:8080")

    # Create PID controller for altitude
    # PID(Kp, Ki, Kd, setpoint)
    # The PID will output throttle value directly (0 to 1)
    altitude_pid = PID(0.02, 0.001, 0.01, setpoint=TARGET_ALTITUDE)
    altitude_pid.output_limits = (0.0, 1.0)  # Throttle range

    # Set initial throttle to hover value
    altitude_pid.set_auto_mode(True, last_output=0.5)

    current_altitude = 0.0

    # Telemetry callback
    def on_state_update(state: DroneState):
        nonlocal current_altitude
        current_altitude = state.position['altitude']

        # Display telemetry on console
        print(f"\rAltitude: {current_altitude:.2f}m | "
              f"Target: {TARGET_ALTITUDE:.2f}m | "
              f"Error: {TARGET_ALTITUDE - current_altitude:+.2f}m",
              end='', flush=True)

    # Frame callback - add telemetry overlay to video
    def on_frame(frame):
        # Add text overlay with telemetry
        cv2.putText(frame, f"Altitude: {current_altitude:.2f}m",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Target: {TARGET_ALTITUDE:.2f}m",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Error: {TARGET_ALTITUDE - current_altitude:+.2f}m",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Draw crosshair
        h, w = frame.shape[:2]
        cv2.line(frame, (w//2 - 20, h//2), (w//2 + 20, h//2), (0, 255, 0), 2)
        cv2.line(frame, (w//2, h//2 - 20), (w//2, h//2 + 20), (0, 255, 0), 2)

    # Set callbacks
    client.set_state_callback(on_state_update)
    client.camera.set_frame_callback(on_frame)

    print("Connecting to Dremian Sim...")
    if not await client.connect():
        print("Failed to connect!")
        return

    print("Connected!")

    # Reset drone position and orientation (Moscow, Russia)
    print("Resetting drone position...")
    await client.send_position({
        "position": {
            "latitude": 55.7558,
            "longitude": 37.6173,
            "altitude": 0
        },
        "orientation": {
            "roll": 0,
            "pitch": 0,
            "yaw": 0
        }
    })
    await asyncio.sleep(0.5)  # Wait for reset

    # Enable video display
    client.camera.enable_display(True)

    # Start camera
    print("Starting camera...")
    await client.start_camera(width=640, height=480, rate=30)

    print(f"\nHovering at {TARGET_ALTITUDE}m altitude...")
    print("Press Ctrl+C to stop\n")

    try:
        # Create tasks for receiving messages and PID control
        async def control_loop():
            while True:
                # Calculate throttle from PID based on current altitude
                # PID will increase throttle if below target, decrease if above
                throttle = altitude_pid(current_altitude)

                # Send control command (hover position, maintain altitude)
                await client.send_control(
                    roll=0.0,
                    pitch=0.0,
                    yaw=0.0,
                    throttle=throttle
                )

                await asyncio.sleep(0.05)  # 20 Hz control rate

        # Run both tasks concurrently
        await asyncio.gather(
            client.receive_messages(),
            control_loop()
        )

    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        await client.stop_camera()
        await client.disconnect()
        cv2.destroyAllWindows()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
