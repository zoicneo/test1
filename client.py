#!/usr/bin/env python3
"""
Dremian Sim Client Library - Provides interface for controlling and receiving data from the Dremian Sim drone simulator
"""

import json
import time
import asyncio
import websockets
import base64
import cv2
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, Callable
import io
from PIL import Image

class DroneState:
    """Class to hold drone state information"""
    def __init__(self):
        self.position: Dict[str, float] = {'latitude': 0, 'longitude': 0, 'altitude': 0}
        self.orientation: Dict[str, float] = {'roll': 0, 'pitch': 0, 'yaw': 0}
        self.velocity: Dict[str, float] = {'vx': 0, 'vy': 0, 'vz': 0}
        self.rotation_rates: Dict[str, float] = {'rollRate': 0, 'pitchRate': 0, 'yawRate': 0}
        self.timestamp: int = 0

    def update(self, telemetry_data: Dict[str, Any]) -> None:
        """Update state from telemetry data"""
        self.position = telemetry_data.get('position', self.position)
        self.orientation = telemetry_data.get('orientation', self.orientation)
        self.velocity = telemetry_data.get('velocity', self.velocity)
        self.rotation_rates = telemetry_data.get('rotationRates', self.rotation_rates)
        self.timestamp = telemetry_data.get('timestamp', int(time.time() * 1000))

class DroneCamera:
    """Class to handle drone camera operations"""
    def __init__(self):
        self.frame_count: int = 0
        self.latest_frame: Optional[np.ndarray] = None
        self.window_name: str = "Dremian Sim Camera Feed"
        self.show_display: bool = False
        self.frame_callback: Optional[Callable[[np.ndarray], None]] = None

    def process_frame(self, frame_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Process camera frame data and return numpy array"""
        try:
            base64_data = frame_data.get('data', '')
            if not base64_data:
                return None

            # Add padding if needed
            padding_needed = len(base64_data) % 4
            if padding_needed:
                base64_data += '=' * (4 - padding_needed)

            # Decode base64 data
            image_bytes = base64.b64decode(base64_data)

            # Try OpenCV first
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                # Fallback to PIL
                pil_img = Image.open(io.BytesIO(image_bytes))
                img = np.array(pil_img)
                if img.shape[2] == 3:  # If RGB, convert to BGR
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            if img is not None:
                self.latest_frame = img
                self.frame_count += 1

                # Call frame callback if set
                if self.frame_callback:
                    self.frame_callback(img)

                # Show display if enabled
                if self.show_display:
                    cv2.imshow(self.window_name, img)
                    cv2.waitKey(1)

            return img

        except Exception as e:
            print(f"Error processing frame: {e}")
            return None

    def set_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Set callback function to be called when new frame arrives"""
        self.frame_callback = callback

    def enable_display(self, enable: bool = True) -> None:
        """Enable or disable video display window"""
        self.show_display = enable
        if enable:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 640, 480)
        else:
            cv2.destroyWindow(self.window_name)

