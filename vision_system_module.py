import time
import re
from pathlib import Path
import serial
import json

from vision_system.photo_transfer_module import PhotoTransferModule
from vision_system.vision_modules.bumblebee_cv import BumbleBeeCv


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


class VisionDriver:
    def __init__(self):
        """
            Vision system constructor. opens local vision data
        :return: VisionDriver object
        """
        # Path to movement module directory
        base_dir = Path(__file__).resolve().parent
        data_path = base_dir / "vision_data.json"

        # Open vision data dict
        self.vision_data = load_json(data_path)

        self.camera_system = PhotoTransferModule()
        self.cv_module = BumbleBeeCv()

    def emergency_stop(self):
        # Need to implement
        return True

    # ==========================================
    # photo transfer module related functions
    # ==========================================

    def vision_system_startup(self):
        """
        Starts the vision system for feeding (which involves warming up the camera)
        :return: true if the camera is onf/has been successfully turned on
        """
        return self.camera_system.turn_on()

    def vision_system_turn_off(self):
        """
        Turns off the vision system at the end of a feeding (which involves turning off the camera)
        :return: true if the camera is off/has been successfully shut off
        """
        return self.camera_system.turn_off()

    def take_photo(self, photo_path):
        """
        Takes a photo and save it in the designated path
        :return: true if picture taken successfully or false otherwise
        """
        return self.camera_system.take_photo(photo_path)

    # ==========================================
    # CV related functions
    # ==========================================

    def analyze_photo(self, photo_path):
        """
        Receives a path to the photo and returns the analyzed parameters
        :param photo_path: path of the photo to analyze
        :return: ((x,y offsets), larvae area mm^2, larvae height mm)
        """
        path = Path(photo_path)
        if not path.is_file():
            print(f"Error: Photo not found at {path}")
            return None

        try:
            return self.cv_module.analyze_photo(str(path))
        except (ValueError, TypeError, OSError) as e:
            print(f"Error analyzing photo at {path}: {e}")
            return None