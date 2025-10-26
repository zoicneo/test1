#!/usr/bin/env python3
"""
Basic Control Example - Shows how to connect and send control commands
"""

import asyncio
import sys
import os

# Add parent directory to path to import dremian_sim_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dremian_sim_sdk import DroneClient

async def main():
    # Create client and connect
    client = DroneClient("ws://localhost:8080")

    print("Connecting to Dremian Sim...")
    if not await client.connect():
        print("Failed to connect!")
        return

    print("Connected successfully!")

    try:
        # Hover in place
        print("Hovering...")
        await client.send_control(roll=0, pitch=0, yaw=0, throttle=0.5)
        await asyncio.sleep(2)

        # Move forward
        print("Moving forward...")
        await client.send_control(roll=0, pitch=0.3, yaw=0, throttle=0.6)
        await asyncio.sleep(3)

        # Move right
        print("Moving right...")
        await client.send_control(roll=0.3, pitch=0, yaw=0, throttle=0.6)
        await asyncio.sleep(3)

        # Rotate
        print("Rotating...")
        await client.send_control(roll=0, pitch=0, yaw=0.5, throttle=0.5)
        await asyncio.sleep(2)

        # Stop
        print("Stopping...")
        await client.send_control(roll=0, pitch=0, yaw=0, throttle=0.5)
        await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await client.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
