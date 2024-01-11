# ruff: noqa: D103

from typing import Any

from mods_base import ENGINE, get_pc, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .db import open_db


@hook("/Script/OakGame.GFxPauseMenu:OnQuitChoiceMade")
def sq_hook(
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    if args.ChoiceNameId == "None":
        return
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
                SaveQuits (Map, Station)
            VALUES
                (?, ?)
            """,
            (world, station),
        )
