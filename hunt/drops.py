# ruff: noqa: D103

from typing import Any

import unrealsdk
from mods_base import ENGINE, hook, html_to_plain_text
from ui_utils import show_hud_message
from unrealsdk import logging
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .db import open_db
from .native.drops import get_inventory_balance_name

"""
When an enemy dies, it's drops are added to `SpawnLootManager::DroppedPickupRequests`. This list
contains both the balance which is dropped and the reference to the enemy, it's how we detect if the
drop came from a valid source.

We can't hook on this object unfortuantly, the best time we can manage is when the item is
constructed - but the construction hook doesn't have any reference back to the enemy. We instead
iterate back through all the requests in globals to try find the request for the current item. We do
this by matching balance.

Technically, if there are multiple requests for the same balance at the same time, we might grab the
wrong one - which'd mean the other item would grab ours. If one of these was a world drop on the
opposite side of the map, theoretically this might swap them, and mark the world drop as the only
valid one. Decided this is a niche enough case we don't really care to handle it however.

Once we've detected that a drop is valid, we still want to wait for the user to actually look at it,
so we keep a reference to it to double check against on drawing an item card.
"""


valid_pickups: set[UObject] = set()

# There are some scenarios where a tonne of items get spawned very quickly
# We can quickly discard them, before doing a db query or iterating through any requests, by
# checking the drop's inventory category
# We could go more in depth, but these are the main problems categories - and adding more risks
# ignoring actual drops
INVENTORY_CATEGORIES_TO_IGNORE: set[UObject] = {
    unrealsdk.find_object(
        "InventoryCategoryData",
        "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Ammo.InventoryCategory_Ammo",
    ),
    unrealsdk.find_object(
        "InventoryCategoryData",
        "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Eridium.InventoryCategory_Eridium",
    ),
    unrealsdk.find_object(
        "InventoryCategoryData",
        "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_InstantHealth.InventoryCategory_InstantHealth",
    ),
    unrealsdk.find_object(
        "InventoryCategoryData",
        "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Money.InventoryCategory_Money",
    ),
}

PICKUP_CATEGORY_PROP = unrealsdk.find_class("InventoryItemPickup")._find("PickupCategory")


def find_matching_drop_request(balance: UObject) -> tuple[UObject, str | None] | tuple[None, None]:
    """
    Tries to find the matching drop request for the given balance.

    Args:
        balance: The balance of the item to find the drop request of.
    Returns:
        A tuple of the actor and it's extra itempool, if one was found, or a tuple of two Nones.
    """
    for request in ENGINE.GameInstance.OakSingletons.SpawnLootManager.DroppedPickupRequests:
        actor = request.ContextActor
        if actor is None or actor.Class is None:
            continue
        if not any(info.InventoryBalanceData == balance for info in request.SelectedInventoryInfos):
            continue

        try:
            bal_comp = actor.BalanceComponent
        except AttributeError:
            continue

        try:
            extra_item_pool = None if bal_comp is None else bal_comp.ExtraItemPoolToDropOnDeath
            extra_item_pool_name = None if extra_item_pool is None else extra_item_pool._path_name()
        except AttributeError:
            extra_item_pool_name = None

        return actor, extra_item_pool_name
    return None, None


@hook(
    "/Game/Pickups/_Shared/_Design/BP_OakInventoryItemPickup.BP_OakInventoryItemPickup_C:UserConstructionScript",
)
def drop_hook(
    obj: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    if obj._get_field(PICKUP_CATEGORY_PROP) in INVENTORY_CATEGORIES_TO_IGNORE:
        return

    cached_bal_comp = obj.CachedInventoryBalanceComponent
    if cached_bal_comp is None:
        return
    balance = cached_bal_comp.InventoryBalanceData
    if balance is None:
        return

    balance_name = get_inventory_balance_name(cached_bal_comp)
    with open_db("r") as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT
                    1
                FROM
                    Items
                WHERE
                    Balance = ?
            )
            """,
            (balance_name,),
        )
        # If we don't care about this balance
        if not cur.fetchone()[0]:
            return

        # Check if this is a word drop - doing this as an extra step beforehand since it avoids
        # needing to iterate through the drop requests
        cur.execute(
            """
            SELECT EXISTS (
                SELECT
                    1
                FROM
                    Drops
                WHERE
                    ItemBalance = ?
                    and EnemyClass IS NULL
            )
            """,
            (balance_name,),
        )
        # If we found a row, it's a valid world drop
        if cur.fetchone()[0]:
            valid_pickups.add(obj)
            return

        # Try find the request this item is for
        actor, extra_item_pool_name = find_matching_drop_request(balance)
        if actor is None:
            return

        actor_cls = actor.Class._path_name()
        cur.execute(
            """
            SELECT EXISTS (
                SELECT
                    1
                FROM
                    Drops
                WHERE
                    ItemBalance = ?
                    and EnemyClass = ?
                    and (
                        ExtraItemPool IS NULL
                        or ExtraItemPool = ?
                    )
            )
            """,
            (balance_name, actor_cls, extra_item_pool_name),
        )
        # If we found a row, it's a valid drop
        if cur.fetchone()[0]:
            valid_pickups.add(obj)
            return


@hook("/Script/GbxInventory.InventoryItemPickup:OnLookedAtByPlayer")
def itemcard_hook(
    obj: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    # This hook is called for both the small weapon type icon, as well as the full item card
    # OakUseComponent::PickupInteractionDistance is 450, GFxItemCard::ShowItemCardDistance is 448
    # If you look at something 449 units away, then step forward without looking away, the hook does
    # *not* get called again, so we'll use the larger value
    if args.NewUsableDistanceAway > args.InstigatingPlayer.UseComponent.PickupInteractionDistance:
        # Not viewing the full item card
        return

    try:
        valid_pickups.remove(obj)
    except KeyError:
        # Not in set
        return

    bal = get_inventory_balance_name(obj.CachedInventoryBalanceComponent)
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
            (bal,),
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
                    '<font color="#00ff00">+' || Points || '</font> points'
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
            (bal,),
        )
        title, message, duration = cur.fetchone()
        show_hud_message(title, message, duration)
        logging.info(html_to_plain_text(f"[HUNT] {title}: {message}"))


@hook("/Script/Engine.PlayerController:ServerNotifyLoadedWorld")
def world_change_hook(
    _1: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    valid_pickups.clear()
