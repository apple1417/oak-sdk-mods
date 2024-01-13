#!/usr/bin/env python
import csv
import sqlite3
from collections.abc import Iterator
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

TRUE_TRIAL_EXTRA_DROPS: tuple[tuple[str, str], ...] = (
    (
        "/Game/PatchDLC/Geranium/Gear/Weapon/_Unique/Flipper/Balance/Balance_SM_MAL_Flipper.Balance_SM_MAL_Flipper",
        "/Game/Enemies/Mech/_Unique/TrialBoss/_Design/Character/BPChar_Mech_TrialBoss.BPChar_Mech_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Mayhem2/Gear/Weapon/_Shared/_Unique/Kaoson/Balance/Balance_SM_DAHL_Kaoson.Balance_SM_DAHL_Kaoson",
        "/Game/Enemies/Mech/_Unique/TrialBoss/_Design/Character/BPChar_Mech_TrialBoss.BPChar_Mech_TrialBoss_C",
    ),
    (
        "/Game/Gear/Weapons/Pistols/Jakobs/_Shared/_Design/_Unique/Maggie/Balance/Balance_PS_JAK_Maggie.Balance_PS_JAK_Maggie",
        "/Game/Enemies/Goon/_Unique/TrialBoss/_Design/Character/BPChar_Goon_TrialBoss.BPChar_Goon_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Alisma/Gear/Weapon/_Unique/Convergence/Balance/Balance_SG_HYP_Convergence.Balance_SG_HYP_Convergence",
        "/Game/Enemies/Goon/_Unique/TrialBoss/_Design/Character/BPChar_Goon_TrialBoss.BPChar_Goon_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Ixora2/Gear/Weapons/_Unique/Replay/Balance/Balance_PS_ATL_Replay.Balance_PS_ATL_Replay",
        "/Game/Enemies/Guardian/_Unique/TrialBoss/_Design/Character/BPChar_Guardian_TrialBoss.BPChar_Guardian_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Mayhem2/Gear/Weapon/_Shared/_Unique/Monarch/Balance/Balance_AR_VLA_Monarch.Balance_AR_VLA_Monarch",
        "/Game/Enemies/Guardian/_Unique/TrialBoss/_Design/Character/BPChar_Guardian_TrialBoss.BPChar_Guardian_TrialBoss_C",
    ),
    (
        "/Game/Gear/Weapons/Shotguns/Torgue/_Shared/_Design/_Unique/TheLob/Balance/Balance_SG_Torgue_ETech_TheLob.Balance_SG_Torgue_ETech_TheLob",
        "/Game/Enemies/Skag/_Unique/TrialBoss/_Design/Character/BPChar_Skag_TrialBoss.BPChar_Skag_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Dandelion/Gear/Weapon/_Unique/Lucky7/Balance/Balance_PS_JAK_Lucky7.Balance_PS_JAK_Lucky7",
        "/Game/Enemies/Skag/_Unique/TrialBoss/_Design/Character/BPChar_Skag_TrialBoss.BPChar_Skag_TrialBoss_C",
    ),
    (
        "/Game/Gear/Weapons/AssaultRifles/Vladof/_Shared/_Design/_Unique/Sickle/Balance/Balance_AR_VLA_Sickle.Balance_AR_VLA_Sickle",
        "/Game/Enemies/Tink/_Unique/TrialBoss/_Design/Character/BPChar_Tink_TrialBoss.BPChar_Tink_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Hibiscus/Gear/Weapon/_Unique/Skullmasher/Balance/Balance_SR_JAK_Skullmasher.Balance_SR_JAK_Skullmasher",
        "/Game/Enemies/Tink/_Unique/TrialBoss/_Design/Character/BPChar_Tink_TrialBoss.BPChar_Tink_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Ixora/Gear/Weapons/_Unique/Tizzy/Balance/Balance_PS_COV_Tizzy.Balance_PS_COV_Tizzy",
        "/Game/Enemies/Saurian/_Unique/TrialBoss/_Design/Character/BPChar_Saurian_TrialBoss.BPChar_Saurian_TrialBoss_C",
    ),
    (
        "/Game/PatchDLC/Mayhem2/Gear/Weapon/_Shared/_Unique/Backburner/Balance/Balance_HW_VLA_ETech_BackBurner.Balance_HW_VLA_ETech_BackBurner",
        "/Game/Enemies/Saurian/_Unique/TrialBoss/_Design/Character/BPChar_Saurian_TrialBoss.BPChar_Saurian_TrialBoss_C",
    ),
)

