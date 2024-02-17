# ruff: noqa: D103

from typing import Any

from mods_base import ENGINE, get_pc, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .db import open_db
from .native import drops


@hook("/Script/OakGame.GFxPauseMenu:OnQuitChoiceMade")
def sq_hook(
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    if args.ChoiceNameId == "None":
        return

    # Close the native module's db connection on quit.
    # Since we're doing a write right after this, this should clean up the WAL files - otherwise
    # they will grow infinitely, if we keep a reader open constantly
    # Only closing it on sq is still relatively frequent, but let's us benefit from the optimization
    # of using a single connection for all drops in a single game session.
    drops.close_db()

    world = ENGINE.GameViewport.World.Name

    station: str
    try:
        save_game = get_pc().CurrentSavegame
        station = save_game.LastActiveTravelStationForPlaythrough[save_game.LastPlayThroughIndex]
    except IndexError:
        station = "Unknown"

    with open_db("w") as cur:
        cur.execute(
            """
            INSERT INTO
                SaveQuits (WorldName, Station)
            VALUES
                (?, ?)
            """,
            (world, station),
        )
