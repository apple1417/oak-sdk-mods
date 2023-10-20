# ruff: noqa: D103

import unrealsdk
from mods_base import ENGINE, HiddenOption, get_pc, keybind
from ui_utils import show_hud_message

NUM_POSITIONS: int = 3
current_position_idx: int = 0


positions_option: HiddenOption[dict[str, list[dict[str, float] | None]]] = HiddenOption(
    "positions",
    {},
)


@keybind("Select Position")
def select_position() -> None:
    global current_position_idx

    current_position_idx += 1
    current_position_idx %= NUM_POSITIONS

    show_hud_message("Select Position", f"Selected slot {current_position_idx + 1}")


@keybind("Save Position")
def save_position() -> None:
    pc = get_pc()
    loc = pc.Pawn.K2_GetActorLocation()
    rot = pc.K2_GetActorRotation()

    world: str = ENGINE.GameViewport.World.Name

    if world not in positions_option.value:
        positions_option.value[world] = [None] * NUM_POSITIONS
    positions_option.value[world][current_position_idx] = {
        "x": loc.X,
        "y": loc.Y,
        "z": loc.Z,
        "pitch": rot.Pitch,
        "yaw": rot.Yaw,
        # Ignoring roll, since it's always 0
    }
    positions_option.save()

    show_hud_message("Save Position", f"Saved position to slot {current_position_idx + 1}")


@keybind("Restore Position")
def restore_position() -> None:
    world: str = ENGINE.GameViewport.World.Name

    position = positions_option.value.get(world, [None] * NUM_POSITIONS)[current_position_idx]

    if position is None:
        show_hud_message(
            "Restore Position",
            f"No position saved in slot {current_position_idx + 1}.",
        )
        return

    loc = unrealsdk.make_struct(
        "Vector",
        X=position["x"],
        Y=position["y"],
        Z=position["z"],
    )
    rot = unrealsdk.make_struct(
        "Rotator",
        Pitch=position["pitch"],
        Yaw=position["yaw"],
        Roll=0,
    )

    pc = get_pc()
    pc.ClientSetLocation(loc, rot)
    pc.ClientSetRotation(rot, True)