MISSION_TOKEN_REWARDS: tuple[tuple[str, int, int], ...] = (
    (
        "/Game/Missions/Plot/Mission_Ep23_TyreenFinalBoss.Mission_Ep23_TyreenFinalBoss_C",
        2,
        20,
    ),
    (
        "/Game/PatchDLC/Dandelion/Missions/Plot/Mission_DLC1_Ep07_TheHeist.Mission_DLC1_Ep07_TheHeist_C",
        1,
        7,
    ),
    (
        "/Game/PatchDLC/Hibiscus/Missions/Plot/EP06_DLC2.EP06_DLC2_C",
        1,
        7,
    ),
    (
        "/Game/PatchDLC/Geranium/Missions/Plot/Mission_Ep05_Crater.Mission_Ep05_Crater_C",
        1,
        5,
    ),
    (
        "/Game/PatchDLC/Alisma/Missions/Plot/ALI_EP05.ALI_EP05_C",
        1,
        5,
    ),
    (
        "/Game/PatchDLC/Ixora2/Missions/Side/Mission_Ixora_Main04.Mission_Ixora_Main04_C",
        1,
        3,
    ),
)

CRAZY_EARL_DOOR: (
    str
) = "/Game/InteractiveObjects/GameSystemMachines/CrazyEarl/BP_CrazyEarlDoor.BP_CrazyEarlDoor_C"

ENEMY_NAME_OVERRIDES: dict[str, str | None] = {
    "Crawly, Cybil": "Cybil Crawly",
    "Crawly, Edie": "Edie Crawly",
    "Crawly, Martha": "Martha Crawly",
    "Crawly, Matty": "Matty Crawly",
    "Ipswitch Dunne (v1)": "Ipswitch Dunne",
    "Ipswitch Dunne (v2)": None,
    "Power Troopers - Black": "Black Power Troopers",
    "Power Troopers - Blue": "Blue Power Troopers",
    "Power Troopers - Pink": "Pink Power Troopers",
    "Power Troopers - Red": "Red Power Troopers",
    "Power Troopers - Yellow": "Yellow Power Troopers",
    "Psychobillies - Billy": "Billy (Psychobillies)",
    # These aren't killable so we remove them from the list
    "Eadric Edelhard": None,
    "The Black Rook": None,
}

ARMS_RACE_EXTRA_SOURCES: dict[str, str] = {
    "Eternal Flame": "Dam, WTF",
    "Binary Operator": "Dam, WTF",
    "Boogeyman": "Dam, WTF",
    "Kickcharger": "Dam, WTF",
    "Kensei": "Dreadnought Drydock",
    "Holy Grail / King Arthur's Holy Grail / Perceval's Holy Grail": "Dreadnought Drydock",
    "Deathrattle": "Dreadnought Drydock",
    "Infernal Wish": "Launch Command",
    "Beskar": "Launch Command",
    "HOT Spring / Soothing HOT Spring / Thermal HOT Spring": "Launch Command",
    "Superconducting Plasma Coil": "Madwidth Power",
    "Dark Army / Exceptional Dark Army / Exceptional Dark Army +": "Madwidth Power",
    "Spy": "Madwidth Power",
    "Gas Mask": "Plunderdome",
    "Madcap": "Plunderdome",
    "Toboggan": "Plunderdome",
    "Torrent": "Seepage and Creepage",
    "Hotfoot Teddy": "Seepage and Creepage",
    "Critical Thug / Critical Thug x2": "Seepage and Creepage",
    "Res": "Shipping Encouraged",
    "Firefly": "Shipping Encouraged",
    "Bloodstained Trickshot / Snide Trickshot": "The Hunker Bunker",
    "Fasterfied Tizzy / Moar Fasterfied Tizzy": "The Hunker Bunker",
    "3RR0R Cmdl3t": "The Hunker Bunker",
}


