"""Clean English 1.03 -> localized campaign in Documents/Warcraft III/Campaigns (no Editor resave needed)."""
import sys
sys.path.insert(0, r"C:\Users\UserM\Documents\GitHub\clever-play-ua.github.io\w3r-l10n-toolkit\python_tools")
from roa_build_1_03 import build_campaign  # noqa: E402

REPO = __file__.rsplit("scripts", 1)[0]

build_campaign('deDE', REPO, 'CSW_Rise_of_the_Alliance_1_03_DE_0_1.w3n', loading_screens={
})
