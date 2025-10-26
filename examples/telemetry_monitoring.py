#!/usr/bin/env python3
"""
Telemetry Monitoring Example - Shows how to receive and display telemetry data
"""

import asyncio
import sys
import os

# Add parent directory to path to import dremian_sim_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dremian_sim_sdk import DroneClient, DroneState

async def main():
    client = DroneClient("ws://localhost:8080")

    # Define telemetry callback
    def on_state_update(state: DroneState):
        print("\n" + "="*50)
        print(f"Timestamp: {state.timestamp}")
        print(f"Position:")
        print(f"  Latitude:  {state.position['latitude']:.6f}°")
        print(f"  Longitude: {state.position['longitude']:.6f}°")
        print(f"  Altitude:  {state.position['altitude']:.2f}m")
        print(f"Orientation:")
        print(f"  Roll:  {state.orientation['roll']:.2f}°")
        print(f"  Pitch: {state.orientation['pitch']:.2f}°")
        print(f"  Yaw:   {state.orientation['yaw']:.2f}°")
        print(f"Velocity:")
        print(f"  Vx: {state.velocity['vx']:.2f} m/s")
        print(f"  Vy: {state.velocity['vy']:.2f} m/s")
        print(f"  Vz: {state.velocity['vz']:.2f} m/s")

    # Set callback
    client.set_state_callback(on_state_update)

    print("Connecting to Dremian Sim...")
    if not await client.connect():
        print("Failed to connect!")
        return

    print("Connected! Monitoring telemetry... Press Ctrl+C to stop\n")

    try:
        # Receive messages (triggers telemetry callbacks)
        await client.receive_messages()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await client.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
