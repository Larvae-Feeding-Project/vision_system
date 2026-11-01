import os
import glob
import cv2
from bumblebee_cv import BumbleBeeCv


def run_debug_on_path(folder_path: str, cv_module: BumbleBeeCv):
    """
    Receives a directory path, iterates over all images inside it,
    and displays the ARIS CV debug output.
    """
    valid_extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp")
    image_paths = []
    for ext in valid_extensions:
        image_paths.extend(glob.glob(os.path.join(folder_path, ext)))

    image_paths = sorted(image_paths)

    if not image_paths:
        print(f"No images found in directory: {folder_path}")
        return

    for img_path in image_paths:
        (dx, dy), area, thickness, debug_frame = cv_module.analyze_photo(img_path, return_debug=True)
        print(f"[{img_path}]")
        print(f"  -> Offset (dx, dy): ({dx:.1f} px, {dy:.1f} px)")
        print(f"  -> Larva Area:      {area:.0f} px^2")
        print(f"  -> Max Thickness:   {thickness:.1f} px\n")

        cv2.imshow("ARIS CV Debug", debug_frame)
        key = cv2.waitKey(0) & 0xFF
        if key in (ord('q'), 27):  # Press 'q' or ESC to exit early
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Path to the directory containing the larva images
    images_dir = "C:\\Users\\nitai\\Desktop\\ARIS_DATA\\clay_dark_underblack_aluminumv2_24_exp16\\feed_1"

    # Looking at your 1920x1080 sample photos, the central target well is located
    # roughly around (x=950, y=490) with a radius of ~220px.
    cv_module = BumbleBeeCv(
        lower_ir_thresh=65,
        upper_ir_thresh=230,
        roi_radius_px=200,
        well_center_px=(950, 490)  # Set to None if camera is centered directly over the well
    )

    run_debug_on_path(images_dir, cv_module)