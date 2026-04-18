import serial


class PhotoTransferModule:
    """
    This class controls the transfer of photos back to the computer. They will later be analyzed by the CV module
    """
    def __init__(self):
        """
        PhotoTransferModule constructor.
        :return: PhotoTransferModule object
        """
        # Probably need to read from json here (comport etc):



    def __del__(self):
        """
        PhotoTransferModule destructor. Stops system action and then closes port.
        may need to reset the rasberrypie
        :return: VOID
        """

    def take_photo(self, path):
        """
        Commands the rasberrypie to take a photo and store it at path
        :param path: amount of food to output (im micro-liters)
        :return: boolean true for success, false otherwise
        """

    def transfer_photo(self, rasberry_path, pc_path):
        """
        Transfers the photo back to the pc (used for cleaning). Will either use keypress to stop or a predefined amount
        :return: true when finished, false otherwise
        """

