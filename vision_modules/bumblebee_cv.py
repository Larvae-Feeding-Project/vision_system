import cv2
import numpy as np
from typing import Tuple, Optional, Union
from aris_cv_ac import ArisCvAc

class BumbleBeeCv(ArisCvAc):
    """
    OpenCV implementation for extracting bumblebee larva metrics from IR imagery
    using Glare-Halo Suppression and Croissant-Contour Pruning.
    """

    def __init__(
        self,
        lower_ir_thresh: int = 105,
        upper_ir_thresh: int = 248,
        roi_radius_px: int = 150,
        well_center_px: Optional[Tuple[int, int]] = (961, 538),
        glare_halo_pad_px: int = 10,
        croissant_smooth_px: int = 9,
        mm_per_pixel: float = 1.0,
        min_larva_area_px: int = 1200
    ):
        """
        :param lower_ir_thresh: Minimum intensity for larva body (set ~125-135 to ignore floor smudges).
        :param upper_ir_thresh: Cutoff intensity where specular LED glare starts (~220-235).
        :param roi_radius_px: Radius of the circular mask inside the target well rim.
        :param well_center_px: (x, y) center of the target well.
        :param glare_halo_pad_px: Pixels to expand around ultra-white glare spots to eat their blurry halos.
        :param croissant_smooth_px: Radius of the circular rolling-ball filter that forces a smooth croissant outline
                                    and shears off thin glare/smudge protrusions.
        :param mm_per_pixel: Calibration factor.
        :param min_larva_area_px: Minimum pixel area for a valid larva.
        """
        super().__init__()
        self.lower_ir_thresh = lower_ir_thresh
        self.upper_ir_thresh = upper_ir_thresh
        self.roi_radius_px = roi_radius_px
        self.well_center_px = well_center_px
        self.glare_halo_pad_px = glare_halo_pad_px
        self.croissant_smooth_px = croissant_smooth_px
        self.mm_per_pixel = mm_per_pixel
        self.min_larva_area_px = min_larva_area_px

    def _load_and_validate(self, image: Union[str, np.ndarray]) -> np.ndarray:
        if isinstance(image, str):
            img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"Could not load image from path: {image}")
            return img
        elif isinstance(image, np.ndarray):
            if len(image.shape) == 3:
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return image.copy()
        else:
            raise TypeError("Input must be a file path string or a numpy ndarray.")

    def _preprocess(self, gray_img: np.ndarray) -> np.ndarray:
        """
        Applies edge-preserving bilateral filtering (smooths out floor smudges while keeping
        the larva's curved boundary crisp) followed by mild unsharp masking.
        """
        bilateral = cv2.bilateralFilter(gray_img, d=7, sigmaColor=35, sigmaSpace=35)
        gaussian = cv2.GaussianBlur(bilateral, (0, 0), sigmaX=2.5)
        sharpened = cv2.addWeighted(bilateral, 1.4, gaussian, -0.4, 0)
        return sharpened

    def _enforce_croissant_outline(self, raw_larva_mask: np.ndarray) -> np.ndarray:
        """
        Enforces a smooth, organic 'croissant' contour by:
        1. Filling small internal holes inside the larva.
        2. Using Distance-Transform Core Pruning to sever any thin bridges/tails connected
           to glare halos or well-floor residue.
        3. Reconstructing the smooth curved outline via circular disk dilation & Fourier/Gaussian contour smoothing.
        """
        # 1. Fill internal pinholes first
        contours, _ = cv2.findContours(raw_larva_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return raw_larva_mask
        largest = max(contours, key=cv2.contourArea)
        solid = np.zeros_like(raw_larva_mask)
        cv2.drawContours(solid, [largest], -1, 255, thickness=-1)

        # 2. Rolling-ball opening (erosion -> keep main core -> dilation)
        # Any protrusion thinner than (2 * croissant_smooth_px) cannot be the larva body and gets amputated!
        r = max(1, int(self.croissant_smooth_px))
        disk_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        eroded_core = cv2.erode(solid, disk_kernel, iterations=1)

        # Keep only the primary larva core if erosion split off a stray smudge blob
        core_contours, _ = cv2.findContours(eroded_core, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if core_contours:
            main_core = max(core_contours, key=cv2.contourArea)
            clean_core = np.zeros_like(eroded_core)
            cv2.drawContours(clean_core, [main_core], -1, 255, thickness=-1)
            reconstructed = cv2.dilate(clean_core, disk_kernel, iterations=1)
        else:
            reconstructed = solid

        # 3. Smooth the boundary curve (removes jagged pixel stair-stepping, producing a true croissant curve)
        blur_k = max(3, (r | 1))  # Ensure odd kernel size
        smoothed_prob = cv2.GaussianBlur(reconstructed, (blur_k * 2 + 1, blur_k * 2 + 1), sigmaX=r * 0.6)
        _, croissant_mask = cv2.threshold(smoothed_prob, 127, 255, cv2.THRESH_BINARY)

        return croissant_mask

    def analyze_photo(
        self,
        image: Union[str, np.ndarray],
        return_debug: bool = False
    ) -> Union[Tuple[Tuple[float, float], float, float], Tuple[Tuple[float, float], float, float, np.ndarray]]:
        gray = self._load_and_validate(image)
        img_h, img_w = gray.shape[:2]

        ref_x, ref_y = self.well_center_px if self.well_center_px is not None else (img_w // 2, img_h // 2)

        # Step 1: Edge-preserving smoothing + sharpening
        proc = self._preprocess(gray)

        # Step 2: Circular ROI mask to isolate inside of the target well
        roi_mask = np.zeros_like(proc)
        cv2.circle(roi_mask, (ref_x, ref_y), self.roi_radius_px, 255, thickness=-1)

        # Step 3: GLARE HALO KILLER
        # Detect ultra-bright specular LED reflections (> upper_ir_thresh) and dilate them
        # so their blurry mid-grey skirts/halos are completely masked out!
        _, glare_cores = cv2.threshold(gray, self.upper_ir_thresh, 255, cv2.THRESH_BINARY)
        if self.glare_halo_pad_px > 0:
            halo_k = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (2 * self.glare_halo_pad_px + 1, 2 * self.glare_halo_pad_px + 1)
            )
            glare_with_halos = cv2.dilate(glare_cores, halo_k, iterations=1)
        else:
            glare_with_halos = glare_cores

        # Combine valid region: Inside ROI AND NOT inside a glare halo
        valid_zone_mask = cv2.bitwise_and(roi_mask, cv2.bitwise_not(glare_with_halos))

        # Step 4: Threshold the larva body within the valid zone
        _, larva_candidates = cv2.threshold(proc, self.lower_ir_thresh, 255, cv2.THRESH_BINARY)
        larva_candidates = cv2.bitwise_and(larva_candidates, valid_zone_mask)

        # Step 5: Pick the largest candidate blob near the well
        contours, _ = cv2.findContours(larva_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_contours = [c for c in contours if cv2.contourArea(c) >= self.min_larva_area_px]

        if not valid_contours:
            empty_res = ((0.0, 0.0), 0.0, 0.0)
            if return_debug:
                return (*empty_res, cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
            return empty_res

        raw_larva_contour = max(valid_contours, key=cv2.contourArea)
        raw_mask = np.zeros_like(gray)
        cv2.drawContours(raw_mask, [raw_larva_contour], -1, 255, thickness=-1)

        # Step 6: Enforce smooth Croissant Outline (shears off smudges & glare bridges)
        croissant_mask = self._enforce_croissant_outline(raw_mask)

        final_contours, _ = cv2.findContours(croissant_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not final_contours:
            empty_res = ((0.0, 0.0), 0.0, 0.0)
            if return_debug:
                return (*empty_res, cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
            return empty_res

        larva_contour = max(final_contours, key=cv2.contourArea)

        # --- METRIC 1: Larva Area ---
        area_px = float(cv2.countNonZero(croissant_mask))
        calibrated_area = area_px * (self.mm_per_pixel ** 2)

        # --- METRIC 2: (x, y) Offset from Well Center ---
        moments = cv2.moments(croissant_mask, binaryImage=True)
        if moments["m00"] != 0:
            cx = moments["m10"] / moments["m00"]
            cy = moments["m01"] / moments["m00"]
        else:
            cx, cy = float(ref_x), float(ref_y)

        dx = (cx - ref_x) * self.mm_per_pixel
        dy = (cy - ref_y) * self.mm_per_pixel

        # --- METRIC 3: Larva "Radius" / Fattest Cross-Section Width ---
        dist_transform = cv2.distanceTransform(croissant_mask, cv2.DIST_L2, 5)
        _, max_inscribed_radius_px, _, max_loc = cv2.minMaxLoc(dist_transform)

        fattest_width_px = 2.0 * max_inscribed_radius_px
        calibrated_height = fattest_width_px * self.mm_per_pixel

        if not return_debug:
            return (dx, dy), calibrated_area, calibrated_height

        # --- Debug Visualization ---
        debug_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # 1. Draw rejected Glare + Halo zones in subtle Red tint so you can see what was blocked
        glare_in_roi = cv2.bitwise_and(glare_with_halos, roi_mask)
        debug_img[glare_in_roi > 0] = (
            debug_img[glare_in_roi > 0] * 0.5 + np.array([0, 0, 180]) * 0.5
        ).astype(np.uint8)

        # 2. Draw target well ROI boundary (Blue)
        cv2.circle(debug_img, (ref_x, ref_y), self.roi_radius_px, (255, 100, 0), 2)
        cv2.drawMarker(debug_img, (ref_x, ref_y), (255, 100, 0), cv2.MARKER_CROSS, 15, 2)

        # 3. Draw smooth Croissant Contour (Green)
        cv2.drawContours(debug_img, [larva_contour], -1, (0, 255, 0), 2)

        # 4. Draw Center of Mass & Offset Vector (Yellow)
        cx_int, cy_int = int(round(cx)), int(round(cy))
        cv2.circle(debug_img, (cx_int, cy_int), 5, (0, 255, 255), -1)
        cv2.line(debug_img, (ref_x, ref_y), (cx_int, cy_int), (0, 255, 255), 2)

        # 5. Draw Fattest Cross-Section Circle (Cyan)
        cv2.circle(debug_img, max_loc, int(round(max_inscribed_radius_px)), (255, 255, 0), 2)
        cv2.circle(debug_img, max_loc, 3, (255, 255, 0), -1)

        return (dx, dy), calibrated_area, calibrated_height, debug_img