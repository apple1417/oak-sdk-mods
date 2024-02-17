#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/static_py_object.h"
#include "unrealsdk/hook_manager.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/properties/uobjectproperty.h"
#include "unrealsdk/unreal/classes/uclass.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"
#include "unrealsdk/unrealsdk.h"

#include "balance.h"
#include "drop_queries.h"
#include "find_drop_request.h"

using namespace unrealsdk::unreal;

namespace hunt::drops {

namespace {

pyunrealsdk::StaticPyObject drop_callback{};

const constexpr std::wstring_view HOOK_ID = L"hunt_drops";

/*
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
*/

std::unordered_set<UObject*> valid_pickups{};

/*
There are some scenarios where a tonne of items get spawned very quickly
We can quickly discard them, before doing a db query or iterating through any requests, by checking
the drop's inventory category.
We could go more in depth, but these are the main problems categories - and adding more risks
ignoring actual drops.
*/

const std::unordered_set<UObject*> INVENTORY_CATEGORIES_TO_IGNORE{
    unrealsdk::find_object(L"InventoryCategoryData"_fn,
                           L"/Game/Gear/_Shared/_Design/InventoryCategories/"
                           L"InventoryCategory_Ammo.InventoryCategory_Ammo"),
    unrealsdk::find_object(L"InventoryCategoryData"_fn,
                           L"/Game/Gear/_Shared/_Design/InventoryCategories/"
                           L"InventoryCategory_Eridium.InventoryCategory_Eridium"),
    unrealsdk::find_object(L"InventoryCategoryData"_fn,
                           L"/Game/Gear/_Shared/_Design/InventoryCategories/"
                           L"InventoryCategory_InstantHealth.InventoryCategory_InstantHealth"),
    unrealsdk::find_object(L"InventoryCategoryData"_fn,
                           L"/Game/Gear/_Shared/_Design/InventoryCategories/"
                           L"InventoryCategory_Money.InventoryCategory_Money"),
};

const constexpr std::wstring_view DROP_HOOK_FUNC_NAME =
    L"/Game/Pickups/_Shared/_Design/"
    L"BP_OakInventoryItemPickup.BP_OakInventoryItemPickup_C:UserConstructionScript";

bool drop_hook(unrealsdk::hook_manager::Details& details) {
    static auto pickup_category_prop =
        details.obj->Class->find_prop_and_validate<UObjectProperty>(L"PickupCategory"_fn);

    if (INVENTORY_CATEGORIES_TO_IGNORE.contains(
            details.obj->get<UObjectProperty>(pickup_category_prop))) {
        return false;
    }

    static auto bal_comp_prop = details.obj->Class->find_prop_and_validate<UObjectProperty>(
        L"CachedInventoryBalanceComponent"_fn);
    auto bal_comp = details.obj->get<UObjectProperty>(bal_comp_prop);
    if (bal_comp == nullptr) {
        return false;
    }

    static auto balance_prop =
        bal_comp->Class->find_prop_and_validate<UObjectProperty>(L"InventoryBalanceData"_fn);
    auto balance = bal_comp->get<UObjectProperty>(balance_prop);
    // Not sure if this is a real thing that can happen anymore, but going to check early to skip
    // more expensive checks just in case
    if (balance == nullptr) {
        return false;
    }

    auto balance_name = balance::get_inventory_balance_name(bal_comp);

    if (!is_balance_in_db(balance_name)) {
        return false;
    }
    if (may_balance_world_drop(balance_name)) {
        valid_pickups.insert(details.obj);
    }

    // This needs to take the actual balance object, not the possibly expanded one, so that we find
    // the right request
    auto request = find_matching_drop_request(balance);
    if (!request) {
        return false;
    }
    auto actor_cls = request->first->Class->get_path_name();

    if (is_valid_drop(balance_name, actor_cls, request->second)) {
        valid_pickups.insert(details.obj);
    }

    return false;
}

const constexpr std::wstring_view ITEMCARD_HOOK_FUNC_NAME =
    L"/Script/GbxInventory.InventoryItemPickup:OnLookedAtByPlayer";

bool itemcard_hook(unrealsdk::hook_manager::Details& details) {
    /*
    This hook is called for both the small weapon type icon, as well as the full item card.
    OakUseComponent::PickupInteractionDistance is 450, GFxItemCard::ShowItemCardDistance is 448.
    If you look at something 449 units away, then step forward without looking away, the hook does
    *not* get called again, so we'll use the larger value.

    We could do `args.InstigatingPlayer.UseComponent.PickupInteractionDistance` to support moddable
    distances, but that's a niche case which is kind of annoying to follow, just going to hardcode.
    */
    const constexpr auto min_itemcard_distance = 450;

    static auto new_distance_prop =
        details.args->type->find_prop_and_validate<UFloatProperty>(L"NewUsableDistanceAway"_fn);

    if (details.args->get<UFloatProperty>(new_distance_prop) > min_itemcard_distance) {
        // Not viewing the full item card
        return false;
    }

    if (valid_pickups.erase(details.obj) == 0) {
        // Didn't erase anything, i.e. pickup wasn't in the set
        return false;
    }

    static auto bal_comp_prop = details.obj->Class->find_prop_and_validate<UObjectProperty>(
        L"CachedInventoryBalanceComponent"_fn);
    auto balance_name =
        balance::get_inventory_balance_name(details.obj->get<UObjectProperty>(bal_comp_prop));

    if (!drop_callback) {
        return false;
    }
    const py::gil_scoped_acquire gil{};
    drop_callback(balance_name);

    return false;
}

const constexpr std::wstring_view WORLD_CHANGE_HOOK_FUNC_NAME =
    L"/Script/Engine.PlayerController:ServerNotifyLoadedWorld";

bool world_change_hook(unrealsdk::hook_manager::Details& /*details*/) {
    valid_pickups.clear();
    return false;
}

}  // namespace

void enable(void) {
    unrealsdk::hook_manager::add_hook(DROP_HOOK_FUNC_NAME, unrealsdk::hook_manager::Type::PRE,
                                      HOOK_ID, drop_hook);
    unrealsdk::hook_manager::add_hook(ITEMCARD_HOOK_FUNC_NAME, unrealsdk::hook_manager::Type::PRE,
                                      HOOK_ID, itemcard_hook);
    unrealsdk::hook_manager::add_hook(WORLD_CHANGE_HOOK_FUNC_NAME,
                                      unrealsdk::hook_manager::Type::PRE, HOOK_ID,
                                      world_change_hook);
}

void disable(void) {
    unrealsdk::hook_manager::remove_hook(DROP_HOOK_FUNC_NAME, unrealsdk::hook_manager::Type::PRE,
                                         HOOK_ID);
    unrealsdk::hook_manager::remove_hook(ITEMCARD_HOOK_FUNC_NAME,
                                         unrealsdk::hook_manager::Type::PRE, HOOK_ID);
    unrealsdk::hook_manager::remove_hook(WORLD_CHANGE_HOOK_FUNC_NAME,
                                         unrealsdk::hook_manager::Type::PRE, HOOK_ID);
}

void set_drop_callback(const pyunrealsdk::StaticPyObject&& getter) {
    drop_callback = getter;
}

}  // namespace hunt::drops
