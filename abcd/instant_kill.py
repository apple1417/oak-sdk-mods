# ruff: noqa: D103

from typing import Any

import unrealsdk
from mods_base import BoolOption, get_pc, hook, keybind
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


one_shot_one_percent_option = BoolOption(
    "One Shot to 1% HP",
    False,
    description=(
        "Limit One Shot Mode to setting enemies' health to 1%. Usually, this prevents skipping"
        " phase changes, but some enemies need to phase in order to properly kill them."
    ),
)


@hook("/Script/GbxGameSystemCore.DamageComponent:ReceiveAnyDamage", Type.PRE)
def receive_any_damage(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    pc = get_pc()
    if args.InstigatedBy != pc:
        return
    if not pc.GetTeamComponent().IsHostile(obj.Outer):
        return

    obj.SetCurrentShield(0)

    # Try set the enemy hp to 1%, so that your bullet kills them, which usually triggers all the
    # proper death logic
    # If this fails, and you hit someone at less than 1%, just set to 0 directly - unless the we
    # have the option overriding it
    one_percent = obj.GetMaxHealth() / 100
    if obj.GetCurrentHealth() > one_percent:
        obj.SetCurrentHealth(one_percent)
    elif not one_shot_one_percent_option.value:
        obj.SetCurrentHealth(0)
