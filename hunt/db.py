import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from mods_base import SETTINGS_DIR, open_in_mod_dir

from .native import drops

DB_PATH = SETTINGS_DIR / "hunt" / "hunt.sqlite3"
DB_TEMPLATE_PATH = Path(__file__).parent / "hunt.sqlite3.template"


@contextmanager
def open_db(mode: Literal["r", "w"]) -> Iterator[sqlite3.Cursor]:
    """
    Opens a connection to the db.

    Args:
        mode: What mode to open the db in.
    Returns:
        A new cursor for the db.
    """
    if not DB_PATH.exists():
        reset_db()

    read_only = "" if mode == "w" else "?mode=ro"
    con = sqlite3.connect(f"file:{DB_PATH}{read_only}", uri=True)
    if mode == "w":
        cur = con.cursor()

        try:
            yield cur
            con.commit()
        except Exception:  # noqa: BLE001
            con.rollback()
        finally:
            cur.close()

        _on_write_callbacks()

    else:
        cur = con.cursor()
        yield cur
        cur.close()

    con.close()


def reset_db() -> None:
    """Resets the db back to default."""
    drops.close_db()

    DB_PATH.parent.mkdir(exist_ok=True)

    # Try delete journal files as well
    for file in DB_PATH.parent.glob(DB_PATH.name + "*"):
        file.unlink()

    with open_in_mod_dir(DB_TEMPLATE_PATH, binary=True) as template, DB_PATH.open("wb") as db:
        shutil.copyfileobj(template, db)

    with open_db("w") as cur:
        cur.execute(
            """
            INSERT INTO
                MetaData (Key, Value)
            VALUES
                ("StartTime", datetime())
            """,
        )


@drops.set_db_getter
def native_db_getter() -> str:  # noqa: D103
    if not DB_PATH.exists():
        reset_db()
    return str(DB_PATH)


from .osd import update_osd  # noqa: E402


def _on_write_callbacks() -> None:
    update_osd()
