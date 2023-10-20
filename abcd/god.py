# ruff: noqa: D103

from mods_base import get_pc, keybind
from ui_utils import show_hud_message


@keybind("God Mode")
def cycle_god() -> None:
    pawn = get_pc().Pawn
    if pawn is None:
        return
    damage_comp = pawn.DamageComponent
    if damage_comp is None:
        return

    if damage_comp.bGodMode:
        damage_comp.bGodMode = False
        damage_comp.bDemiGodMode = True
        show_hud_message("God Mode", "1 HP")
    elif damage_comp.bDemiGodMode:
        damage_comp.bGodMode = False
        damage_comp.bDemiGodMode = False
        show_hud_message("God Mode", "Off")
    else:
        damage_comp.bGodMode = True
        damage_comp.bDemiGodMode = False
        show_hud_message("God Mode", "Full")


@keybind("Refill Health + Shields")
def refill_health() -> None:
    pawn = get_pc().Pawn
    if pawn is None:
        return
    pawn.FillAllHealth()
