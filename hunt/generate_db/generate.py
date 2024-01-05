#!/usr/bin/env python
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path

HUNT_DB = Path(__file__).with_name("hunt.sqlite3")

HUNT_SHEET = Path(__file__).with_name("BL3 Hunt Sheet v3 - Drops.csv")
UNIQUES_DB = Path(__file__).with_name("_uniques.sqlite3")

RARITY_COLOURS = (
    ("Legendary", "#ffb400"),
    ("Purple", "#a83fe5"),
    ("Blue", "#3c8eff"),
    ("Green", "#3dd20b"),
    ("White", "#f0f0f0"),
)

POINT_COLOUR = "#00ff00"


@dataclass(frozen=True)
class Planet:
    name: str
    maps: tuple[str, ...]


# The current and any map options always comes before these
OPTIONS_LAYOUT: tuple[Planet, ...] = (
    Planet("Any Map", ("Any Map",)),
    Planet("Sanctuary", ("Sanctuary",)),
    Planet(
        "Pandora",
        (
            "Covenant Pass",
            "Droughts",
            "Ascension Bluff",
            "Devil's Razor",
            "Splinterlands",
            "Carnivora",
            "Guts of Carnivora",
            "Konrad's Hold",
            "Sandblast Scar",
            "Cathedral of the Twin Gods",
            "Great Vault",
            "Destroyer's Rift",
            "Slaughter Shaft",
        ),
    ),
    Planet(
        "Promethea",
        (
            "Meridian Outskirts",
            "Meridian Metroplex",
            "Lectra City",
            "Skywell-27",
            "Atlas HQ",
            "Neon Arterial",
            "Forgotten Basilica",
            "Cistern of Slaughter",
        ),
    ),
    Planet(
        "Eden-6",
        (
            "Floodmoor Basin",
            "Anvil",
            "Jakobs Estate",
            "Voracious Canopy",
            "Ambermire",
            "Blackbarrel Cellars",
            "Floating Tomb",
        ),
    ),
    Planet(
        "Nekrotafeyo",
        (
            "Desolation's Edge",
            "Tazendeer Ruins",
            "Pyre of Stars",
        ),
    ),
    Planet("Athenas", ("Athenas",)),
    Planet("Slaughterstar 3000", ("Slaughterstar 3000",)),
    Planet(
        "Trials",
        (
            "Ghostlight Beacon (Cunning)",
            "Gradient of Dawn (Survival)",
            "Precipice Anchor (Discipline)",
            "Hall Obsidian (Supremacy)",
            "Skydrowned Pulpit (Fervor)",
            "Wayward Tether (Instinct)",
        ),
    ),
    Planet(
        "Takedowns",
        (
            "Midnight's Cairn",
            "Minos Prime",
        ),
    ),
    Planet(
        "Events",
        (
            "Any Map (Events)",
            "Heck Hole",
            "Villa Ultraviolet",
        ),
    ),
    Planet(
        "The Handsome Jackpot",
        (
            "Any Map (Jackpot)",
            "Grand Opening",
            "Spendopticon",
            "Impound Deluxe",
            "Compactor",
            "Jack's Secret",
            "VIP Tower",
        ),
    ),
    Planet(
        "Xylourgos",
        (
            "Skittermaw Basin",
            "Lodge",
            "Cursehaven",
            "Dustbound Archives",
            "Cankerwood",
            "Negul Neshai",
            "Heart's Desire",
        ),
    ),
    Planet(
        "Gehenna",
        (
            "Vestige",
            "Ashfall Peaks",  # This displays out of order in game ¯\_(ツ)_/¯
            "Blastplains",
            "Obsidian Forest",
            "Bloodsun Canyon",
            "Crater's Edge",
        ),
    ),
    Planet(
        "Krieg's Mind",
        (
            "Psychoscape",
            "Castle Crimson",
            "Sapphire's Run",
            "Benediction of Pain",
            "Vaulthalla",
        ),
    ),
    Planet("Stormblind Complex", ("Stormblind Complex",)),
    Planet(
        "Director's Cut",
        (
            "Darkthirst Dominion",
            "Eschaton Row",
            "Enoch's Grove",
            "Karass Canyon",
            "Scryer's Crypt",
        ),
    ),
)

