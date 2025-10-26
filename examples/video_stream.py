#!/usr/bin/env python3
"""
Video Stream Example - Shows how to receive and display camera stream
"""

import asyncio
import sys
import os
import cv2

# Add parent directory to path to import dremian_sim_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dremian_sim_sdk import DroneClient

async def main():
    client = DroneClient("ws://localhost:8080")

    print("Connecting to Dremian Sim...")
    if not await client.connect():
        print("Failed to connect!")
        return

    print("Connected!")

    # Option 1: Use built-in display
    client.camera.enable_display(True)

    # Option 2: Custom frame processing
    def on_frame(frame):
        # Add custom processing here
        # For example, detect objects, add overlays, etc.
        cv2.putText(frame, f"Frame: {client.camera.frame_count}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    client.camera.set_frame_callback(on_frame)

    # Start camera with custom settings
    print("Starting camera stream...")
    await client.start_camera(
        width=640,
        height=480,
        rate=30,
        quality=0.8
    )

    print("Receiving video... Press Ctrl+C to stop")

    try:
        # Receive messages (includes video frames)
        await client.receive_messages()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await client.stop_camera()
        await client.disconnect()
        cv2.destroyAllWindows()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
