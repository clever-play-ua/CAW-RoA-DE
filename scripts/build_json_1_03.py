"""Builds WTS_1_03/deDE + json_1_03 via the shared toolkit build (python_tools/roa_build_1_03.py)."""
import sys
sys.path.insert(0, r"C:\Users\UserM\Documents\GitHub\clever-play-ua.github.io\w3r-l10n-toolkit\python_tools")
from roa_build_1_03 import build_wts_json  # noqa: E402

REPO = __file__.rsplit("scripts", 1)[0]

build_wts_json('deDE', REPO, csv_column=None,
               title=None,
               description_suffix=None)
