# Dremian Sim SDK

Python SDK for controlling and interacting with Dremian Sim drone simulator.

## Features

- 🎮 **Control Commands**: Send roll, pitch, yaw, and throttle commands
- 📡 **Telemetry Data**: Receive real-time position, orientation, and velocity data
- 📹 **Camera Stream**: Access live video feed from the drone
- 📐 **Camera Parameters**: Get camera calibration matrix and distortion coefficients
- 🔄 **Both Async & Sync**: Use with asyncio or threading

## Installation

1. Copy the `dremian_sim_sdk` folder into your project
2. Install dependencies:

```bash
cd dremian_sim_sdk
pip install -r requirements.txt
```

## Running Examples

Run examples from the parent directory using `PYTHONPATH`:

```bash
# From the directory containing dremian_sim_sdk/
PYTHONPATH=. python3 dremian_sim_sdk/examples/hover_with_video.py
PYTHONPATH=. python3 dremian_sim_sdk/examples/basic_control.py
PYTHONPATH=. python3 dremian_sim_sdk/examples/telemetry_monitoring.py
```

## Quick Start

### Async Usage (Recommended)

```python
import asyncio
from dremian_sim_sdk import DroneClient

async def main():
    # Create client
    client = DroneClient("ws://localhost:8080")

    # Connect to simulator
    if await client.connect():
        print("Connected to Dremian Sim!")

        # Start camera stream
        await client.start_camera(width=640, height=480, rate=30)

        # Send control commands
        await client.send_control(
            roll=0.0,
            pitch=0.2,
            yaw=0.0,
            throttle=0.6
        )

        # Receive messages in background
        await client.receive_messages()

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Sync Usage (Threading)

```python
import asyncio
import threading
from dremian_sim_sdk import DroneClient

