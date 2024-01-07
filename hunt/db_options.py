import traceback
from collections.abc import Sequence
from dataclasses import KW_ONLY, dataclass, field
from functools import cache, cached_property

from mods_base import BaseOption, ButtonOption, NestedOption

from .db import open_db


# Cache this since the same item may exist in multiple maps
@cache
def create_item_option(item_id: int) -> BaseOption:
    """
    Creates an option to display a single item.

    Args:
        item_id: The item to display.
    Returns:
        A new option.
    """
    with open_db("r") as cur:
        cur.execute(
            """
            SELECT
                format(
                    '<img src="img://Game/UI/Menus/Debug/%s" width="18" height="18"/>  %s',
                    IIF(NumCollected <= 0,
                        'T_HUD_MissionTrackerBoxUnchecked.T_HUD_MissionTrackerBoxUnchecked',
                        'T_HUD_MissionTrackerBoxChecked.T_HUD_MissionTrackerBoxChecked'),
                    Name
                ),
                Name,
                CASE NumCollected
                    WHEN 0 THEN Description
                    WHEN 1 THEN format(
                        'Collected %s%c%c%s',
                        datetime(FirstCollectTime, 'localtime'),
                        char(10),
                        char(10),
                        Description
                    )
                    ELSE format(
                        'Collected %d times, first at %s%c%c%s',
                        NumCollected,
                        datetime(FirstCollectTime, 'localtime'),
                        char(10),
                        char(10),
                        Description
                    )
                END
            FROM
                CollectedItems
            WHERE
                ID = ?
            """,
            (item_id,),
        )
        title, description_title, description = cur.fetchone()
        return ButtonOption(title, description_title=description_title, description=description)


@dataclass
class MapOption(NestedOption):
    _: KW_ONLY
    map_id: int

    children: Sequence[BaseOption] = field(init=False, default_factory=tuple)  # type: ignore

    def __post_init__(self) -> None:
        super().__post_init__()
        del self.children
        del self.description

    @cached_property
    def description(self) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]  # noqa: D102
        try:
            with open_db("r") as cur:
                cur.execute(
                    """
                    SELECT
                        format(
                            'Total: %d/%d (%d%%)%c%c%s',
                            COUNT(*) FILTER (WHERE NumCollected > 0),
                            COUNT(*),
                            (
                                100.0 * IFNULL(
                                    SUM(Points) FILTER (WHERE NumCollected > 0),
                                    0
                                ) / SUM(Points)
                            ),
                            char(10),
                            char(10),
                            (
                                SELECT
                                    GROUP_CONCAT(Summary, char(10))
                                FROM
                                (
                                    SELECT
                                        (
                                            '<img src="img://Game/UI/Menus/Debug/'
                                            || IIF(c.NumCollected > 0,
                                                    'T_HUD_MissionTrackerBoxChecked.T_HUD_MissionTrackerBoxChecked',
                                                    'T_HUD_MissionTrackerBoxUnchecked.T_HUD_MissionTrackerBoxUnchecked')
                                            || '" width="18" height="18"/>  '
                                            || i.Name
                                        ) as Summary
                                    FROM
                                        CollectedLocations as c
                                    LEFT JOIN
                                        Items as i ON c.ItemID = i.ID
                                    WHERE
                                        c.MapID = ?
                                    ORDER BY
                                        c.ID
                                )
                            )
                        )
                    FROM
                        CollectedLocations
                    WHERE
                        MapID = ?
                    """,
                    (self.map_id, self.map_id),
                )
                return cur.fetchone()[0]
        except Exception:  # noqa: BLE001
            return "Failed to generate description!\n\n" + traceback.format_exc()

    @cached_property
    def children(self) -> Sequence[BaseOption]:  # pyright: ignore[reportIncompatibleVariableOverride]  # noqa: D102
        try:
            with open_db("r") as cur:
                cur.execute(
                    """
                    SELECT
                        ItemID
                    FROM
                        ItemLocations
                    WHERE
                        MapID = ?
                    ORDER BY
                        ID
                    """,
                    (self.map_id,),
                )

                return tuple(create_item_option(item_id) for (item_id,) in cur.fetchall())
        except Exception:  # noqa: BLE001
            return (
                ButtonOption(
                    "Failed to generate children!",
                    description=traceback.format_exc(),
                ),
            )


@dataclass
class PlanetOption(NestedOption):
    _: KW_ONLY
    planet_id: int

    children: Sequence[BaseOption] = field(init=False, default_factory=tuple)  # type: ignore

    def __post_init__(self) -> None:
        super().__post_init__()
        del self.children
        del self.description

    @cached_property
    def description(self) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]  # noqa: D102
        try:
            with open_db("r") as cur:
                cur.execute(
                    """
                    SELECT
                        format(
                            'Total: %d/%d (%d%%)%c%c%s',
                            COUNT(*) FILTER (WHERE NumCollected > 0),
                            COUNT(*),
                            (
                                100.0 * IFNULL(
                                    SUM(Points) FILTER (WHERE NumCollected > 0),
                                    0
                                ) / SUM(Points)
                            ),
                            char(10),
                            char(10),
                            (
                                SELECT
                                    GROUP_CONCAT(Summary, char(10))
                                FROM
                                (
                                    SELECT
                                        format(
                                            '%s: %d/%d (%d%%)',
                                            MapName,
                                            COUNT(*) FILTER (WHERE NumCollected > 0),
                                            COUNT(*),
                                            (
                                                100.0 * IFNULL(
                                                    SUM(Points) FILTER (WHERE NumCollected > 0),
                                                    0
                                                ) / SUM(Points)
                                            )
                                        ) as Summary
                                    FROM
                                        CollectedLocations
                                    WHERE
                                        PlanetID = ?
                                    GROUP BY
                                        MapID
                                    ORDER BY
                                        ID
                                )
                            )
                        )
                    FROM
                        (
                            SELECT
                                *
                            FROM
                                CollectedLocations
                            WHERE
                                PlanetID = ?
                            GROUP BY
                                ItemID
                        )
                    """,
                    (self.planet_id, self.planet_id),
                )
                return cur.fetchone()[0]
        except Exception:  # noqa: BLE001
            return "Failed to generate description!\n\n" + traceback.format_exc()

    @cached_property
    def children(self) -> Sequence[BaseOption]:  # pyright: ignore[reportIncompatibleVariableOverride]  # noqa: D102
        try:
            with open_db("r") as cur:
                cur.execute(
                    """
                    SELECT DISTINCT
                        MapName, MapID
                    FROM
                        ItemLocations
                    WHERE
                        PlanetID = ?
                    ORDER BY
                        ID
                    """,
                    (self.planet_id,),
                )
                return tuple(
                    MapOption(map_name, map_id=map_id) for map_name, map_id in cur.fetchall()
                )
        except Exception:  # noqa: BLE001
            return (
                ButtonOption(
                    "Failed to generate children!",
                    description=traceback.format_exc(),
                ),
            )