@dataclass
class SourceRestrictionData:
    item_names: tuple[str, ...]
    restriction: str


COMMON_SOURCE_RESTRICTIONS: tuple[SourceRestrictionData, ...] = (
    SourceRestrictionData(
        (
            "Polyaimourous",
            "Wedding Invitation",
        ),
        " <font color='#9900FF'>[L72]</font>",
    ),
    SourceRestrictionData(
        (
            "Antifreeze",
            "Crader's EM-P5",
            "Good Juju",
            "Juliet's Dazzle",
            "R4kk P4k",
            "Raging Bear",
            "S3RV-80S-EXECUTE",
            "Spiritual Driver",
            "Tankman's Shield",
            "Vosk's Deathgrip",
            "Zheitsev's Eruption",
        ),
        " <font color='#FF0000'>[M4]</font>",
    ),
    SourceRestrictionData(
        (
            "Backburner",
            "D.N.A.",
            "Kaoson",
            "Multi-tap",
            "Plaguebearer",
            "Reflux",
            "Sand Hawk",
            "The Monarch",
        ),
        " <font color='#FF0000'>[M6]</font>",
    ),
)

# The true trial restrictions should overwrite the basic ones
# In theory they could happen at the same time, but gearbox didn't mayhem restrict them
TRUE_TRIAL_RESTRICTION: str = " <font color='#008000'>[TT]</font>"
TRUE_TRIAL_RESTRICTION_NAMES: tuple[tuple[str, str], ...] = (
    ("Boom Sickle / Sickle", "Tink of Cunning"),
    ("Skullmasher", "Tink of Cunning"),
    ("Lucky 7", "Skag of Survival"),
    ("The Lob", "Skag of Survival"),
    ("Flipper", "Arbalest of Discipline"),
    ("Kaoson", "Arbalest of Discipline"),
    ("Atlas Replay", "Sera of Supremacy"),
    ("The Monarch", "Sera of Supremacy"),
    ("Convergence", "Hag of Fervor"),
    ("Maggie", "Hag of Fervor"),
    ("Backburner", "Tyrant of Instinct"),
    ("Fasterfied Tizzy / Moar Fasterfied Tizzy", "Tyrant of Instinct"),
)

