# ruff: noqa: D103

import string
import textwrap
from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass
from threading import Thread
from typing import Any, Self

import unrealsdk
from mods_base import SETTINGS_DIR, BoolOption, GroupedOption, HookProtocol, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .db import open_db

OUTPUT_TEXT_FILE = SETTINGS_DIR / "hunt_osd.txt"
TEMPLATE_TEXT_FILE = SETTINGS_DIR / "hunt_osd.template.txt"


def on_hunt_stat_change(option: BoolOption, new_value: bool) -> None:
    # On change is called before setting the new value, but we want to query it in `update_osd`, so
    # just change it ourselves
    option.value = new_value
    update_osd()


@dataclass
class HuntStat(BoolOption):
    on_change: Callable[[Self, bool], None] | None = on_hunt_stat_change

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
        "Items",
        True,
        description="Show the number of unique items you've collected.",
        format_id="num_items",
        sql="""
            SELECT
                COUNT(*) FILTER (WHERE NumCollected > 0)
            FROM
                CollectedItems
            """,
    ),
    HuntStat(
        "Total Items",
        True,
        description="Show the total number of available items.",
        format_id="total_items",
        sql="""
            SELECT
                COUNT(*)
            FROM
                Items
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
        "Points",
        False,
        description="Show the total point value of the items you've collected.",
        format_id="num_points",
        sql="""
            SELECT
                IFNULL(SUM(Points) FILTER (WHERE NumCollected > 0), 0)
            FROM
                CollectedItems
            """,
    ),
    HuntStat(
        "Total Points",
        True,
        description="Show the total number of available points.",
        format_id="total_points",
        sql="""
            SELECT
                SUM(Points)
            FROM
                Items
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

osd_option = GroupedOption("On Screen Display", ALL_STATS, display_name="In Game")

STAT_BY_FORMAT_ID: dict[str, HuntStat] = {stat.format_id: stat for stat in ALL_STATS}
FORMATTER = string.Formatter()


def format_stats(format_string: str) -> str:
    """
    Formats a string using the various hunt stats.

    Args:
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


def create_template_file() -> None:
    """Creates the template text file."""
    with TEMPLATE_TEXT_FILE.open("w") as file:
        file.write(
            "This file is the template for the on screen display text file. You can edit it\n"
            "to completely customize the output.\n"
            "\n"
            "The following patterns will be substituted:\n",
        )

        for stat in ALL_STATS:
            file.write(stat.in_game_format)
            file.write("\n")

        file.write(
            "\n"
            "These use standard Python string formatting.\n"
            "https://docs.python.org/3/library/string.html#formatstrings\n",
        )


WHITE = unrealsdk.make_struct("LinearColor", R=1, G=1, B=1, A=1)
BLACK_50 = unrealsdk.make_struct("LinearColor", A=0.5)
FONT = unrealsdk.find_object("Font", "/Game/UI/_Shared/Fonts/OAK_BODY.OAK_BODY")
OUTER_PADDING = 10
INTER_LINE_PADDING = 1

DRAW_RECT = unrealsdk.find_object("Function", "/Script/Engine.HUD:DrawRect")
DRAW_TEXT = unrealsdk.find_object("Function", "/Script/Engine.HUD:DrawText")

# Since calculating what to draw each frame is expensive, we'll just construct a hook that draws
# exactly what we need
draw_osd_hook: HookProtocol | None = None

# We format the lines to draw in a thread
# However, for some reason, trying to call `HUD::GetTextSize` out of band just returns 0, so we
# can't calculate layout in the thread - we use this list to transfer between the two
lines_to_draw: list[str] = []


def update_osd() -> None:
    # Updating is expensive, do it in a thread
    Thread(target=_update_osd_inner).start()


def _update_osd_inner() -> None:
    global draw_osd_hook, lines_to_draw

    # Can't put this any higher due to circular imports
    from . import mod

    if not mod.is_enabled:
        return

    if not TEMPLATE_TEXT_FILE.exists():
        create_template_file()

    with TEMPLATE_TEXT_FILE.open("r") as template, OUTPUT_TEXT_FILE.open("w") as out:
        out.write(format_stats(template.read()))

    # If nothing to draw
    if not any(stat.value for stat in ALL_STATS):
        if draw_osd_hook is not None:
            draw_osd_hook.disable()
            draw_osd_hook = None
        return

    lines_to_draw = [format_stats(stat.in_game_format) for stat in ALL_STATS if stat.value]
    if not lines_to_draw:
        return

    update_osd_hook.enable()


@hook("/Script/Engine.HUD:ReceiveDrawHUD")
def update_osd_hook(
    obj: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    global draw_osd_hook

    update_osd_hook.disable()

    if draw_osd_hook is not None:
        draw_osd_hook.disable()
    draw_osd_hook = None

    max_width: float = 0
    heights: list[float] = []
    for line in lines_to_draw:
        _, w, h = obj.GetTextSize(line, 0, 0, FONT, 1)
        max_width = max(w, max_width)
        heights.append(h)

    source = textwrap.dedent(
        f"""
        @hook("/Script/Engine.HUD:ReceiveDrawHUD")
        def draw_osd_hook(
            obj: UObject,
            _2: WrappedStruct,
            _3: Any,
            _4: BoundFunction,
        ) -> None:
            obj._get_field(DRAW_RECT)(
                BLACK_50,
                0,
                0,
                {max_width + 2 * OUTER_PADDING!r},
                {sum(heights) + len(heights) * INTER_LINE_PADDING + 2 * OUTER_PADDING!r},
            )
        """,
    )
    for idx, line in enumerate(lines_to_draw):
        source += textwrap.indent(
            textwrap.dedent(
                f"""
                obj._get_field(DRAW_TEXT)(
                    {line!r},
                    WHITE,
                    {OUTER_PADDING!r},
                    {OUTER_PADDING + sum(heights[:idx]) + idx * INTER_LINE_PADDING!r},
                    FONT,
                    1,
                    False,
                )
                """,
            ),
            prefix=" " * 4,
        )

    globals_dict: dict[str, Any] = {
        "hook": hook,
        "UObject": UObject,
        "WrappedStruct": WrappedStruct,
        "Any": Any,
        "BoundFunction": BoundFunction,
        "BLACK_50": BLACK_50,
        "WHITE": WHITE,
        "FONT": FONT,
        "DRAW_RECT": DRAW_RECT,
        "DRAW_TEXT": DRAW_TEXT,
    }
    exec(source, globals_dict)  # noqa: S102

    new_hook: HookProtocol = globals_dict["draw_osd_hook"]

    draw_osd_hook = new_hook
    draw_osd_hook.enable()
