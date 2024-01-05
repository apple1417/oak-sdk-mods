# ruff: noqa: D103

import sqlite3
from typing import Any

import unrealsdk
from mods_base import ENGINE, hook
from ui_utils import show_hud_message
from unrealsdk import logging
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .db import open_db

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

# Store inventory categories to ignore directly, which'll just do fast pointer comparisons
INV_CAT_AMMO = unrealsdk.find_object(
    "InventoryCategoryData",
    "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Ammo.InventoryCategory_Ammo",
)
INV_CAT_ERIDIUM = unrealsdk.find_object(
    "InventoryCategoryData",
    "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Eridium.InventoryCategory_Eridium",
)
INV_CAT_HEALTH = unrealsdk.find_object(
    "InventoryCategoryData",
    "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_InstantHealth.InventoryCategory_InstantHealth",
)
INV_CAT_MONEY = unrealsdk.find_object(
    "InventoryCategoryData",
    "/Game/Gear/_Shared/_Design/InventoryCategories/InventoryCategory_Money.InventoryCategory_Money",
)

PICKUP_CATEGORY_PROP = unrealsdk.find_class("InventoryItemPickup")._find("PickupCategory")


@hook(
    "/Game/Pickups/_Shared/_Design/BP_OakInventoryItemPickup.BP_OakInventoryItemPickup_C:UserConstructionScript",
)
def drop_hook(
    obj: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    if obj._get_field(PICKUP_CATEGORY_PROP) == INV_CAT_MONEY:
        return

    cached_bal_comp = obj.CachedInventoryBalanceComponent
    if cached_bal_comp is None:
        return
    balance = cached_bal_comp.InventoryBalanceData
    if balance is None:
        return

    balance_name = balance._path_name()
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
    for request in ENGINE.GameInstance.OakSingletons.SpawnLootManager.DroppedPickupRequests:
        if request.ContextActor.Class is None:
            continue
        if not any(info.InventoryBalanceData == balance for info in request.SelectedInventoryInfos):
            continue

        actor_cls = request.ContextActor.Class._path_name()
        with open_db("r") as cur:
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
                )
                """,
                (balance_name, actor_cls),
            )
            # If we found a row, it's a valid drop
            if cur.fetchone()[0]:
                valid_pickups.add(obj)
                return
        break


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

    bal = obj.CachedInventoryBalanceComponent.InventoryBalanceData._path_name()
    with open_db("w") as cur:
        try:
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
        except sqlite3.IntegrityError:
            # Already collected
            return

    with open_db("r") as cur:
        # Partly base the duration of the message on the point value, let the more valuable stuff
        # hang around a bit longer
        cur.execute(
            """
            SELECT
                Name,
                '<font color="#00ff00">+' || Points || '</font> points',
                MAX(4, MIN(8, Points))
            FROM
                Items
            WHERE
                Balance = ?
            """,
            (bal,),
        )
        name, points_message, duration = cur.fetchone()
        show_hud_message(name, points_message, duration)
        logging.info(f"HUNT: Collected {name}")


@hook("/Script/Engine.PlayerController:ServerNotifyLoadedWorld")
def world_change_hook(
    _1: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    valid_pickups.clear()