EXPANDABLE_BALANCE_DATA: dict[str, dict[str, str]] = {
    (
        "/Game/Gear/Artifacts/_Design/BalanceDefs/InvBalD_Artifact_05_Legendary.InvBalD_Artifact_05_Legendary"
    ): {
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Slide/SplatterGun/Artifact_Part_Ability_SplatterGun.Artifact_Part_Ability_SplatterGun"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/SplatterGun/InvBalD_Artifact_SplatterGun.InvBalD_Artifact_SplatterGun"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Misc/MoxxisEndowment/Artifact_Part_Ability_MoxxisEndowment.Artifact_Part_Ability_MoxxisEndowment"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/MoxxisEndowment/InvBalD_Artifact_MoxxisEndowment.InvBalD_Artifact_MoxxisEndowment"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Misc/OttoIdol/Artifact_Part_Ability_OttoIdol.Artifact_Part_Ability_OttoIdol"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/OttoIdol/InvBalD_Artifact_OttoIdol.InvBalD_Artifact_OttoIdol"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Melee/CommanderPlanetoid/Artifact_Part_Ability_CommanderPlanetoid.Artifact_Part_Ability_CommanderPlanetoid"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/CommanderPlanetoid/InvBalD_Artifact_CommanderPlanetoid.InvBalD_Artifact_CommanderPlanetoid"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Slam/PullOutMethod/Artifact_Part_Ability_PullOutMethod.Artifact_Part_Ability_PullOutMethod"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/PullOutMethod/InvBalD_Artifact_PullOutMethod.InvBalD_Artifact_PullOutMethod"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Slide/StaticTouch/Artifact_Part_Ability_StaticTouch.Artifact_Part_Ability_StaticTouch"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/StaticTouch/InvBalD_Artifact_StaticTouch.InvBalD_Artifact_StaticTouch"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Misc/LoadedDice/Artifact_Part_Ability_LoadedDice.Artifact_Part_Ability_LoadedDice"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/LoadedDice/InvBalD_Artifact_LoadedDice.InvBalD_Artifact_LoadedDice"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Melee/WhiteElephant/Artifact_Part_Ability_WhiteElephant.Artifact_Part_Ability_WhiteElephant"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/WhiteElephant/InvBalD_Artifact_WhiteElephant.InvBalD_Artifact_WhiteElephant"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Slide/RocketBoots/Artifact_Part_Ability_RocketBoots.Artifact_Part_Ability_RocketBoots"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/RocketBoots/InvBalD_Artifact_RocketBoots.InvBalD_Artifact_RocketBoots"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Misc/Deathless/Artifact_Part_Ability_Deathless.Artifact_Part_Ability_Deathless"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/Deathless/InvBalD_Artifact_Deathless.InvBalD_Artifact_Deathless"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Misc/VictoryRush/Artifact_Part_Ability_VictoryRush.Artifact_Part_Ability_VictoryRush"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/VictoryRush/InvBalD_Artifact_VictoryRush.InvBalD_Artifact_VictoryRush"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Slam/CosmicCrater/Artifact_Part_Ability_CosmicCrater.Artifact_Part_Ability_CosmicCrater"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/CosmicCrater/InvBalD_Artifact_CosmicCrater.InvBalD_Artifact_CosmicCrater"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Slam/Salvo/Artifact_Part_Ability_Salvo.Artifact_Part_Ability_Salvo"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/Salvo/InvBalD_Artifact_Salvo.InvBalD_Artifact_Salvo"
        ),
        (
            "/Game/Gear/Artifacts/_Design/PartSets/Abilities/_Legendary/Slam/Safegaurd/Artifact_Part_Ability_Safegaurd.Artifact_Part_Ability_Safegaurd"
        ): (
            "/Game/PatchDLC/Raid1/Gear/Artifacts/Safegaurd/InvBalD_Artifact_Safegaurd.InvBalD_Artifact_Safegaurd"
        ),
    },
    (
        "/Game/Gear/ClassMods/_Design/BalanceDefs/InvBalD_ClassMod_Beastmaster_05_Legendary.InvBalD_ClassMod_Beastmaster_05_Legendary"
    ): {
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Beastmaster/_Unique/Beastmaster_Unique_01/ClassMod_Part_Beastmaster_Unique_01_Friendbot.ClassMod_Part_Beastmaster_Unique_01_Friendbot"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/BeastMaster/InvBalD_ClassMod_Beastmaster_FriendBot.InvBalD_ClassMod_Beastmaster_FriendBot"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Beastmaster/_Unique/Beastmaster_Unique_02/ClassMod_Part_Beastmaster_Unique_02_CosmicStalker.ClassMod_Part_Beastmaster_Unique_02_CosmicStalker"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/BeastMaster/InvBalD_ClassMod_Beastmaster_CosmicStalker.InvBalD_ClassMod_Beastmaster_CosmicStalker"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Beastmaster/_Unique/Beastmaster_Unique_03/ClassMod_Part_Beastmaster_Unique_03_BountyHunter.ClassMod_Part_Beastmaster_Unique_03_BountyHunter"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/BeastMaster/InvBalD_ClassMod_Beastmaster_BountyHunter.InvBalD_ClassMod_Beastmaster_BountyHunter"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Beastmaster/_Unique/Beastmaster_Unique_04/ClassMod_Part_Beastmaster_Unique_04_DE4DEYE.ClassMod_Part_Beastmaster_Unique_04_DE4DEYE"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/BeastMaster/InvBalD_ClassMod_Beastmaster_DE4DEYE.InvBalD_ClassMod_Beastmaster_DE4DEYE"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Beastmaster/_Unique/Beastmaster_Unique_05/ClassMod_Part_Beastmaster_Unique_05_RakkCommander.ClassMod_Part_Beastmaster_Unique_05_RakkCommander"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/BeastMaster/InvBalD_ClassMod_Beastmaster_RakkCommander.InvBalD_ClassMod_Beastmaster_RakkCommander"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Beastmaster/_Unique/Beastmaster_Unique_06/ClassMod_Part_Beastmaster_Unique_06_RedFang.ClassMod_Part_Beastmaster_Unique_06_RedFang"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/BeastMaster/InvBalD_ClassMod_Beastmaster_RedFang.InvBalD_ClassMod_Beastmaster_RedFang"
        ),
    },
    (
        "/Game/Gear/ClassMods/_Design/BalanceDefs/InvBalD_ClassMod_Gunner_05_Legendary.InvBalD_ClassMod_Gunner_05_Legendary"
    ): {
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Gunner/_Unique/Unique_01/ClassMod_Part_Gunner_Unique_01_Rocketeer.ClassMod_Part_Gunner_Unique_01_Rocketeer"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Gunner/InvBalD_ClassMod_Gunner_Rocketeer.InvBalD_ClassMod_Gunner_Rocketeer"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Gunner/_Unique/Unique_02/ClassMod_Part_Gunner_Unique_02_ColdBlooded.ClassMod_Part_Gunner_Unique_02_ColdBlooded"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Gunner/InvBalD_ClassMod_Gunner_BloodLetter.InvBalD_ClassMod_Gunner_BloodLetter"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Gunner/_Unique/Unique_03/ClassMod_Part_Gunner_Unique_03.ClassMod_Part_Gunner_Unique_03"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Gunner/InvBalD_ClassMod_Gunner_MindSweeper.InvBalD_ClassMod_Gunner_MindSweeper"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Gunner/_Unique/Unique_04/ClassMod_Part_Gunner_Unique_04.ClassMod_Part_Gunner_Unique_04"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Gunner/InvBalD_ClassMod_Gunner_BearTrooper.InvBalD_ClassMod_Gunner_BearTrooper"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Gunner/_Unique/Unique_05/ClassMod_Part_Gunner_Unique_05.ClassMod_Part_Gunner_Unique_05"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Gunner/InvBalD_ClassMod_Gunner_BlastMaster.InvBalD_ClassMod_Gunner_BlastMaster"
        ),
    },
    (
        "/Game/Gear/ClassMods/_Design/BalanceDefs/InvBalD_ClassMod_Operative_05_Legendary.InvBalD_ClassMod_Operative_05_Legendary"
    ): {
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Operative/_Unique/Unique_01/ClassMod_Part_Operative_Unique_01_Infiltrator.ClassMod_Part_Operative_Unique_01_Infiltrator"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Operative/InvBalD_ClassMod_Operative_Infiltrator.InvBalD_ClassMod_Operative_Infiltrator"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Operative/_Unique/Unique_02/ClassMod_Part_Operative_Unique_02_Executor.ClassMod_Part_Operative_Unique_02_Executor"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Operative/InvBalD_ClassMod_Operative_Executor.InvBalD_ClassMod_Operative_Executor"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Operative/_Unique/Unique_03/ClassMod_Part_Operative_Unique_03_Expert.ClassMod_Part_Operative_Unique_03_Expert"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Operative/InvBalD_ClassMod_Operative_Techspert.InvBalD_ClassMod_Operative_Techspert"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Operative/_Unique/Unique_04/ClassMod_Part_Operative_Unique_04_Firebrand.ClassMod_Part_Operative_Unique_04_Firebrand"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Operative/InvBalD_ClassMod_Operative_FireBrand.InvBalD_ClassMod_Operative_FireBrand"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/Operative/_Unique/Unique_05/ClassMod_Part_Operative_Unique_05_Operative.ClassMod_Part_Operative_Unique_05_Operative"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Operative/InvBalD_ClassMod_Operative_ColdWarrior.InvBalD_ClassMod_Operative_ColdWarrior"
        ),
    },
    (
        "/Game/Gear/ClassMods/_Design/BalanceDefs/InvBalD_ClassMod_Siren_05_Legendary.InvBalD_ClassMod_Siren_05_Legendary"
    ): {
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/SIren/_Unique/Unique_01/ClassMod_Part_Siren_Unique_01_Storm.ClassMod_Part_Siren_Unique_01_Storm"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Siren/InvBalD_ClassMod_Siren_Elementalist.InvBalD_ClassMod_Siren_Elementalist"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/SIren/_Unique/Unique_02/ClassMod_Part_Siren_Unique_02_Dragon.ClassMod_Part_Siren_Unique_02_Dragon"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Siren/InvBalD_ClassMod_Siren_Dragon.InvBalD_ClassMod_Siren_Dragon"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/SIren/_Unique/Unique_03/ClassMod_Part_Siren_Unique_03_Bruiser.ClassMod_Part_Siren_Unique_03_Bruiser"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Siren/InvBalD_ClassMod_Siren_Breaker.InvBalD_ClassMod_Siren_Breaker"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/SIren/_Unique/Unique_04/ClassMod_Part_Siren_Unique_04_Phasezerker.ClassMod_Part_Siren_Unique_04_Phasezerker"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Siren/InvBalD_ClassMod_Siren_Phasezerker.InvBalD_ClassMod_Siren_Phasezerker"
        ),
        (
            "/Game/Gear/ClassMods/_Design/PartSets/Part_ClassMod/SIren/_Unique/Unique_05/ClassMod_Part_Siren_Unique_05_Siren.ClassMod_Part_Siren_Unique_05_Siren"
        ): (
            "/Game/PatchDLC/Raid1/Gear/ClassMods/Siren/InvBalD_ClassMod_Siren_Nimbus.InvBalD_ClassMod_Siren_Nimbus"
        ),
    },
}


