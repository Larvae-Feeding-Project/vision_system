import sys
from pathlib import Path

# Path building
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from vision_system.photo_transfer_module import PhotoTransferModule

# ==========================================
# EDIT THIS DIRECTORY TO TEST DIFFERENT LOCATIONS
# ==========================================
TEST_PHOTO_DIR = Path(r"C:\Users\nitai\PycharmProjects\Larvae Project\test_photos")
FILE_PREFIX = "new_test_capture_"

print("Initializing Vision System Test Utility...")
vision_system = PhotoTransferModule()

# Initialize the photo counter
photo_counter = 1

print("\n" + "=" * 50)
print("VISION SYSTEM TEST CLI")
print("Commands:")
print("  'on'          : Wakes up the camera")
print("  'off'         : Puts the camera to sleep")
print("  'snap' or 's' : Takes a photo and auto-increments the file number")
print("  'exp <num>'   : Set manual exposure (e.g., 'exp -4' or 'exp -8')")
print("  'exit' or 'q' : Quits the utility")
print("=" * 50 + "\n")

try:
    while True:
        cmd = input(">> ").strip().lower()

        if cmd in ("exit", "quit", "q"):
            print("Exiting test utility.")
            break

        elif cmd in ("on", "turn on"):
            vision_system.turn_on()

        elif cmd in ("off", "turn off"):
            vision_system.turn_off()

        elif cmd in ("snap", "s", "take photo"):
            filename = f"{FILE_PREFIX}{photo_counter:02d}.jpg"
            current_path = TEST_PHOTO_DIR / filename

            print(f"Testing photo capture for {filename}...")

            success = vision_system.take_photo(str(current_path))

            if success:
                print(f"SUCCESS: Go check {current_path} to verify the image.")
                photo_counter += 1
            else:
                print("FAILED: Photo capture returned False. Check the console for errors.")

        elif cmd.startswith("exp "):
            try:
                # Parse the number after "exp "
                exp_val = int(cmd.split(" ")[1])
                vision_system.set_exposure(exp_val)
                print(f"Tip: Take a new photo ('s') to see the effect of exposure {exp_val}.")
            except ValueError:
                print("Invalid exposure value. Please provide an integer (e.g., 'exp -6').")

        elif cmd == "":
            continue

        else:
            print("Unknown command. Type 'snap', 'exp -6', 'on', 'off', or 'exit'.")

finally:
    # Close camera module
    print("Cleaning up...")
    if hasattr(vision_system, '__del__'):
        vision_system.__del__()