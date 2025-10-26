#!/usr/bin/env python3
"""
Synchronous Wrapper Example - Shows how to use the SDK without asyncio
"""

import asyncio
import threading
import time
import sys
import os

# Add parent directory to path to import dremian_sim_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dremian_sim_sdk import DroneClient

class DroneSyncWrapper:
    """Synchronous wrapper around async DroneClient"""

    def __init__(self, server_url="ws://localhost:8080"):
        self.client = DroneClient(server_url)
        self.loop = None
        self.thread = None
        self._started = False

    def start(self):
        """Start async loop in background thread"""
        if self._started:
            return

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        time.sleep(0.1)  # Give thread time to start
        self._started = True

    def _run_loop(self):
        """Run asyncio event loop in thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, timeout=5):
        """Synchronous connect"""
        if not self._started:
            self.start()

        future = asyncio.run_coroutine_threadsafe(
            self.client.connect(), self.loop
        )
        return future.result(timeout=timeout)

    def disconnect(self, timeout=5):
        """Synchronous disconnect"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.disconnect(), self.loop
        )
        return future.result(timeout=timeout)

    def send_control(self, roll=0, pitch=0, yaw=0, throttle=0, timeout=1):
        """Synchronous control command"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.send_control(roll, pitch, yaw, throttle),
            self.loop
        )
        return future.result(timeout=timeout)

    def start_camera(self, width=640, height=480, rate=30, quality=0.8, timeout=5):
        """Synchronous camera start"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.start_camera(width=width, height=height, rate=rate, quality=quality),
            self.loop
        )
        return future.result(timeout=timeout)

    def stop_camera(self, timeout=5):
        """Synchronous camera stop"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.stop_camera(),
            self.loop
        )
        return future.result(timeout=timeout)

    def get_camera_parameters(self, timeout=5):
        """Synchronous get camera parameters"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.get_camera_parameters(),
            self.loop
        )
        return future.result(timeout=timeout)

    def set_state_callback(self, callback):
        """Set telemetry callback"""
        self.client.set_state_callback(callback)

    def set_frame_callback(self, callback):
        """Set frame callback"""
        self.client.camera.set_frame_callback(callback)

    def start_receiving(self):
        """Start receiving messages in background"""
        asyncio.run_coroutine_threadsafe(
            self.client.receive_messages(),
            self.loop
        )


def main():
    # Create synchronous drone client
    drone = DroneSyncWrapper()

    print("Connecting to Dremian Sim...")
    drone.connect()
    print("Connected!")

    # Set up telemetry callback
    def on_telemetry(state):
        print(f"Alt: {state.position['altitude']:.1f}m | "
              f"Roll: {state.orientation['roll']:.1f}° | "
              f"Pitch: {state.orientation['pitch']:.1f}°")

    drone.set_state_callback(on_telemetry)

    # Start receiving messages in background
    drone.start_receiving()

    try:
        # Use synchronous control - no await needed!
        print("Hovering...")
        drone.send_control(throttle=0.5)
        time.sleep(2)

        print("Moving forward...")
        drone.send_control(pitch=0.3, throttle=0.6)
        time.sleep(3)

        print("Moving right...")
        drone.send_control(roll=0.3, throttle=0.6)
        time.sleep(3)

        print("Stopping...")
        drone.send_control(throttle=0.5)
        time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        drone.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    main()
