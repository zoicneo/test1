"""
Dremian Sim SDK - Python SDK for controlling and interacting with Dremian Sim drone simulator

This SDK provides a simple interface to:
- Connect to Dremian Sim via WebSocket
- Send control commands (roll, pitch, yaw, throttle)
- Receive telemetry data (position, orientation, velocity)
- Access camera stream and process frames
- Get camera calibration parameters

Example usage:
    import asyncio
    from dremian_sim_sdk import DroneClient

    async def main():
        # Create and connect client
        client = DroneClient("ws://localhost:8080")
        await client.connect()

        # Start camera
        await client.start_camera()

        # Send control commands
        await client.send_control(roll=0.5, pitch=0.2, yaw=0, throttle=0.6)

        # Receive messages
        await client.receive_messages()

        await client.disconnect()

    if __name__ == "__main__":
        asyncio.run(main())
"""

__version__ = "1.0.0"
__author__ = "Dremian Sim Team"

from .client import DroneClient, DroneState, DroneCamera
from .proxy import WebSocketProxy

__all__ = [
    "DroneClient",
    "DroneState",
    "DroneCamera",
    "WebSocketProxy"
]
