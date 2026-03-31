import os
import sys

# ensure project root is on python path so that 'core', 'models' can be imported
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# additional package initialization can go here
