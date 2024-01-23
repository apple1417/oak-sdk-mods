# ruff: noqa: D103

import string
from dataclasses import KW_ONLY, dataclass
from typing import Any

import unrealsdk
from mods_base import BoolOption, GroupedOption, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .db import open_db


@dataclass
class HuntStat(BoolOption):
    _: KW_ONLY
    format_id: str
    sql: str
    in_game_format: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()

        self.description += f"\n\nIn the text file use: &#123;{self.format_id}&#125;"

        if not self.in_game_format:
            self.in_game_format = f"{self.display_name}: {{{self.format_id}}}"


ALL_STATS: tuple[HuntStat, ...] = (
    HuntStat(
        "Total Items",
        True,
        description="Show the number of unique items you've collected.",
        format_id="total_items",
        sql="""
            SELECT
                COUNT(*) FILTER (WHERE NumCollected > 0)
            FROM
                CollectedItems
            """,
    ),
    HuntStat(
        "Percent Items",
        False,
        description="Show the percentage of unique items you've collected.",
        format_id="percent_items",
        in_game_format="Percent Items: {percent_items:.2f}%",
        sql="""
            SELECT
                100.0 * CollectedCount / TotalCount
            FROM (
                SELECT
                    COUNT(*) FILTER (WHERE NumCollected > 0) as CollectedCount,
                    COUNT(*) as TotalCount
                FROM
                    CollectedItems
            )
            """,
    ),
    HuntStat(
        "Total Points",
        False,
        description="Show the total point value of the items you've collected.",
        format_id="total_points",
        sql="""
            SELECT
                IFNULL(SUM(Points) FILTER (WHERE NumCollected > 0), 0)
            FROM
                CollectedItems
            """,
    ),
    HuntStat(
        "Percent Points",
        False,
        description="Show the percentage of points you've collected.",
        format_id="percent_points",
        in_game_format="Percent Points: {percent_points:.2f}%",
        sql="""
            SELECT
                100.0 * CollectedPoints / TotalPoints
            FROM (
                SELECT
                    IFNULL(SUM(Points) FILTER (WHERE NumCollected > 0), 0) as CollectedPoints,
                    SUM(Points) as TotalPoints
                FROM
                    CollectedItems
            )
            """,
    ),
    HuntStat(
        "Total SQs",
        True,
        description="Show the amount of times you've save quit during the playthrough.",
        format_id="total_sqs",
        sql="""
            SELECT
                COUNT(*)
            FROM
                SaveQuits
            """,
    ),
    HuntStat(
        "Total Drops",
        False,
        description="Show the total amount of drops you've collected, including duplicates.",
        format_id="total_drop",
        sql="""
            SELECT
                SUM(NumCollected)
            FROM
                CollectedItems
            """,
    ),
    HuntStat(
        "Total Duplicates",
        False,
        description="Show the total amount of duplicate drops you've collected.",
        format_id="total_duplicates",
        sql="""
            SELECT
                SUM(NumCollected - 1)
            FROM
                CollectedItems
            WHERE
                NumCollected > 1
            """,
    ),
    HuntStat(
        "Latest Drop",
        False,
        description="Show the latest drop you've collected, including duplicates.",
        format_id="latest_drop",
        sql="""
            SELECT IFNULL(
                (
                    SELECT
                        Name
                    FROM
                        Items
                    WHERE
                        ID = (
                            SELECT
                                ItemID
                            FROM
                                Collected
                            ORDER BY
                                rowid DESC
                            LIMIT 1
                        )
                ),
                'No Drops Collected'
            )
            """,
    ),
    HuntStat(
        "Latest Item",
        False,
        description="Show the latest new item you've collected, excluding duplicates.",
        format_id="latest_item",
        sql="""
            SELECT IFNULL(
                (
                    SELECT
                        Name
                    FROM
                        CollectedItems
                    WHERE
                        NumCollected > 0
                    ORDER BY
                        FirstCollectTime DESC
                    LIMIT 1
                ),
                'No Drops Collected'
            )
            """,
    ),
    HuntStat(
        "SQs Since Last Drop",
        False,
        description=(
            "Show the amount of times you've sq since collecting the last drop, including"
            " duplicates."
        ),
        format_id="sqs_since_last_drop",
        sql="""
            SELECT
                COUNT(*)
            FROM
                SaveQuits
            WHERE
                QuitTime > IFNULL(
                    (
                        SELECT
                            CollectTime
                        FROM
                            Collected
                        ORDER BY
                            rowid DESC
                        LIMIT 1
                    ),
                    ''
                )
            """,
    ),
    HuntStat(
        "SQs Since Last Item",
        False,
        description=(
            "Show the amount of times you've sq since collecting the last new item, excluding"
            " duplicates."
        ),
        format_id="sqs_since_last_item",
        sql="""
            SELECT
                COUNT(*)
            FROM
                SaveQuits
            WHERE
                QuitTime > IFNULL(
                    (
                        SELECT
                            FirstCollectTime
                        FROM
                            CollectedItems
                        WHERE
                            NumCollected > 0
                        ORDER BY
                            FirstCollectTime DESC
                        LIMIT 1
                    ),
                    ''
                )
            """,
    ),
)

osd_option = GroupedOption("On Screen Display", children=ALL_STATS, display_name="Show In Game")

STAT_BY_FORMAT_ID: dict[str, HuntStat] = {stat.format_id: stat for stat in ALL_STATS}
FORMATTER = string.Formatter()


def format_stats(format_string: str) -> str:
    """
    Formats a string using the various hunt stats.

    Ags:
        format_string: The string to format.
    Returns:
        The formatted string.
    """
    kwargs: dict[str, Any] = {}

    with open_db("r") as cur:
        for _, format_id, _, _ in FORMATTER.parse(format_string):
            if format_id is None:
                continue
            stat = STAT_BY_FORMAT_ID.get(format_id, None)
            if stat is None:
                continue
            cur.execute(stat.sql)
            kwargs[format_id] = cur.fetchone()[0]

    return format_string.format(**kwargs)


WHITE = unrealsdk.make_struct("LinearColor", R=1, G=1, B=1, A=1)
BLACK_50 = unrealsdk.make_struct("LinearColor", A=0.5)
FONT = unrealsdk.find_object("Font", "/Game/UI/_Shared/Fonts/OAK_BODY.OAK_BODY")
OUTER_PADDING = 10
INTER_LINE_PADDING = 1


@hook("/Script/Engine.HUD:ReceiveDrawHUD")
def draw_osd_hook(
    obj: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    lines: list[str] = [format_stats(stat.in_game_format) for stat in ALL_STATS if stat.value]
    if not lines:
        return

    max_width: float = 0
    heights: list[float] = []
    for line in lines:
        _, w, h = obj.GetTextSize(line, 0, 0, FONT, 1)
        max_width = max(w, max_width)
        heights.append(h)

    obj.DrawRect(
        BLACK_50,
        0,
        0,
        max_width + 2 * OUTER_PADDING,
        sum(heights) + len(heights) * INTER_LINE_PADDING + 2 * OUTER_PADDING,
    )
    for idx, line in enumerate(lines):
        obj.DrawText(
            line,
            WHITE,
            OUTER_PADDING,
            OUTER_PADDING + sum(heights[:idx]) + idx * INTER_LINE_PADDING,
            FONT,
            1,
            False,
        )