class DroneSyncWrapper:
    def __init__(self, server_url="ws://localhost:8080"):
        self.client = DroneClient(server_url)
        self.loop = None
        self.thread = None

    def start(self):
        """Start async loop in background thread"""
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        """Run asyncio event loop in thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self):
        """Synchronous connect"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.connect(), self.loop
        )
        return future.result(timeout=5)

    def send_control(self, roll=0, pitch=0, yaw=0, throttle=0):
        """Synchronous control command"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.send_control(roll, pitch, yaw, throttle),
            self.loop
        )
        return future.result(timeout=1)

    def start_camera(self, width=640, height=480, rate=30):
        """Synchronous camera start"""
        future = asyncio.run_coroutine_threadsafe(
            self.client.start_camera(width=width, height=height, rate=rate),
            self.loop
        )
        return future.result(timeout=5)

# Usage
drone = DroneSyncWrapper()
drone.start()
drone.connect()
drone.start_camera()

# Send controls
drone.send_control(roll=0.5, pitch=0.2, throttle=0.6)
```

## Complete Examples

### 1. Basic Control

```python
import asyncio
from dremian_sim_sdk import DroneClient

async def fly_forward():
    client = DroneClient("ws://localhost:8080")
    await client.connect()

    # Fly forward for 3 seconds
    await client.send_control(pitch=0.5, throttle=0.7)
    await asyncio.sleep(3)

    # Stop
    await client.send_control(pitch=0, throttle=0.5)
    await client.disconnect()

asyncio.run(fly_forward())
```

### 2. Telemetry Callback

```python
import asyncio
from dremian_sim_sdk import DroneClient

async def monitor_telemetry():
    client = DroneClient("ws://localhost:8080")

    # Define callback for telemetry updates
    def on_state_change(state):
        print(f"Position: {state.position}")
        print(f"Orientation: {state.orientation}")
        print(f"Velocity: {state.velocity}")

    client.set_state_callback(on_state_change)

    await client.connect()
    await client.receive_messages()  # Will call callback on updates

asyncio.run(monitor_telemetry())
```

### 3. Camera Stream Processing

```python
import asyncio
import cv2
from dremian_sim_sdk import DroneClient

async def process_video():
    client = DroneClient("ws://localhost:8080")

    # Define frame processing callback
    def on_frame(frame):
        # Process frame (OpenCV numpy array)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Processed", gray)
        cv2.waitKey(1)

    client.camera.set_frame_callback(on_frame)

    await client.connect()
    await client.start_camera(width=640, height=480, rate=30)

    # Or enable built-in display
    # client.camera.enable_display(True)

    await client.receive_messages()

asyncio.run(process_video())
```

### 4. Get Camera Parameters

```python
import asyncio
from dremian_sim_sdk import DroneClient

async def get_calibration():
    client = DroneClient("ws://localhost:8080")
    await client.connect()

    # Get camera parameters
    params = await client.get_camera_parameters()

    print("Camera Matrix:")
    print(params["camera_matrix"])
    print("\nDistortion Coefficients:")
    print(params["dist_coeffs"])
    print(f"\nFrame Size: {params['frame_width']}x{params['frame_height']}")

    await client.disconnect()

asyncio.run(get_calibration())
```

### 5. Set Drone Position

```python
import asyncio
from dremian_sim_sdk import DroneClient

async def teleport_drone():
    client = DroneClient("ws://localhost:8080")
    await client.connect()

    # Set drone position and orientation
    await client.send_position({
        "position": {
            "latitude": 50.4501,
            "longitude": 30.5234,
            "altitude": 100  # meters
        },
        "orientation": {
            "roll": 0,
            "pitch": 0,
            "yaw": 90  # heading East
        }
    })

    await client.disconnect()

asyncio.run(teleport_drone())
```

## Running the WebSocket Proxy

The SDK includes a WebSocket proxy server that bridges browser and client:

```bash
# Start the proxy server
python -m dremian_sim_sdk.proxy --host localhost --port 8080

# Or with custom settings
python -m dremian_sim_sdk.proxy --host 0.0.0.0 --port 9000 --log-level DEBUG
```

## API Reference

### DroneClient

Main client class for interacting with Dremian Sim.

#### Methods

- `connect()` → `bool`: Connect to simulator
- `disconnect()`: Disconnect from simulator
- `send_control(roll, pitch, yaw, throttle)` → `bool`: Send control commands
- `start_camera(rate, quality, width, height)` → `bool`: Start camera stream
- `stop_camera()` → `bool`: Stop camera stream
- `get_camera_parameters()` → `dict`: Get camera calibration data
- `send_position(position_data)`: Teleport drone to position
- `set_state_callback(callback)`: Set telemetry callback
- `receive_messages()`: Main message receiving loop

### DroneState

Holds current drone state.

#### Properties

- `position`: `{latitude, longitude, altitude}`
- `orientation`: `{roll, pitch, yaw}`
- `velocity`: `{vx, vy, vz}`
- `rotation_rates`: `{rollRate, pitchRate, yawRate}`
- `timestamp`: Unix timestamp in milliseconds

### DroneCamera

Handles camera operations.

#### Methods

- `set_frame_callback(callback)`: Set callback for new frames
- `enable_display(enable)`: Show/hide OpenCV window

#### Properties

- `latest_frame`: Most recent frame as numpy array
- `frame_count`: Total frames received

## Architecture

```
┌─────────────┐      WebSocket      ┌─────────────┐      WebSocket      ┌──────────────┐
│   Browser   │ ←──────────────────→ │    Proxy    │ ←──────────────────→ │ Your Client  │
│ (Dremian)   │                      │   Server    │                      │   (Python)   │
└─────────────┘                      └─────────────┘                      └──────────────┘
```

1. Browser runs Dremian Sim and connects to proxy
2. Proxy forwards messages between browser and clients
3. Multiple clients can connect simultaneously

## Requirements

- Python 3.7+
- websockets
- opencv-python
- numpy
- Pillow

## License

MIT License
