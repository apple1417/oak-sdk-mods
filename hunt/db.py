import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from mods_base import SETTINGS_DIR, open_in_mod_dir

DB_PATH = SETTINGS_DIR / "hunt.sqlite3"
DB_TEMPLATE_PATH = Path(__file__).parent / "generate_db" / "hunt.sqlite3"

cached_readonly_con: sqlite3.Connection | None = None
cached_readwrite_con: sqlite3.Connection | None = None


@contextmanager
def open_db(mode: Literal["r", "w"]) -> Iterator[sqlite3.Cursor]:
    """
    Opens a connection to the db.

    Args:
        mode: What mode to open the db in.
    Returns:
        A new cursor for the db.
    """
    global cached_readonly_con, cached_readwrite_con

    if not DB_PATH.exists():
        reset_db()

    if cached_readonly_con is None or cached_readwrite_con is None:
        cached_readonly_con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cached_readwrite_con = sqlite3.connect(f"file:{DB_PATH}", uri=True)

        cached_readonly_con.cursor().execute("PRAGMA foreign_keys = ON")
        cached_readwrite_con.cursor().execute("PRAGMA foreign_keys = ON")

    if mode == "w":
        cur = cached_readwrite_con.cursor()

        try:
            yield cur
            cached_readwrite_con.commit()
        except Exception:  # noqa: BLE001
            cached_readwrite_con.rollback()
        finally:
            cur.close()

    else:
        yield cached_readonly_con.cursor()


def reset_db() -> None:
    """Resets the db back to default."""
    global cached_readonly_con, cached_readwrite_con

    if cached_readonly_con is not None:
        cached_readonly_con.close()
    cached_readonly_con = None
    if cached_readwrite_con is not None:
        cached_readwrite_con.close()
    cached_readwrite_con = None

    DB_PATH.unlink(missing_ok=True)
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
