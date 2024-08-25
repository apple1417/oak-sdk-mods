# ruff: noqa: D103

if True:
    assert __import__("mods_base").__version_info__ >= (1, 4), "Please update the SDK"
    assert __import__("pyunrealsdk").__version_info__ >= (1, 3, 0), "Please update the SDK"
    assert __import__("unrealsdk").__version_info__ >= (1, 3, 0), "Please update the SDK"
    assert __import__("ui_utils").__version_info__ >= (1, 0), "Please update the SDK"

    from mods_base import Game

    assert Game.get_current() == Game.BL3, "The Hunt Tracker only works in BL3"

    assert __import__("bl3_mod_menu").__version_info__ >= (1, 0), "Please update the SDK"

from mods_base import SETTINGS_DIR, build_mod

from .mod_class import HuntTracker, coop_options
from .osd import osd_option
from .sqs import sq_hook
from .tokens import (
    item_inspect_end_hook,
    item_inspect_start_hook,
    mission_complete_hook,
    redeem_token_option,
)

# isort: split
# Import for side effects
from . import db, drops  # noqa: F401 # noqa: F401  # pyright: ignore[reportUnusedImport]

__version__: str
__version_info__: tuple[int, ...]

mod = build_mod(
    cls=HuntTracker,
    settings_file=SETTINGS_DIR / "hunt" / "hunt.json",
    hooks=[
        mission_complete_hook,
        item_inspect_end_hook,
        item_inspect_start_hook,
        sq_hook,
    ],
    options=[
        redeem_token_option,
        osd_option,
        coop_options,
    ],
)