class DroneClient:
    """Main drone client class for controlling and receiving data from Dremian Sim"""
    def __init__(self, server_url: str = "ws://localhost:8080"):
        self.server_url: str = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected: bool = False
        self.running: bool = True
        self._camera_params_future: Optional[asyncio.Future] = None

        # Initialize components
        self.state = DroneState()
        self.camera = DroneCamera()

        # Callbacks
        self.on_state_changed: Optional[Callable[[DroneState], None]] = None

    async def connect(self) -> bool:
        """Connect to the Dremian Sim API websocket server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Dremian Sim"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.connected = False
        self.camera.enable_display(False)

    async def start_camera(self, rate: int = 60, quality: float = 0.8,
                          width: int = 640, height: int = 480) -> bool:
        """Start the camera stream"""
        if not self.connected:
            return False

        try:
            message = {
                "type": "camera_stream",
                "data": {
                    "active": True,
                    "rate": rate,
                    "quality": quality,
                    "width": width,
                    "height": height
                }
            }
            await self.send_message(message)
            return True
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False

    async def stop_camera(self) -> bool:
        """Stop the camera stream"""
        if not self.connected:
            return False

        try:
            message = {
                "type": "camera_stream",
                "data": {"active": False}
            }
            await self.send_message(message)
            return True
        except Exception as e:
            print(f"Error stopping camera: {e}")
            return False

    async def send_control(self, roll: float = 0, pitch: float = 0,
                          yaw: float = 0, throttle: float = 0) -> bool:
        """Send control commands to the drone

        Args:
            roll: Roll control (-1.0 to 1.0)
            pitch: Pitch control (-1.0 to 1.0)
            yaw: Yaw control (-1.0 to 1.0)
            throttle: Throttle control (-1.0 to 1.0)
        """
        if not self.connected:
            return False

        try:
            message = {
                "type": "control",
                "data": {
                    "roll": max(-1, min(1, roll)),
                    "pitch": max(-1, min(1, pitch)),
                    "yaw": max(-1, min(1, yaw)),
                    "throttle": max(-1, min(1, throttle))
                }
            }
            await self.send_message(message)
            return True
        except Exception as e:
            print(f"Error sending control: {e}")
            return False

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message to Dremian Sim"""
        if not self.connected:
            return False

        try:
            message["sender"] = "client"
            message["timestamp"] = int(time.time() * 1000)
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            self.connected = False
            return False

    def set_state_callback(self, callback: Callable[[DroneState], None]) -> None:
        """Set callback for state changes"""
        self.on_state_changed = callback

    async def receive_messages(self) -> None:
        """Main message receiving loop"""
        if not self.connected:
            return

        try:
            while self.running and self.connected:
                message = await self.websocket.recv()
                data = json.loads(message)

                if data["type"] == "telemetry":
                    self.state.update(data["data"])
                    if self.on_state_changed:
                        self.on_state_changed(self.state)

                elif data["type"] == "camera_frame":
                    self.camera.process_frame(data["data"])

                elif data["type"] == "camera_parameters" and self._camera_params_future:
                    # Set the result for the waiting future
                    self._camera_params_future.set_result(data)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            self.connected = False
        except Exception as e:
            print(f"Error receiving messages: {e}")
            self.connected = False

    async def send_position(self, position_data: Dict[str, Any]) -> None:
        """Set the drone's position and orientation directly.

        Args:
            position_data: Dictionary containing position data:
                {
                    "position": {
                        "longitude": float,
                        "latitude": float,
                        "altitude": float  # Optional, will be handled by terrain height
                    },
                    "orientation": {
                        "roll": float,   # Roll angle in degrees
                        "pitch": float,  # Pitch angle in degrees
                        "yaw": float     # Heading in degrees (0=North, 90=East)
                    }
                }
        """
        if not self.websocket:
            raise ConnectionError("Not connected to server")

        pos = position_data.get("position", {})
        orient = position_data.get("orientation", {})

        message = {
            "type": "command",
            "data": {
                "command": "setPosition",
                "params": {
                    "longitude": pos.get("longitude", 0),
                    "latitude": pos.get("latitude", 0),
                    "roll": orient.get("roll", 0),
                    "pitch": orient.get("pitch", 0),
                    "yaw": orient.get("yaw", 0)
                }
            }
        }

        await self.send_message(message)

    async def get_camera_parameters(self) -> Dict[str, Any]:
        """Get camera parameters (camera matrix, distortion coefficients, frame dimensions) from the simulator"""

        if not self.websocket:
            raise ConnectionError("Not connected to server")

        # Create a future to receive the response
        response_future = asyncio.Future()

        # Store the future in a temporary variable
        self._camera_params_future = response_future

        # Send request for camera parameters
        await self.send_message({
            "type": "get_camera_parameters"
        })

        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout=3.0)

            # Convert nested arrays to numpy arrays for camera matrix
            camera_matrix = np.array(response["camera_matrix"], dtype=np.float32)
            dist_coeffs = np.array(response["dist_coeffs"], dtype=np.float32)

            return {
                "camera_matrix": camera_matrix,
                "dist_coeffs": dist_coeffs,
                "frame_width": response["frame_width"],
                "frame_height": response["frame_height"]
            }
        finally:
            # Clean up the future
            self._camera_params_future = None

async def main():
    """Example usage of the DroneClient"""
    # Create client instance
    client = DroneClient()

    # Define callbacks
    def on_state_update(state: DroneState):
        print(f"Position: {state.position}")

    def on_frame(frame: np.ndarray):
        # Process frame as needed
        pass

    # Set up callbacks
    client.set_state_callback(on_state_update)
    client.camera.set_frame_callback(on_frame)

    # Connect and start services
    if await client.connect():
        client.camera.enable_display(True)
        await client.start_camera()

        try:
            # Start message receiving loop
            await client.receive_messages()
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
