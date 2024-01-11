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
    SliderOption,
)

from .db import open_db, reset_db
from .db_options import MapOption, PlanetOption, create_item_option
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
                100.0 * CollectedPoints / TotalPoints,
                format("Total Save Quits: %d", (SELECT COUNT(*) FROM SaveQuits))
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
        item_name, item_percent, points_name, points_percent, save_quits_name = cur.fetchone()

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
        yield ButtonOption(
            save_quits_name,
            description=(
                "The total number of save quits you've done with the tracker active since last"
                " resetting playthrough. Counts clicks of the SQ buttons, so won't trigger on"
                " crashes.\n"
                "\n"
                "You can expect a full clear to take in the ballpark of 2000."
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
    def iter_display_options(self) -> Iterator[BaseOption]:  # noqa: D102
        for option in super().iter_display_options():
            if isinstance(option, GroupedOption) and option.identifier == "Options":
                break
            yield option

        try:
            create_item_option.cache_clear()

            yield ButtonOption(
                "Open Rules",
                on_press=lambda _: os.startfile("https://pastebin.com/NQ9YR5ZS"),  # type: ignore
                description=(
                    "Open the rules in your browser.\n"
                    "\n"
                    "If pressing the button does nothing, you can view them at:\n"
                    "<font size='40' color='#FFFFFF'>https://pastebin.com/NQ9YR5ZS</font>"
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

            yield GroupedOption("Full Item List", tuple(gen_item_options()))

        except Exception:  # noqa: BLE001
            yield ButtonOption(
                "Failed to generate description!",
                description=traceback.format_exc(),
            )