def match_source_restriction(item_name: str, enemy_name: str) -> str | None:
    """
    Checks if the given item-enemy combo has a restriction.

    Args:
        item_name: The item to check.
        enemy_name: The enemy to check.
    Returns:
        The restriction, or None if there isn't one.
    """
    restriction: str | None = None
    for restriction_data in COMMON_SOURCE_RESTRICTIONS:
        if item_name in restriction_data.item_names:
            restriction = restriction_data.restriction
            break

    if (item_name, enemy_name) in TRUE_TRIAL_RESTRICTION_NAMES:
        restriction = TRUE_TRIAL_RESTRICTION

    return restriction


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

    cur.execute("SELECT CAST(Value AS INT) FROM uniques.MetaData WHERE Key = 'Version'")
    assert cur.fetchone()[0] == 13  # noqa: PLR2004

    cur.close()
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


def iter_item_sources(con: sqlite3.Connection, item_id: int) -> Iterator[str]:
    """
    Iterates through all the sources we consider valid for an item.

    Args:
        con: The database connection to use.
        item_id: The item id.
    Yields:
        The name of each source.
    """
    cur = con.cursor()
    cur.execute("SELECT Name FROM Items WHERE ID = ?", (item_id,))
    item_name = cur.fetchone()[0]

    cur.execute(
        """
        SELECT
            d.EnemyClass,
            s.Description
        FROM
            Drops as d
        LEFT JOIN
            Items as i ON d.ItemBalance = i.Balance
        LEFT JOIN
            uniques.Sources as s ON d.EnemyClass = (s.ObjectName || '_C')
        WHERE
            i.ID = ?
        """,
        (item_id,),
    )

    world_drops_allowed = False
    for enemy_class, combined_enemy_name in cur.fetchall():
        if enemy_class is None:
            world_drops_allowed = True
            assert combined_enemy_name is None
            continue

        if enemy_class in (x[1] for x in CARTEL_DUPLICATE_MINIBOSSES):
            continue
        if enemy_class == CRAZY_EARL_DOOR:
            combined_enemy_name = "Crazy Earl (redeeming Loot-o-Gram) / Dinklebot (via Loot-o-Gram)"

        for base_enemy_name in sorted(combined_enemy_name.split(" / ")):
            enemy_name = ENEMY_NAME_OVERRIDES.get(base_enemy_name, base_enemy_name)
            if enemy_name is None:
                continue

            yield enemy_name + (match_source_restriction(item_name, enemy_name) or "")

    if item_name in ARMS_RACE_EXTRA_SOURCES:
        yield ARMS_RACE_EXTRA_SOURCES[item_name]
        yield "Heavyweight Harker"

    if world_drops_allowed:
        yield "World Drops"


