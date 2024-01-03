# ruff: noqa: D103

import unrealsdk
from mods_base import ENGINE, EInputEvent, SliderOption, keybind

gameplay_statics = unrealsdk.find_class("GameplayStatics").ClassDefaultObject

set_time_dialation = gameplay_statics.SetGlobalTimeDilation
get_time_dialoation = gameplay_statics.GetGlobalTimeDilation

fast_forward_speed = SliderOption("Fast Forward Speed", 8, 1, 50)


@keybind("Fast Forward (Toggle)")
def fast_forward_toggle() -> None:
    world = ENGINE.GameViewport.World
    current_dialation = get_time_dialoation(world)
    new_dialation = fast_forward_speed.value if current_dialation == 1 else 1
    set_time_dialation(world, new_dialation)


@keybind("Fast Forward (Hold)", event_filter=None)
def fast_forward_hold(event: EInputEvent) -> None:
    dialation: float

    match event:
        case EInputEvent.IE_Pressed:
            dialation = fast_forward_speed.value
        case EInputEvent.IE_Released:
            dialation = 1
        case _:
            return

    set_time_dialation(ENGINE.GameViewport.World, dialation)
