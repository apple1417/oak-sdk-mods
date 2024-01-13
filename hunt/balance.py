import unrealsdk
from unrealsdk.unreal import UObject

from .db import open_db

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

# root balance : part : expanded balance name
EXPANDABLE_BALANCE_DATA: dict[UObject, dict[UObject, str]] = {}

with open_db("r") as cur:
    cur.execute("SELECT RootBalance, Part, ExpandedBalance FROM ExpandableBalances")
    for root_balance, part, expanded_balance in cur.fetchall():
        root_obj = unrealsdk.find_object("InventoryBalanceData", root_balance)
        part_obj = unrealsdk.find_object("InventoryPartData", part)

        if root_obj not in EXPANDABLE_BALANCE_DATA:
            EXPANDABLE_BALANCE_DATA[root_obj] = {}
        EXPANDABLE_BALANCE_DATA[root_obj][part_obj] = expanded_balance


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
