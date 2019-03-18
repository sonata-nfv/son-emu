import os
import sys


def get_absolute_path(absolute_or_relative_to_main_path):
    if os.path.isabs(absolute_or_relative_to_main_path):
        return absolute_or_relative_to_main_path
    return os.path.join(sys.path[0], absolute_or_relative_to_main_path)
