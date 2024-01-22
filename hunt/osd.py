# ruff: noqa: D103

from typing import Any

import unrealsdk
from mods_base import BoolOption, GroupedOption, NestedOption, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

WHITE = unrealsdk.make_struct("LinearColor", R=1, G=1, B=1, A=1)
BLACK_50 = unrealsdk.make_struct("LinearColor", A=0.5)
FONT = unrealsdk.find_object("Font", "/Game/UI/_Shared/Fonts/OAK_BODY.OAK_BODY")
OUTER_PADDING = 10
INTER_LINE_PADDING = 1

items_option = BoolOption(
    "Items",
    True,
    description="Show the amount of unique items you've collected.",
)
points_option = BoolOption(
    "Points",
    False,
    description="Show the total point value of the items you've collected.",
)
sqs_option = BoolOption(
    "SQs",
    True,
    description="Show the amount of times you've save quit during the playthrough.",
)

osd_option = NestedOption(
    "On Screen Display",
    children=(
        GroupedOption(
            "In-Game",
            children=(
                items_option,
                points_option,
                sqs_option,
            ),
        ),
    ),
    description="Options for displaying these stats on screen.",
)


@hook("/Script/Engine.HUD:ReceiveDrawHUD")
def draw_osd_hook(
    obj: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    lines: list[str] = []
    if items_option.value:
        lines.append("Items: 213/379")
    if points_option.value:
        lines.append("Points: 866/1872")
    if sqs_option.value:
        lines.append("SQs: 1862")
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