def format_full_item_description(con: sqlite3.Connection, item_id: int) -> str:
    """
    Formats the info available in the database into the full item description for use in game.

    Must not be called twice on the same item.

    Args:
        con: The database connection to use.
        item_id: The item id.
    Return:
        The formatted description.
    """
    cur = con.cursor()
    cur.execute(
        """
        SELECT
            Description,
            Points
        FROM
            Items
        WHERE
            ID = ?
        """,
        (item_id,),
    )
    base_description, points = cur.fetchone()

    rarity_colour = ""
    for prefix, prefix_colour in RARITY_COLOURS:
        if base_description.startswith(prefix):
            rarity_colour = prefix_colour
            break
    assert rarity_colour

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

    formatted_description += "\nCollectable from:\n<ul>"
    for source in sorted(iter_item_sources(con, item_id)):
        formatted_description += f"<li>{source}</li>"
    formatted_description += "</ul>"

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

            # Insert the basic description for now, we'll format the full one later once we have
            # more useful info in the DB
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
                    description,
                    points,
                    uniques_item_id,
                ),
            )

    cur.execute(
        """
        CREATE TABLE Collected (
            ID          INTEGER NOT NULL UNIQUE,
            ItemID      INTEGER NOT NULL,
            CollectTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(ID AUTOINCREMENT),
            FOREIGN KEY(ItemID) REFERENCES Items(ID)
        )
        """,
    )
    cur.execute("CREATE INDEX CollectedItemIDIndex ON Collected(ItemID)")
    cur.execute(
        """
        CREATE VIEW CollectedItems AS
        SELECT
            ID,
            Name,
            Description,
            Points,
            Balance,
            (
                SELECT COUNT(*) FROM Collected as c WHERE c.ItemID = i.ID
            ) as NumCollected,
            (
                SELECT
                    CollectTime
                FROM
                    Collected
                WHERE
                    ItemID = i.ID
                ORDER BY
                    CollectTime ASC
                LIMIT 1
            ) as FirstCollectTime
        FROM
            Items as i
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
            EnemyClass = ?
        WHERE
            EnemyClass = '/Game/Enemies/Oversphere/_Unique/Rare01/_Design/Character/'
                         || 'BPChar_OversphereRare01.BPChar_OversphereRare01_C'
        """,
        (CRAZY_EARL_DOOR,),
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
    # Add the true trial drops
    for item, enemy_class in TRUE_TRIAL_EXTRA_DROPS:
        cur.execute(
            """
            INSERT INTO
                Drops (ItemBalance, EnemyClass)
            VALUES
                (?, ?)
            """,
            (item, enemy_class),
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

    # Go back and actually format the item descriptions, now that we've collected all valid sources
    cur.execute("SELECT MAX(ID) FROM Items")
    for item_id in range(1, cur.fetchone()[0] + 1):
        cur.execute(
            """
            UPDATE
                Items
            SET
                Description = ?
            WHERE
                ID = ?
            """,
            (format_full_item_description(con, item_id), item_id),
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
            (
                SELECT COUNT(*) FROM Collected as c WHERE c.ItemID = i.ID
            ) as NumCollected
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

            # Order by what's in the description after the collectable, i.e. the enemies
            cur.execute(
                f"""
                INSERT INTO
                    ItemLocations (PlanetID, PlanetName, MapID, MapName, WorldName, ItemID)
                SELECT
                    ?, ?, ?, ?, ?, i.ID
                FROM
                    Items as i
                WHERE
                    i.ID in ({','.join(['?'] * len(map_item_ids))})
                ORDER BY
                    SUBSTR(Description,
                           INSTR(Description, 'Collectable from:')),
                    i.Name
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

    cur.execute(
        """
        CREATE TABLE TokenRedeems (
            ID          INTEGER NOT NULL UNIQUE,
            CollectedID INTEGER NOT NULL UNIQUE,
            PRIMARY KEY(ID AUTOINCREMENT),
            FOREIGN KEY(CollectedID) REFERENCES Collected(ID)
        )
        """,
    )
    cur.execute(
        """
        CREATE TABLE CompletedMissions (
            ID               INTEGER NOT NULL UNIQUE,
            MissionClass     TEXT NOT NULL,
            CompleteTime     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(ID AUTOINCREMENT)
        )
        """,
    )
    cur.execute(
        """
        CREATE TABLE MissionTokens (
            ID               INTEGER NOT NULL UNIQUE,
            MissionClass     STRING NOT NULL UNIQUE,
            InitialTokens    INTEGER,
            SubsequentTokens INTEGER,
            PRIMARY KEY(ID AUTOINCREMENT)
        )
        """,
    )
    for row in MISSION_TOKEN_REWARDS:
        cur.execute(
            """
            INSERT INTO
                MissionTokens (MissionClass, InitialTokens, SubsequentTokens)
            VALUES
                (?, ?, ?)
            """,
            row,
        )
    cur.execute(
        """
        CREATE VIEW AvailableTokens AS
        SELECT
            (
                IFNULL(SUM(Tokens), 0)
                + 1
                - IFNULL((SELECT COUNT(*) FROM TokenRedeems), 0)
            )
            as Tokens
        FROM
        (
            SELECT
                CASE COUNT(*)
                    WHEN 0 THEN 0
                    WHEN 1 THEN t.InitialTokens
                    ELSE t.InitialTokens + (t.SubsequentTokens * (COUNT(*) - 1))
                END as Tokens
            FROM
                MissionTokens as t
            INNER JOIN
                CompletedMissions as c ON t.MissionClass = c.MissionClass
            GROUP BY
                t.ID
        )
        """,
    )

    # Deliberately not making map a foreign key, in case anything in our db is wrong, and we get
    # something new from the game.
    cur.execute(
        """
        CREATE TABLE SaveQuits (
            ID       INTEGER NOT NULL UNIQUE,
            Map      TEXT NOT NULL,
            Station  TEXT NOT NULL,
            QuitTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(ID AUTOINCREMENT)
        )
        """,
    )

    cur.execute(
        """
        CREATE TABLE ExpandableBalances (
            ID              INTEGER NOT NULL UNIQUE,
            RootBalance     TEXT NOT NULL,
            Part            TEXT NOT NULL,
            ExpandedBalance TEXT NOT NULL,
            PRIMARY KEY(ID AUTOINCREMENT),
            FOREIGN KEY(ExpandedBalance) REFERENCES Items(Balance)
        )
        """,
    )
    for root_balance, inner in EXPANDABLE_BALANCE_DATA.items():
        for part, expanded_balance in inner.items():
            cur.execute(
                """
                INSERT INTO
                    ExpandableBalances (RootBalance, Part, ExpandedBalance)
                VALUES
                    (?, ?, ?)
                """,
                (root_balance, part, expanded_balance),
            )

    cur.close()
    con.commit()
