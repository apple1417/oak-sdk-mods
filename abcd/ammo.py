# ruff: noqa: D103

from mods_base import get_pc, keybind
from ui_utils import show_hud_message


@keybind("Infinite Ammo")
def infinite_ammo() -> None:
    pc = get_pc()
    pc.bInfiniteAmmo = not pc.bInfiniteAmmo

    show_hud_message("Infinite Ammo", ("Off", "On")[pc.bInfiniteAmmo])
