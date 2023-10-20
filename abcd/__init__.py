if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

from mods_base import build_mod

from .ammo import infinite_ammo
from .god import cycle_god, refill_health
from .instant_kill import kill_all, one_shot
from .teleport import positions_option, restore_position, save_position, select_position

__version__: str
__version_info__: tuple[int, ...]

build_mod(
    keybinds=[
        save_position,
        restore_position,
        select_position,
        infinite_ammo,
        cycle_god,
        refill_health,
        one_shot,
        kill_all,
    ],
    options=[positions_option],
)