# The cartel minibosses all have two bpchars each, one for next to joey, one everywhere else
# The DB only stores one, so we need to duplicate them
CARTEL_DUPLICATE_MINIBOSSES: tuple[tuple[str, str], ...] = (
    (
        "/Game/PatchDLC/Event2/Enemies/Cyber/Punk/TechLt/_Design/Character/BPChar_PunkCyberLt.BPChar_PunkCyberLt_C",
        "/Game/PatchDLC/Event2/Enemies/Cyber/Punk/TechLt/_Design/Character/BPChar_PunkCyberLt_MiniBoss.BPChar_PunkCyberLt_MiniBoss_C",
    ),
    (
        "/Game/PatchDLC/Event2/Enemies/Cyber/Trooper/Capo/_Design/Character/BPChar_CyberTrooperCapo.BPChar_CyberTrooperCapo_C",
        "/Game/PatchDLC/Event2/Enemies/Cyber/Trooper/Capo/_Design/Character/BPChar_CyberTrooperCapo_MiniBoss.BPChar_CyberTrooperCapo_MiniBoss_C",
    ),
    (
        "/Game/PatchDLC/Event2/Enemies/Meat/Punk/RoasterLT/_Design/Character/BPChar_Punk_Roaster.BPChar_Punk_Roaster_C",
        "/Game/PatchDLC/Event2/Enemies/Meat/Punk/RoasterLT/_Design/Character/BPChar_Punk_Roaster_MiniBoss.BPChar_Punk_Roaster_MiniBoss_C",
    ),
    (
        "/Game/PatchDLC/Event2/Enemies/Meat/Tink/TenderizerLt/_Design/Character/BPChar_Tink_Tenderizer.BPChar_Tink_Tenderizer_C",
        "/Game/PatchDLC/Event2/Enemies/Meat/Tink/TenderizerLt/_Design/Character/BPChar_Tink_Tenderizer_MiniBoss.BPChar_Tink_Tenderizer_MiniBoss_C",
    ),
    (
        "/Game/PatchDLC/Event2/Enemies/Tiny/Psycho/Badass/_Design/Character/BPChar_PsychoBadassTinyEvent2.BPChar_PsychoBadassTinyEvent2_C",
        "/Game/PatchDLC/Event2/Enemies/Tiny/Psycho/Badass/_Design/Character/BPChar_PsychoBadassTinyEvent2_MiniBoss.BPChar_PsychoBadassTinyEvent2_MiniBoss_C",
    ),
    (
        "/Game/PatchDLC/Event2/Enemies/Tiny/Trooper/Badass/_Design/Character/BPChar_TrooperBadassTinyEvent2.BPChar_TrooperBadassTinyEvent2_C",
        "/Game/PatchDLC/Event2/Enemies/Tiny/Trooper/Badass/_Design/Character/BPChar_TrooperBadassTinyEvent2_MiniBoss.BPChar_TrooperBadassTinyEvent2_MiniBoss_C",
    ),
)

