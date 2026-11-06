"""
Builds the German campaign from the clean English 1.03 release, with no
World Editor resave needed: every map gets its war3map.wts swapped, then the
maps + war3campaign.wts go back into the campaign via mpq_rebuild (which
writes the archive exactly like an Editor save, embedded maps stored raw).
"""

import sys
from pathlib import Path

TOOLKIT_MPQ = Path(r"C:\Users\UserM\Documents\GitHub\clever-play-ua.github.io\w3r-l10n-toolkit\ToD database")
sys.path.insert(0, str(TOOLKIT_MPQ))
from mpq_rebuild import MpqArchive, rebuild_archive  # noqa: E402

SOURCE = Path(r"F:\ЗАГРУЗКИ\CSW_Rise_of_the_Alliance_1_03.w3n")
OUTPUT = Path(r"C:\Users\UserM\Documents\Warcraft III\Campaigns\CSW_Rise_of_the_Alliance_1_03_DE_0_1.w3n")
WTS_DIR = Path(__file__).resolve().parent.parent / "WTS_1_03" / "deDE"
WORK = Path(__file__).resolve().parent.parent / "_build_tmp"

MAPS = {
    "WC2HumanAct1.w3x": "RoA_A01_CNMC1_deDE_1_03.wts",
    "WC2Human01.w3x": "RoA_A01_M01_deDE_1_03.wts",
    "WC2Human02.w3x": "RoA_A01_M02_deDE_1_03.wts",
    "WC2Human03.w3x": "RoA_A01_M03_deDE_1_03.wts",
    "WC2Human04.w3x": "RoA_A01_M04_deDE_1_03.wts",
}


def main():
    WORK.mkdir(exist_ok=True)
    replacements = {"war3campaign.wts": (WTS_DIR / "RoA_GLOBAL_deDE_1_03.wts").read_bytes()}
    with MpqArchive(SOURCE) as campaign:
        for map_name, wts_name in MAPS.items():
            src_map = WORK / map_name
            src_map.write_bytes(campaign.read(map_name))
            out_map = WORK / ("de_" + map_name)
            rebuild_archive(src_map, out_map, {"war3map.wts": (WTS_DIR / wts_name).read_bytes()})
            replacements[map_name] = out_map.read_bytes()
            print(f"  {map_name} <- {wts_name}")
    rebuild_archive(SOURCE, OUTPUT, replacements)
    for f in WORK.iterdir():
        f.unlink()
    WORK.rmdir()
    print(f"saved {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
