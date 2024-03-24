import os
import traceback
from collections.abc import Iterator
from dataclasses import dataclass

from bl3_mod_menu import DialogBox, DialogBoxChoice
from mods_base import (
    ENGINE,
    BaseOption,
    ButtonOption,
    GroupedOption,
    Mod,
    NestedOption,
    SliderOption,
)

from .db import open_db, reset_db
from .db_options import MapOption, PlanetOption, create_item_option
from .native import drops
from .osd import OUTPUT_TEXT_FILE, TEMPLATE_TEXT_FILE, osd_option, update_osd
from .tokens import redeem_token_option


def gen_item_options() -> Iterator[BaseOption]:
    """
    Generates all the options which are used to display what items have been collected.

    Yields:
        The child options.
    """
    with open_db("r") as cur:
        cur.execute(
            """
            SELECT
                PlanetID, PlanetName, MapID, MapName
            FROM
                OptionsList
            ORDER BY
                ID
            """,
        )
        for planet_id, planet_name, map_id, map_name in cur.fetchall():
            if planet_id is None:
                assert map_id is not None and map_name is not None
                yield MapOption(map_name, map_id=map_id)
            else:
                assert planet_id is not None and planet_name is not None
                yield PlanetOption(planet_name, planet_id=planet_id)


def gen_progression_options() -> Iterator[BaseOption]:
    """
    Generates all the options which are used to display the progression overview.

    Yields:
        The child options.
    """
    with open_db("r") as cur:
        cur.execute(
            """
            SELECT
                format("Items: %d/%d", CollectedCount, TotalCount),
                100.0 * CollectedCount / TotalCount,
                format("Points: %d/%d", CollectedPoints, TotalPoints),
                100.0 * CollectedPoints / TotalPoints
            FROM (
                SELECT
                    COUNT(*) FILTER (WHERE NumCollected > 0) as CollectedCount,
                    COUNT(*) as TotalCount,
                    IFNULL(SUM(Points) FILTER (WHERE NumCollected > 0), 0) as CollectedPoints,
                    SUM(Points) as TotalPoints
                FROM
                    CollectedItems
            )
            """,
        )
        item_name, item_percent, points_name, points_percent = cur.fetchone()

        for name, percent in ((item_name, item_percent), (points_name, points_percent)):
            yield SliderOption(
                name,
                percent,
                min_value=0,
                max_value=100,
                description=(
                    "The slider shows your percentage of completion. Somehow, changing it to 100%"
                    " doesn't actually finish the challenge for you."
                ),
            )

        yield NestedOption(
            "On Screen Display",
            (
                ButtonOption(
                    "Update Now",
                    description="Forces the displays to update now.",
                    on_press=lambda _: update_osd(),
                ),
                GroupedOption(
                    "External Text File",
                    (
                        ButtonOption(
                            "Open Template File",
                            description=(
                                "Opens the template file, which you can edit to fully customize the"
                                " display."
                            ),
                            on_press=lambda _: os.startfile(TEMPLATE_TEXT_FILE),  # type: ignore  # noqa: S606
                        ),
                        ButtonOption(
                            "Open Output File",
                            description="Opens the output file, which you should point OBS at.",
                            on_press=lambda _: os.startfile(OUTPUT_TEXT_FILE),  # type: ignore  # noqa: S606
                        ),
                    ),
                ),
                osd_option,
            ),
            description=(
                "Settings to help display these, and various other interesting stats, on screen.\n"
                "\n"
                "Supports both displaying in-game, or exporting to a text file for more advanced"
                " customization in OBS."
            ),
        )


