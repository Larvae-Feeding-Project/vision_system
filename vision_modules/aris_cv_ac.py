

class ArisCvAc(object):
"""
    ArisCvAc class defines the interface any CV model needs to implement to properly work with the ARIS system
"""

def __init__(self):
    pass

def __del__(self):
    pass

def analyze_photo(self, image):
    """
    This method analyzes the image of a larvae and return the relevant parameters for the system
    :param self:
    :param image: Image of the larvae to be analyzed (may change to path instead)
    :return: Returns a tuple with 3 parameters:
    - The first - tuple of x,y offset from the center of the well to the larva center
    - The second - Volume of the larvae (millimeters ^ 3?)
    - The third -  Larvae height (in millimeters)
    """
