import time
import json
from pathlib import Path
import cv2


def load_json(file_path):
    """
    Loads json files and returns them
    :param file_path: path to json file
    :return: data structure inside the json if success otherwise returns None
    """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse {file_path}. Invalid JSON.")
        return None


class PhotoTransferModule:
    """
    This class controls the native USB camera directly connected to the computer.
    It manages the hardware state per feeding cycle to balance speed and longevity.
    """

    def __init__(self):
        """
        PhotoTransferModule constructor. Loads config and initializes in Standby Mode.
        """

        base_dir = Path(__file__).resolve().parent
        config_path = base_dir / "vision_data.json"

        self.config_data = load_json(config_path)
        self.camera_index = self.config_data['CAMERA_INDEX']

        # Hardware state variables
        self.cap = None
        self.is_active = False

        print(f"Vision System: Initialized in Standby Mode (Camera index {self.camera_index}).")

    def __del__(self):
        """
        PhotoTransferModule destructor. Ensures the camera hardware is released on shutdown.
        """
        self.turn_off()

    def turn_on(self):
        """
        Wakes up the camera hardware, sets resolution, and warms up the sensor.
        Call this at the beginning of a feeding cycle.
        :return: boolean true for success, false otherwise
        """

        if self.is_active:
            print(">> Vision System: Camera is already ON. Ignoring command.")
            return True

        print(f">> Waking up camera {self.camera_index} for feeding cycle...")
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            print(f">> ERROR: Could not open camera. Is it plugged in or used by another app?")
            self.cap = None
            return False

        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        # Warm up the sensor and ISP (Auto-Exposure adjustment)
        print(">> Vision System: Warming up sensor...")
        time.sleep(1.5)

        for _ in range(5):
            self.cap.read()  # Flush dark/blurry startup frames

        self.is_active = True
        print(">> Vision System: Camera is ACTIVE and ready.")
        return True

    def turn_off(self):
        """
        Releases the camera hardware, turning off the sensor and IR LEDs.
        Call this at the end of a feeding cycle.
        """
        if not self.is_active:
            print(">> Vision System: Camera is already OFF. Ignoring command.")
            return

        print(">> Vision System: Releasing camera hardware...")
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        self.cap = None
        self.is_active = False
        print(">> Vision System: Camera is now OFF (Standby Mode).")

    def take_photo(self, path):
        """
        Takes a photo using the active USB camera and saves it directly to the path.
        :param path: The file path to save the image
        :return: boolean true for success, false otherwise
        """
        if not self.is_active or self.cap is None:
            print(">> ERROR: Cannot take photo. Camera is OFF. Call turn_on() first.")
            return False

        # Check if the destination directory exists
        dest_dir = Path(path).parent
        if not dest_dir.exists():
            print(f"<< ERROR: Destination folder '{dest_dir}' does not exist. Aborting save.")
            return False

        print(f">> Snapping photo and saving to: {path}")

        try:
            # Snap the actual photo
            ret, frame = self.cap.read()

            if ret:
                success = cv2.imwrite(str(path), frame)
                if success:
                    print(f"<< Photo successfully saved to {path}")
                    return True
                else:
                    print(f"<< ERROR: OpenCV failed to write file to {path}. Check folder permissions.")
                    return False
            else:
                print("<< ERROR: Failed to grab frame from camera. Hardware may have disconnected.")
                # Auto-recover state if hardware dropped
                self.turn_off()
                return False

        except Exception as e:
            print(f"<< ERROR: Exception while trying to save photo: {e}")
            return False