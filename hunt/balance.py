import unrealsdk
from unrealsdk.unreal import UObject

"""
Some of the legendary artifact/com balances are "expandable". Based on parts, these can roll into
one of multiple different items names. Normally we'd consider these all the same item - but in these
specific cases, each individual item also has it's own dedicated balance. The DB only contains the
dedicated balance.

Generally speaking, the dedicated balance is only for the dedicated drop (that's why they were
added), and world drops are always the generic balance. This means if we get a world drop from the
dedicated source, or if you just try redeem a world drop token, we won't match the balance and won't
count the item - which looks identical to one which would work.

To fix this, we look through the parts on the item, and map it back to the dedicated balance.
"""

_expandable_balance_data_names: dict[str, dict[str, str]] = {
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

# expandable balance : part : individual balance name
EXPANDABLE_BALANCE_DATA: dict[UObject, dict[UObject, str]] = {
    unrealsdk.find_object("InventoryBalanceData", balance): {
        unrealsdk.find_object("InventoryPartData", part): collapsed_balance
        for part, collapsed_balance in part_mappings.items()
    }
    for balance, part_mappings in _expandable_balance_data_names.items()
}


def get_inventory_balance_name(bal_comp: UObject) -> str:
    """
    Gets the name of this item's inventory balance.

    Args:
        bal_comp: The InventoryBalanceStateComponent to inspect.
    Return:
        The inventory balance's name.
    """
    bal_obj = bal_comp.InventoryBalanceData

    if bal_obj in EXPANDABLE_BALANCE_DATA:
        part_mappings = EXPANDABLE_BALANCE_DATA[bal_obj]
        for part in bal_comp.PartList:
            if part in part_mappings:
                return part_mappings[part]

    return bal_obj._path_name()