def gen_token_options() -> Iterator[BaseOption]:
    """
    Generates all the options which are used to display the world drop token overview.

    Yields:
        The child options.
    """
    with open_db("r") as cur:
        cur.execute("SELECT format('Available Tokens: %d', Tokens) FROM AvailableTokens")
        title = cur.fetchone()[0]
        yield ButtonOption(
            title,
            description=(
                "On the item inspection screen, you can spend World Drop Tokens to redeem items"
                " which you got as a world drop (or from any other source not normally allowed).\n"
                "\n"
                "You initially have one world drop token, and can earn more by completing the main"
                " campaign missions. Subsequent completions are worth more.\n"
                "<font color='#FFFFFF'><b>Mission\t\t\t\t\t\t\tFirst\t\tSubsequent</b></font>\n"
                "<font color='#B0E0F0'>"
                "Divine Retribution\t\t\t\t\t2\t\t20\n"
                "All Bets Off\t\t\t\t\t\t1\t\t7\n"
                "The Call of Gythian\t\t\t\t\t1\t\t7\n"
                "Riding to Ruin\t\t\t\t\t\t1\t\t5\n"
                "Locus of Rage\t\t\t\t\t\t1\t\t5\n"
                "Mysteriouslier: Horror at Scryer's Crypt\t1\t\t3\n"
                "</font>"
            ),
        )
        yield redeem_token_option


reset_playthrough_choice = DialogBoxChoice("Reset Playthrough")


@DialogBox(
    "Reset Playthrough?",
    (reset_playthrough_choice, DialogBox.CANCEL),
    "Are you sure you want to reset your playthough? This cannot be reversed.",
    dont_show=True,
)
def reset_playthrough_dialog(choice: DialogBoxChoice) -> None:  # noqa: D103
    if choice != reset_playthrough_choice:
        return

    try:
        reset_db()
        DialogBox(
            "Reset Playthrough",
            (DialogBoxChoice("Ok"),),
            (
                "Your playthrough has been reset.\n"
                "\n"
                "Note you will need to re-open the Mods menu in order for the options to update."
            ),
        )
    except OSError as ex:
        DialogBox(
            "Reset Playthrough",
            (DialogBoxChoice("Ok"),),
            "Failed to reset playthrough!\n\n" + "".join(traceback.format_exception_only(ex)),
        )
        traceback.print_exc()


@ButtonOption(
    "Reset Playthrough",
    description="Delete all your data and reset your playthrough back to be beginning.",
)
def reset_playthrough_button(_button: ButtonOption) -> None:  # noqa: D103
    reset_playthrough_dialog.show()


@dataclass
class HuntTracker(Mod):
    def __post_init__(self) -> None:
        super().__post_init__()
        update_osd()

    def enable(self) -> None:  # noqa: D102
        super().enable()
        update_osd()
        drops.enable()

    def disable(self, dont_update_setting: bool = False) -> None:  # noqa: D102
        super().disable(dont_update_setting)
        update_osd()
        drops.disable()

    def iter_display_options(self) -> Iterator[BaseOption]:  # noqa: D102
        try:
            create_item_option.cache_clear()

            yield ButtonOption(
                "Open Rules",
                on_press=lambda _: os.startfile("https://apple1417.dev/bl3/hunt"),  # type: ignore  # noqa: S606
                description=(
                    "<font size='40' color='#FFFFFF'>https://apple1417.dev/bl3/hunt</font>\n"
                    "\n"
                    "Or press this button to open in your browser."
                ),
            )
            yield reset_playthrough_button
            yield GroupedOption("Progression", tuple(gen_progression_options()))
            yield GroupedOption("World Drop Tokens", tuple(gen_token_options()))

            # See if we can add the current world
            world: str = ENGINE.GameViewport.World.Name
            with open_db("r") as cur:
                cur.execute(
                    """
                    SELECT
                        MapID, MapName
                    FROM
                        ItemLocations
                    WHERE
                        WorldName = ?
                    LIMIT 1
                    """,
                    (world,),
                )
                row = cur.fetchone()
                if row is not None:
                    map_id, map_name = row
                    yield GroupedOption("Current Map", (MapOption(map_name, map_id=map_id),))

            yield GroupedOption("Items", tuple(gen_item_options()))
            yield GroupedOption(
                "Full Item List",
                (
                    FullItemListOption(
                        "Full Item List",
                        description=(
                            "Note that selecting this option may cause the game to freeze for"
                            "several seconds while the entire list is generated."
                        ),
                    ),
                ),
            )

        except Exception:  # noqa: BLE001
            yield ButtonOption(
                "Failed to generate description!",
                description=traceback.format_exc(),
            )
