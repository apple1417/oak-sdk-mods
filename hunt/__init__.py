# ruff: noqa: D103

if True:
    assert __import__("mods_base").__version_info__ >= (1, 1), "Please update the SDK"
    assert __import__("bl3_mod_menu").__version_info__ >= (1, 0), "Please update the SDK"
    assert __import__("pyunrealsdk").__version_info__ >= (1, 1, 0), "Please update the SDK"
    assert __import__("ui_utils").__version_info__ >= (1, 0), "Please update the SDK"

from mods_base import build_mod

from .drops import drop_hook, itemcard_hook, world_change_hook
from .mod_class import HuntTracker
from .osd import osd_option, update_osd
from .sqs import sq_hook
from .tokens import (
    item_inspect_end_hook,
    item_inspect_start_hook,
    mission_complete_hook,
    redeem_token_option,
)

__version__: str
__version_info__: tuple[int, ...]

mod = build_mod(
    cls=HuntTracker,
    hooks=[
        drop_hook,
        itemcard_hook,
        world_change_hook,
        mission_complete_hook,
        item_inspect_end_hook,
        item_inspect_start_hook,
        sq_hook,
    ],
    options=[
        redeem_token_option,
        osd_option,
    ],
)


# To avoid circular imports, only define these after build mod
# This is because calling `update_osd`` imports mod from above
def on_enable() -> None:
    update_osd()


def on_disable() -> None:
    update_osd()


mod.on_enable = on_enable
mod.on_disable = on_disable

update_osd()
