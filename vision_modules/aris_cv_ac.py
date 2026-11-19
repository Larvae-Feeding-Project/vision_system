from abc import ABC, abstractmethod
from typing import Tuple


class ArisCvAc(ABC):
    """
    ArisCvAc defines the interface any CV model needs to implement to properly work with the ARIS system.
    """

    def __init__(self):
        pass

    def __del__(self):
        pass

    @abstractmethod
    def analyze_photo(self, image_path: str) -> Tuple[Tuple[float, float], float, float]:
        """
        Analyzes the image of a larva from a file path and returns the relevant parameters for the system.
        :param image_path: Path string to the larva image to be analyzed.
        :return: Returns a tuple with 3 parameters:
            - The first - tuple of x, y offset from the center of the well to the larva center
            - The second - Volume/area of the larva
            - The third - Larva height (in millimeters)
        """
        pass