EXTRA_BALANCES_PER_MAP: dict[str, tuple[str, ...]] = {
    "Any Map": (
        "/Game/Gear/Weapons/HeavyWeapons/Torgue/_Shared/_Design/_Unique/RYNO/Balance/Balance_HW_TOR_RYNO.Balance_HW_TOR_RYNO",
    ),
    "Sanctuary": (
        "/Game/Gear/Weapons/AssaultRifles/Vladof/_Shared/_Design/_Unique/LuciansCall/Balance/Balance_AR_VLA_LuciansCall.Balance_AR_VLA_LuciansCall",
        "/Game/Gear/Weapons/Shotguns/Hyperion/_Shared/_Design/_Unique/TheButcher/Balance/Balance_SG_HYP_TheButcher.Balance_SG_HYP_TheButcher",
    ),
    "Skywell-27": (
        "/Game/Gear/Weapons/AssaultRifles/Vladof/_Shared/_Design/_Unique/LuciansCall/Balance/Balance_AR_VLA_LuciansCall.Balance_AR_VLA_LuciansCall",
        "/Game/Gear/Weapons/Shotguns/Hyperion/_Shared/_Design/_Unique/TheButcher/Balance/Balance_SG_HYP_TheButcher.Balance_SG_HYP_TheButcher",
    ),
    "Cistern of Slaughter": (
        "/Game/Gear/Weapons/HeavyWeapons/Torgue/_Shared/_Design/_Unique/Swarm/Balance/Balance_HW_TOR_Swarm.Balance_HW_TOR_Swarm",
        "/Game/Gear/Weapons/Pistols/Tediore/Shared/_Design/_Unique/BabyMaker/Balance/Balance_PS_Tediore_BabyMaker.Balance_PS_Tediore_BabyMaker",
        "/Game/Gear/Weapons/SMGs/Maliwan/_Shared/_Design/_Unique/Devoted/Balance/Balance_SM_MAL_Devoted.Balance_SM_MAL_Devoted",
    ),
    "Pyre of Stars": (
        "/Game/Gear/Weapons/HeavyWeapons/Torgue/_Shared/_Design/_Unique/Swarm/Balance/Balance_HW_TOR_Swarm.Balance_HW_TOR_Swarm",
        "/Game/Gear/Weapons/Pistols/Tediore/Shared/_Design/_Unique/BabyMaker/Balance/Balance_PS_Tediore_BabyMaker.Balance_PS_Tediore_BabyMaker",
        "/Game/Gear/Weapons/SMGs/Maliwan/_Shared/_Design/_Unique/Devoted/Balance/Balance_SM_MAL_Devoted.Balance_SM_MAL_Devoted",
    ),
    "Any Map (Events)": (
        "/Game/PatchDLC/BloodyHarvest/Gear/GrenadeMods/_Design/_Unique/FontOfDarkness/Balance/InvBalD_GM_TOR_FontOfDarkness.InvBalD_GM_TOR_FontOfDarkness",
        "/Game/PatchDLC/BloodyHarvest/Gear/Shields/_Design/_Unique/ScreamOfPain/Balance/InvBalD_Shield_ScreamOfTerror.InvBalD_Shield_ScreamOfTerror",
        "/Game/PatchDLC/BloodyHarvest/Gear/Weapons/Shotguns/Hyperion/_Shared/_Design/_Unique/Fearmonger/Balance/Balance_SG_HYP_ETech_Fearmonger.Balance_SG_HYP_ETech_Fearmonger",
        "/Game/PatchDLC/BloodyHarvest/Gear/Weapons/SniperRifles/Dahl/_Design/_Unique/Frostbolt/Balance/Balance_SR_DAL_ETech_Frostbolt.Balance_SR_DAL_ETech_Frostbolt",
        "/Game/PatchDLC/EventVDay/Gear/Weapon/_Unique/PolyAim/Balance/Balance_SM_MAL_PolyAim.Balance_SM_MAL_PolyAim",
        "/Game/PatchDLC/EventVDay/Gear/Weapon/_Unique/WeddingInvitation/Balance/Balance_SR_JAK_WeddingInvite.Balance_SR_JAK_WeddingInvite",
    ),
}
WORLD_DROP_BALANCE_PATTERNS_PER_MAP: dict[str, str] = {
    "Stormblind Complex": "/Game/PatchDLC/Ixora/Gear/%",
    "Any Map (Jackpot)": "/Game/PatchDLC/Dandelion/Gear/%",
}


def open_hunt_db() -> sqlite3.Connection:
    """
    Opens up a new empty database.

    Returns:
        A connection to the new db, with empty tables.
    """
    HUNT_DB.unlink(missing_ok=True)

    con = sqlite3.connect(f"file:{HUNT_DB}", uri=True)
    cur = con.cursor()

    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("ATTACH DATABASE ? AS uniques", (f"file:{UNIQUES_DB}?mode=ro",))
    del cur

    return con


