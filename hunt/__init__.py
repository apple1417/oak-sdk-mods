if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

from mods_base import build_mod

from .drops import drop_hook, itemcard_hook, world_change_hook
from .mod_class import HuntTracker
from .osd import draw_osd_hook, osd_option
from .sqs import sq_hook
from .tokens import (
    item_inspect_end_hook,
    item_inspect_start_hook,
    mission_complete_hook,
    redeem_token_option,
)

__version__: str
__version_info__: tuple[int, ...]

build_mod(
    cls=HuntTracker,
    hooks=[
        drop_hook,
        itemcard_hook,
        world_change_hook,
        mission_complete_hook,
        item_inspect_end_hook,
        item_inspect_start_hook,
        sq_hook,
        draw_osd_hook,
    ],
    options=[
        redeem_token_option,
        osd_option,
    ],
)
