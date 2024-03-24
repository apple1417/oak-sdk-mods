# ruff: noqa: D103

from mods_base import html_to_plain_text
from ui_utils import show_hud_message
from unrealsdk import logging

from .db import open_db
from .native.drops import set_drop_callback


@set_drop_callback
def on_valid_drop(bal_name: str) -> None:
    with open_db("w") as cur:
        cur.execute(
            """
            INSERT INTO
                Collected (ItemID)
            SELECT
                ID
            FROM
                Items
            WHERE
                Balance = ?
            """,
            (bal_name,),
        )

    with open_db("r") as cur:
        # The first time you collect an item, partly base the duration of the message on the point
        # value, let the more valuable stuff hang around a bit longer
        cur.execute(
            """
            SELECT
                IIF(NumCollected > 1,
                    'Duplicate ' || Name,
                    Name
                ),
                IIF(NumCollected > 1,
                    'Collected ' || NumCollected ||' times',
                    '<font color="#00ff00">+'
                        || Points
                        || '</font> point'
                        || IIF(Points > 1, 's', '')
                ),
                IIF(NumCollected > 1,
                    4,
                    MAX(4, MIN(8, Points))
                )
            FROM
                CollectedItems
            WHERE
                Balance = ?
            """,
            (bal_name,),
        )
        title, message, duration = cur.fetchone()
        show_hud_message(title, message, duration)
        logging.info(html_to_plain_text(f"[HUNT] {title}: {message}"))