def find_uniques_item_id(con: sqlite3.Connection, name: str) -> int:
    """
    Finds an item in the uniques db given it's name.

    Args:
        con: The database connection to use.
        name: The item name to lookup.
    Returns:
        The item's id in the uniques db.
    """
    cur = con.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            i.ID
        FROM
            uniques.Items as i
        LEFT JOIN
            uniques.Variants as v ON i.ID = v.ItemID
        WHERE
            trim(i.Name) = ?
            or trim(v.VariantName) = ?
        """,
        (name, name),
    )
    rows = cur.fetchall()
    assert len(rows) == 1

    return rows[0][0]


def format_item_description(
    con: sqlite3.Connection,
    uniques_item_id: int,
    base_description: str,
    points: int,
) -> str:
    """
    Formats the basic item description from the hunt sheet into the full description for use ingame.

    Args:
        con: The database connection to use.
        uniques_item_id: The item id in the uniques database.
        base_description: The basic item description from the sheet.
        points: How many points this item is worth.
    Return:
        The formatted description.
    """
    cur = con.cursor()

    rarity_colour = ""
    for prefix, prefix_colour in RARITY_COLOURS:
        if base_description.startswith(prefix):
            rarity_colour = prefix_colour
            break
    assert rarity_colour != ""

    formatted_description = (
        f"<font color='{rarity_colour}'>{base_description}</font>\n"
        f"<font color='{POINT_COLOUR}'>{points}</font> points\n"
    )

    cur.execute(
        """
        SELECT
            COUNT(*)
        FROM
            uniques.ObtainedFrom as o
        INNER JOIN
            uniques.Sources as s ON o.SourceID = s.ID
        WHERE
            o.ItemID = ?
            and s.SourceType = "World Drop"
        """,
        (uniques_item_id,),
    )
    if cur.fetchone()[0] > 0:
        formatted_description += "Can World Drop\n"

    formatted_description += "\nCollectable from:\n- TODO\n"

    return formatted_description


if __name__ == "__main__":
    con = open_hunt_db()
    cur = con.cursor()

    cur.execute(
        """
        CREATE TABLE MetaData (
            Key   TEXT NOT NULL UNIQUE,
            Value TEXT NOT NULL
        )
        """,
    )
    cur.execute(
        """
        INSERT INTO
            MetaData (Key, Value)
        VALUES
            ("Version", "1"),
            ("GeneratedTime", datetime())
        """,
    )

    cur.execute(
        """
        CREATE TABLE Maps (
            ID        INTEGER NOT NULL UNIQUE,
            Name      TEXT NOT NULL UNIQUE,
            WorldName TEXT UNIQUE,
            PRIMARY KEY(ID AUTOINCREMENT)
        )
        """,
    )
    cur.execute(
        """
        INSERT INTO
            Maps (Name, WorldName)
        SELECT
            Name,
            ObjectName
        FROM
            uniques.Maps
        """,
    )
    # Fix a few cases of bad capitalization, which'd break the "current map" option
    for correction in (
        ("DesertVault_P", "Desertvault_P"),
        ("SacrificeBoss_P", "SacrificeBoss_p"),
        ("NekroMystery_P", "NekroMystery_p"),
    ):
        cur.execute(
            """
            UPDATE
                Maps
            SET
                WorldName = ?
            WHERE
                WorldName = ?
            """,
            correction,
        )
    # Add our dummy any world maps
    cur.execute(
        """
        INSERT INTO
            Maps (Name, WorldName)
        VALUES
            ("Any Map", NULL),
            ("Any Map (Jackpot)", NULL),
            ("Any Map (Events)", NULL)
        """,
    )

    cur.execute(
        """
        CREATE TABLE Planets (
            ID   INTEGER NOT NULL UNIQUE,
            Name TEXT NOT NULL UNIQUE,
            PRIMARY KEY(ID AUTOINCREMENT)
        )
        """,
    )
    for planet in OPTIONS_LAYOUT:
        cur.execute("INSERT INTO Planets(Name) VALUES (?)", (planet.name,))

    cur.execute(
        """
        CREATE TABLE Items (
            ID          INTEGER NOT NULL UNIQUE,
            Name        TEXT NOT NULL UNIQUE,
            Description TEXT NOT NULL,
            Points      INTEGER NOT NULL,
            Balance     TEXT NOT NULL UNIQUE,
            PRIMARY KEY(ID AUTOINCREMENT)
        )
        """,
    )

    # Use the hunt sheet as the canonical source of what items are included
    known_items: set[str] = set()
    with HUNT_SHEET.open(encoding="utf8") as file:
        for name, description, _source, _marker, points, _up, *_ in csv.reader(file):
            # Skip headers
            if description in ("", "Description"):
                continue

            # There are some non-breaking spaces in the sheet download, normalize them
            name = name.replace("\u00A0", " ")
            description = description.replace("\u00A0", " ")

            points = int(points)

            if name in known_items:
                continue
            known_items.add(name)

            uniques_item_id = find_uniques_item_id(con, name.split(" / ")[0])

            cur.execute(
                """
                INSERT INTO
                    Items (Name, Description, Points, Balance)
                VALUES (
                    ?,
                    ?,
                    ?,
                    (SELECT ObjectName FROM uniques.Items as i WHERE i.ID = ?)
                )
                """,
                (
                    name,
                    format_item_description(con, uniques_item_id, description, points),
                    points,
                    uniques_item_id,
                ),
            )

    cur.execute(
        """
        CREATE TABLE Collected (
            ID          INTEGER NOT NULL UNIQUE,
            ItemID      INTEGER NOT NULL UNIQUE,
            CollectTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(ID AUTOINCREMENT),
            FOREIGN KEY(ItemID) REFERENCES Items(ID)
        )
        """,
    )

    # When we detect a drop we have the balance and the enemy's class, hence using those two as the
    # keys here - if the two exist in this table, it's a valid drop
    # Use cascade on enemy class as we expect to change it later
    cur.execute(
        """
        CREATE TABLE Drops (
            ID          INTEGER NOT NULL UNIQUE,
            ItemBalance STRING NOT NULL,
            EnemyClass  STRING,
            PRIMARY KEY(ID AUTOINCREMENT),
            FOREIGN KEY(ItemBalance) REFERENCES Items(Balance),
            UNIQUE(ItemBalance, EnemyClass)
        )
        """,
    )
    # The uniques db guessed full object names by duplicating the last portion
    # This usually works, but for classes there's typically an extra `_C` suffix - and every enemy
    # class we care about has one, so we can unconditionally add it
    cur.execute(
        """
        INSERT INTO
            Drops (ItemBalance, EnemyClass)
        SELECT
            i.Balance,
            s.ObjectName || '_C'
        FROM
            Items as i
        INNER JOIN
            uniques.Items as ui on i.Balance = ui.ObjectName
        INNER JOIN
            uniques.ObtainedFrom as o ON ui.ID = o.ItemID
        INNER JOIN
            uniques.Sources as s ON o.SourceID = s.ID
        WHERE
            s.SourceType = 'Enemy'
            and s.ObjectName is not NULL
        """,
    )
    # Replace Dinklebot with Earl's door so we catch the Loot-o-Grams being redeemed
    cur.execute(
        """
        UPDATE
            Drops
        SET
            EnemyClass = '/Game/InteractiveObjects/GameSystemMachines/CrazyEarl/'
                         || 'BP_CrazyEarlDoor.BP_CrazyEarlDoor_C'
        WHERE
            EnemyClass = '/Game/Enemies/Oversphere/_Unique/Rare01/_Design/Character/'
                         || 'BPChar_OversphereRare01.BPChar_OversphereRare01_C'
        """,
    )
    # Duplicate the cartel minibosses
    for existing, duplicate in CARTEL_DUPLICATE_MINIBOSSES:
        cur.execute(
            """
            INSERT INTO
                Drops (ItemBalance, EnemyClass)
            SELECT
                ItemBalance,
                ?
            FROM
                Drops
            WHERE
                EnemyClass = ?
            """,
            (duplicate, existing),
        )
    # Remove The Black Rook, who is unused, and Eadric Edelhard, who is unkillable
    cur.execute(
        """
        DELETE FROM
            Drops
        WHERE
            EnemyClass IN (
                '/Alisma/Enemies/AliEnforcer/_Unique/TheBlackRook/'
                || 'BPChar_AliEnforcer_TheBlackRook.BPChar_AliEnforcer_TheBlackRook',
                '/Alisma/Enemies/HibPsycho/_Unique/TheCellNeighbor/_Design/Character/'
                || 'BPChar_HibPsycho_TheCellNeighbor.BPChar_HibPsycho_TheCellNeighbor'
            )
        """,
    )

    cur.execute(
        """
        INSERT INTO
            Drops (ItemBalance, EnemyClass)
        SELECT
            i.ObjectName,
            NULL
        FROM
            uniques.Sources as s
        INNER JOIN
            uniques.ObtainedFrom as o ON s.ID = o.SourceID
        INNER JOIN
            uniques.Items as i on o.ItemID = i.ID
        WHERE
            s.Description = 'Arms Race Chest Room'
            or (
                s.SourceType = 'World Drop'
                and NOT EXISTS (
                    SELECT
                        1
                    FROM
                        uniques.Sources as s2
                    INNER JOIN
                        uniques.ObtainedFrom as o2 ON s2.ID = o2.SourceID
                    INNER JOIN
                        uniques.Items as i2 on o2.ItemID = i2.ID
                    WHERE
                        i.ID = i2.ID
                        and s2.SourceType NOT IN (
                            'Mission',
                            'Vendor',
                            'World Drop',
                            'Diamond Chest',
                            'Eridian Fabricator'
                        )
                )
            )
        """,
    )

    # We essentially pre-join the planet and maps table into this one for more efficient lookups at
    # runtime
    cur.execute(
        """
        CREATE TABLE ItemLocations (
            ID         INTEGER NOT NULL UNIQUE,
            PlanetID   INTEGER NOT NULL,
            PlanetName TEXT NOT NULL,
            MapID      INTEGER NOT NULL,
            MapName    TEXT NOT NULL,
            WorldName  TEXT,
            ItemID     INTEGER NOT NULL,
            PRIMARY KEY(ID AUTOINCREMENT),
            FOREIGN KEY(PlanetID) REFERENCES Planets(ID),
            FOREIGN KEY(PlanetName) REFERENCES Planets(Name),
            FOREIGN KEY(MapID) REFERENCES Maps(ID),
            FOREIGN KEY(MapName) REFERENCES Maps(Name),
            FOREIGN KEY(WorldName) REFERENCES Maps(WorldName),
            FOREIGN KEY(ItemID) REFERENCES Items(ID),
            UNIQUE(PlanetID, MapID, ItemID) ON CONFLICT IGNORE
        )
        """,
    )
    cur.execute(
        """
        CREATE VIEW CollectedLocations AS
        SELECT
            l.ID,
            l.PlanetID,
            l.MapID,
            l.MapName,
            l.ItemID,
            i.Points,
            EXISTS (
                SELECT 1 FROM Collected as c WHERE c.ItemID = i.ID
            ) as IsCollected
        FROM
            ItemLocations as l
        LEFT JOIN
            Items as i ON l.ItemID = i.ID
        """,
    )
    for planet in OPTIONS_LAYOUT:
        cur.execute("SELECT ID FROM Planets WHERE Name = ?", (planet.name,))
        planet_id = cur.fetchone()[0]
        for map_name in planet.maps:
            cur.execute("SELECT ID, WorldName FROM Maps WHERE Name = ?", (map_name,))
            map_id, world_name = cur.fetchone()

            cur.execute(
                """
                SELECT
                    i.ID
                FROM
                    Drops as d
                INNER JOIN
                    Items as i on d.ItemBalance = i.Balance
                INNER JOIN
                    uniques.Items as ui ON i.Balance = ui.ObjectName
                INNER JOIN
                    uniques.ObtainedFrom as o ON ui.ID = o.ItemID
                INNER JOIN
                    uniques.Sources as s ON o.SourceID = s.ID
                WHERE
                    d.EnemyClass IS NOT NULL
                    and s.SourceType = 'Enemy'
                    and s.Map = ?
                """,
                (map_name,),
            )
            map_item_ids: set[int] = {x[0] for x in cur.fetchall()}

            for bal in EXTRA_BALANCES_PER_MAP.get(map_name, ()):
                cur.execute("SELECT ID FROM Items WHERE Balance = ?", (bal,))
                map_item_ids.add(cur.fetchone()[0])

            if (bal_pattern := WORLD_DROP_BALANCE_PATTERNS_PER_MAP.get(map_name)) is not None:
                cur.execute(
                    """
                    SELECT
                        i.ID
                    FROM
                        Drops as d
                    LEFT JOIN
                        Items as i ON d.ItemBalance = i.Balance
                    WHERE
                        d.EnemyClass IS NULL
                        and i.Balance like ?
                    """,
                    (bal_pattern,),
                )
                map_item_ids |= {x[0] for x in cur.fetchall()}

            cur.execute(
                f"""
                INSERT INTO
                    ItemLocations (PlanetID, PlanetName, MapID, MapName, WorldName, ItemID)
                SELECT
                    ?, ?, ?, ?, ?, i.ID
                FROM
                    Items as i
                LEFT JOIN
                    uniques.Items as ui ON i.Balance = ui.ObjectName
                INNER JOIN
                    uniques.ObtainedFrom as o ON ui.ID = o.ItemID
                INNER JOIN
                    uniques.Sources as s ON o.SourceID = s.ID
                WHERE
                    i.ID in ({','.join(['?'] * len(map_item_ids))})
                ORDER BY
                    s.Description, i.Name
                """,
                (planet_id, planet.name, map_id, map_name, world_name, *map_item_ids),
            )

    # Again, pre-join the planet/map names
    cur.execute(
        """
        CREATE TABLE OptionsList (
            ID         INTEGER NOT NULL UNIQUE,
            PlanetID   INTEGER UNIQUE,
            PlanetName TEXT UNIQUE,
            MapID      INTEGER UNIQUE,
            MapName    TEXT UNIQUE,
            PRIMARY KEY(ID AUTOINCREMENT),
            FOREIGN KEY(PlanetID) REFERENCES Planets(ID),
            FOREIGN KEY(PlanetName) REFERENCES Planets(Name),
            FOREIGN KEY(MapID) REFERENCES Maps(ID),
            FOREIGN KEY(MapName) REFERENCES Maps(Name),
            CHECK ((PlanetID IS NULL) == (PlanetName IS NULL)),
            CHECK ((MapID IS NULL) == (MapName IS NULL)),
            CHECK ((PlanetID IS NOT NULL) != (MapID IS NOT NULL))
        )
        """,
    )

    for planet in OPTIONS_LAYOUT:
        # Firstly, discard any maps which are empty
        maps_with_items: list[str] = []
        for map_name in planet.maps:
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM ItemLocations WHERE MapName = ?)",
                (map_name,),
            )
            any_items = cur.fetchone()[0]
            if any_items:
                maps_with_items.append(map_name)

        planet_to_insert: str | None
        map_to_insert: str | None
        match len(maps_with_items):
            case 0:
                # Ignore the planet completely
                continue
            case 1:
                # Ignore the planet and just add the map straight to the options list
                planet_to_insert = None
                map_to_insert = maps_with_items[0]
            case _:
                # Add the planet to the options list
                planet_to_insert = planet.name
                map_to_insert = None

        cur.execute(
            """
            INSERT INTO
                OptionsList (PlanetID, PlanetName, MapID, MapName)
            VALUES
                (
                    (SELECT p.ID FROM Planets as p WHERE p.Name = ?),
                    ?,
                    (SELECT m.ID FROM Maps as m WHERE m.Name = ?),
                    ?
                )
            """,
            (planet_to_insert, planet_to_insert, map_to_insert, map_to_insert),
        )

    cur.execute(
        """
        SELECT
            (
                SELECT
                    COUNT(*)
                FROM
                    Items
            ),
            (
                SELECT
                    COUNT(DISTINCT ItemID)
                FROM
                    ItemLocations
            )
        """,
    )
    item_count, item_locations_item_count = cur.fetchone()
    assert item_count == item_locations_item_count
