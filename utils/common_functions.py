import os, sys

def read_data(file_to_read, pos, bytes_to_read):
    with open(file_to_read, "rb") as opened_file:
        opened_file.seek(pos, 0)
        grabed_data = opened_file.read(bytes_to_read)
    return grabed_data

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

