# ruff: noqa: D103
if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

from typing import Any

import unrealsdk
from mods_base import ENGINE, BoolOption, EInputEvent, build_mod, hook, keybind
from unrealsdk.hooks import Block, Type

__version__: str
__version_info__: tuple[int, ...]


@keybind("Skip Dialog")
def skip_dialog() -> None:
    for dialog in unrealsdk.find_all("GbxDialogComponent", exact=False):
        thread_id = dialog.CurrentPerformance.DialogThreadID
        if thread_id > 0:
            dialog.StopPerformance(thread_id, True)


auto_skip = BoolOption(
    "Auto Skip",
    False,
    description=(
        "Automatically skip all dialog as soon as it is started. This includes <i>all dialog</i>,"
        " including miscellaneous idle dialog, so you might want to disable this while not playing"
        " through the story."
    ),
)


@hook("/Script/GbxDialog.GbxDialogComponent:StartPerformance", Type.PRE)
def dialog_start_performance(*_: Any) -> None | type[Block]:
    return Block if auto_skip.value else None


# This is basically stolen straight from ABCD

gameplay_statics = unrealsdk.find_class("GameplayStatics").ClassDefaultObject

set_time_dialation = gameplay_statics.SetGlobalTimeDilation
get_time_dialoation = gameplay_statics.GetGlobalTimeDilation

FAST_FORWARD_SPEED = 8


@keybind("Fast Forward (Toggle)")
def fast_forward_toggle() -> None:
    world = ENGINE.GameViewport.World
    current_dialation = get_time_dialoation(world)
    new_dialation = FAST_FORWARD_SPEED if current_dialation == 1 else 1
    set_time_dialation(world, new_dialation)


@keybind("Fast Forward (Hold)", event_filter=None)
def fast_forward_hold(event: EInputEvent) -> None:
    dialation: float

    match event:
        case EInputEvent.IE_Pressed:
            dialation = FAST_FORWARD_SPEED
        case EInputEvent.IE_Released:
            dialation = 1
        case _:
            return

    set_time_dialation(ENGINE.GameViewport.World, dialation)


build_mod()
