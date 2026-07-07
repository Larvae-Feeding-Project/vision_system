import sys
from pathlib import Path

# Find the current folder (vision_utils) and the parent folder (vision_system)
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

# Add the parent folder to Python's searchable path
sys.path.append(str(parent_dir))

# Now we can safely import from the parent directory.
from vision_system.photo_transfer_module import PhotoTransferModule

# ==========================================
# EDIT THIS DIRECTORY TO TEST DIFFERENT LOCATIONS
# ==========================================
# Point this to the folder where you want the images saved
TEST_PHOTO_DIR = Path(r"C:\Users\nitai\PycharmProjects\Larvae Project\test_photos")
FILE_PREFIX = "test_capture_"

print("Initializing Vision System Test Utility...")
vision_system = PhotoTransferModule()

# Initialize the photo counter
photo_counter = 1

print("\n" + "=" * 40)
print("VISION SYSTEM TEST CLI")
print("Commands:")
print("  'on'          : Wakes up the camera")
print("  'off'         : Puts the camera to sleep")
print("  'snap' or 's' : Takes a photo and auto-increments the file number")
print("  'exit' or 'q' : Quits the utility")
print("=" * 40 + "\n")

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
            # Construct the dynamic path (e.g., test_capture_01.jpg, test_capture_02.jpg)
            filename = f"{FILE_PREFIX}{photo_counter:02d}.jpg"
            current_path = TEST_PHOTO_DIR / filename

            print(f"Testing photo capture for {filename}...")

            # Pass the constructed path as a string to the take_photo method
            success = vision_system.take_photo(str(current_path))

            if success:
                print(f"SUCCESS: Go check {current_path} to verify the image.")
                photo_counter += 1  # Increment the counter for the next photo
            else:
                print("FAILED: Photo capture returned False. Check the console for errors.")

        elif cmd == "":
            continue

        else:
            print("Unknown command. Type 'snap' to test the camera or 'exit' to quit.")

finally:
    # Trigger the destructor manually to ensure the camera hardware is released properly
    print("Cleaning up...")
    if hasattr(vision_system, '__del__'):
        vision_system.__del__()