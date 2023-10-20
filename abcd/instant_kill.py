# ruff: noqa: D103

from typing import Any

import unrealsdk
from mods_base import get_pc, hook, keybind
from ui_utils import show_hud_message
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct


@keybind("Kill All")
def kill_all() -> None:
    is_hostile = get_pc().GetTeamComponent().IsHostile

    for pawn in unrealsdk.find_all("OakCharacter", exact=False):
        if not is_hostile(pawn):
            continue

        damage_comp = pawn.DamageComponent
        damage_comp.SetCurrentShield(0)
        damage_comp.SetCurrentHealth(0)


one_shot_mode_on = False


@keybind("One Shot Mode")
def one_shot() -> None:
    global one_shot_mode_on
    one_shot_mode_on = not one_shot_mode_on

    show_hud_message("One Shot Mode", ("Off", "On")[one_shot_mode_on])
    if one_shot_mode_on:
        receive_any_damage.enable()
    else:
        receive_any_damage.disable()


@hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE)
def receive_any_damage(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    pc = get_pc()
    if args.InstigatedBy != pc:
        return
    if not pc.GetTeamComponent().IsHostile(obj.Outer):
        return

    obj.SetCurrentShield(0)
    if obj.GetCurrentHealth() > 1:
        obj.SetCurrentHealth(1)
    else:
        obj.SetCurrentHealth(0)
