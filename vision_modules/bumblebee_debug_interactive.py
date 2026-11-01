import os
import glob
import cv2
from bumblebee_cv import BumbleBeeCv


def interactive_tuner(folder_path: str):
    valid_extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.JPG", "*.PNG")
    image_paths = sorted(list({
        os.path.abspath(p)
        for ext in valid_extensions
        for p in glob.glob(os.path.join(folder_path, ext))
    }))

    if not image_paths:
        print(f"[Error] No images found in directory: {os.path.abspath(folder_path)}")
        return

    num_images = len(image_paths)

    # Initialized
    cv_module = BumbleBeeCv(
        lower_ir_thresh=128,     # Higher lower-bound ignores floor smudges (which sit around 90-115)
        upper_ir_thresh=225,     # Keep upper-bound high so we don't hollow out the larva!
        roi_radius_px=150,
        well_center_px=(961, 538),
        glare_halo_pad_px=11,    # Expands >225 glare spots by 11px to eat their blurry halos
        croissant_smooth_px=13   # Rolling-ball radius to amputate thin tails and smooth the croissant
    )

    win_name = "ARIS Interactive Tuner"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 1280, 820)

    if num_images > 1:
        cv2.createTrackbar("Photo Idx", win_name, 0, num_images - 1, lambda x: None)

    cv2.createTrackbar("ROI Radius", win_name, cv_module.roi_radius_px, 400, lambda x: None)
    cv2.createTrackbar("Center X", win_name, cv_module.well_center_px[0], 1920, lambda x: None)
    cv2.createTrackbar("Center Y", win_name, cv_module.well_center_px[1], 1080, lambda x: None)
    cv2.createTrackbar("Lower IR", win_name, cv_module.lower_ir_thresh, 255, lambda x: None)
    cv2.createTrackbar("Upper IR", win_name, cv_module.upper_ir_thresh, 255, lambda x: None)
    cv2.createTrackbar("Halo Pad", win_name, cv_module.glare_halo_pad_px, 35, lambda x: None)
    cv2.createTrackbar("Smooth R", win_name, cv_module.croissant_smooth_px, 35, lambda x: None)

    current_idx = 0

    while True:
        if cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1:
            break

        if num_images > 1:
            current_idx = cv2.getTrackbarPos("Photo Idx", win_name)

        cv_module.roi_radius_px = max(10, cv2.getTrackbarPos("ROI Radius", win_name))
        cx = cv2.getTrackbarPos("Center X", win_name)
        cy = cv2.getTrackbarPos("Center Y", win_name)
        cv_module.well_center_px = (cx, cy)
        cv_module.lower_ir_thresh = cv2.getTrackbarPos("Lower IR", win_name)
        cv_module.upper_ir_thresh = max(
            cv_module.lower_ir_thresh + 5,
            cv2.getTrackbarPos("Upper IR", win_name)
        )
        cv_module.glare_halo_pad_px = cv2.getTrackbarPos("Halo Pad", win_name)
        cv_module.croissant_smooth_px = max(1, cv2.getTrackbarPos("Smooth R", win_name))

        img_path = image_paths[current_idx]
        (dx, dy), area, thickness, debug_frame = cv_module.analyze_photo(img_path, return_debug=True)

        header_text = (f"[{current_idx + 1}/{num_images}] {os.path.basename(img_path)} | "
                       f"ROI_R: {cv_module.roi_radius_px} | IR: [{cv_module.lower_ir_thresh}, {cv_module.upper_ir_thresh}] | "
                       f"HaloPad: {cv_module.glare_halo_pad_px} | SmoothR: {cv_module.croissant_smooth_px}")
        metrics_text = f"Offset: ({dx:.1f}, {dy:.1f}) px | Area: {area:.0f} px^2 | Width: {thickness:.1f} px"

        cv2.putText(debug_frame, header_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(debug_frame, metrics_text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

        cv2.imshow(win_name, debug_frame)

        key = cv2.waitKey(30) & 0xFF
        if key in (ord('q'), 27):
            break
        elif key in (ord('n'), ord('d'), ord(' ')) and num_images > 1:
            current_idx = (current_idx + 1) % num_images
            cv2.setTrackbarPos("Photo Idx", win_name, current_idx)
        elif key in (ord('p'), ord('a')) and num_images > 1:
            current_idx = (current_idx - 1) % num_images
            cv2.setTrackbarPos("Photo Idx", win_name, current_idx)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    interactive_tuner("C:\\Users\\nitai\\Desktop\\ARIS_DATA\\clay_dark_underblack_24_exp16\\feed_1")