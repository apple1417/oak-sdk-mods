#include "pyunrealsdk/pch.h"
#include "unrealsdk/hook_manager.h"
#include "unrealsdk/unreal/classes/properties/uboolproperty.h"
#include "unrealsdk/unreal/classes/uclass.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/wrappers/bound_function.h"
#include "unrealsdk/unreal/wrappers/weak_pointer.h"
#include "unrealsdk/unrealsdk.h"

#include "coop.h"
#include "hooks.h"

using namespace unrealsdk::unreal;

namespace hunt::drops::coop {

namespace {

const constexpr std::wstring_view HOOK_ID = L"hunt_drops_coop";

/*
All drops are created on the host. Even with instanced loot, the host creates it, and just sets some
flag for who sees it, and the object is only transmitted to that player. So all our valid drop
detection code works perfectly fine - but only on the host. We need to transmit which drops are
valid to clients, so that they can run the itemcard hook and add to the local client's db.

Now the way we transmit this information is quite stupid. With experimentation, I found this pair of
functions:
- `OakInventoryItemPickup::SetNoLootBeam`
- `OakInventoryItemPickup::OnRep_NoLootBeam`

Toggling the loot beam state using the former on the host, calls the latter on clients. And this
pair also has the really nice property of being directly on the pickup, meaning the engine
automatically deals with associating the host/client versions of the object - it's non trivial to do
so out of band, even the names can differ.

Now a problem with these functions is false positives, these are probably called somewhere normally.
To do this we just toggle it a bunch of times, that probably doesn't happen. We can detect when a
drop gets constructed on client using `InventoryItemPickup:OnRep_PickupActorClientSpawnData`, and
simply look for enough toggles within the first few seconds. We do need a delay, toggling the beam
twice in a row during the same tick does not send any information to the client.

The other main probelem with using this pair of functions is of course that it visually toggles the
loot beam. There are  other function pairs that might avoid this, however they all have their own
downsides too. For example, `InventoryItemPickup::ActivatePickup` and
`InventoryItemPickup::DeactivatePickup` call `InventoryItemPickup::OnRep_IsActive` on the client,
but risk us leaving the pickup deactivated, meaning you can't pick it up or look at the card. There
are also several options on `Actor` - but that's a very fundamental base class which will trigger a
lot of hooks on unrelated objects, which has performance impacts.

Instead, we simply accept that the beam will blink for a bit - since it only happens on valid drops
it's almost a feature.
*/

const constexpr auto BLINK_INTERVAL = std::chrono::milliseconds(100);
const constexpr auto REQUIRED_BLINK_THRESHOLD = 5;

uint32_t total_blink_count = 20;  // NOLINT(readability-magic-numbers)

struct HostUpcomingBlink {
    // Need to use weak pointers since we dereference this, and the object might get picked up and
    // destroyed between updates
    WeakPointer obj;
    uint32_t remaining_blinks;
};
std::vector<HostUpcomingBlink> host_upcoming_blinks{};

struct ClientSeenBlink {
    uint32_t seen_blinks{};
    std::chrono::steady_clock::time_point timeout;
};
// It's safe to use a raw pointer here since we never dereference it, we only check if the pointer
// we get from a hook (which we know is valid) is contained within it.
std::unordered_map<UObject*, ClientSeenBlink> client_seen_blinks{};

std::mutex blinky_mutex{};
std::condition_variable wake_blinky_thread{};

// When set, the blinky thread will terminate as soon as possible after
// Should also set `wake_blinky_thread` after
std::atomic<bool> stop_blinky = false;

/**
 * @brief Checks if the blinky thread needs to be actively running.
 *
 * @return True if it needs to be running.
 */
bool need_blinky_thread_running(void) {
    return !host_upcoming_blinks.empty() || !client_seen_blinks.empty() || stop_blinky;
};

void blinky_thread(void) {
    SetThreadDescription(GetCurrentThread(), L"hunt tracker blinky");

    while (true) {
        // Deep sleep while there's nothing in the list
        std::unique_lock<std::mutex> lock(blinky_mutex);
        if (!need_blinky_thread_running()) {
            wake_blinky_thread.wait(lock, &need_blinky_thread_running);
        }
        if (stop_blinky) {
            stop_blinky = false;
            return;
        }

        // "Polling" loop until we're allowed to sleep again
        while (need_blinky_thread_running()) {
            // Slight abuse of std::erase_if: since it must visit every element, we use it to blink
            // all valid ones at the same time as we remove all invalid ones
            std::erase_if(
                host_upcoming_blinks, [](decltype(host_upcoming_blinks)::value_type& entry) {
                    // Remove anything where the pointer's been invalidated
                    auto obj = *entry.obj;
                    if (obj == nullptr) {
                        return true;
                    }

                    static auto set_no_loot_beam_func =
                        obj->Class->find_func_and_validate(L"SetNoLootBeam"_fn);
                    static auto no_loot_beam_prop =
                        obj->Class->find_prop_and_validate<UBoolProperty>(L"bNoLootBeam"_fn);

                    // Remove anything which's used all blinks
                    if (entry.remaining_blinks == 0) {
                        // Make sure the beam's definitely on now
                        BoundFunction{.func = set_no_loot_beam_func, .object = obj}
                            .call<void, UBoolProperty>(false);
                        return true;
                    }
                    entry.remaining_blinks--;

                    // Toggle the beam, and keep this entry
                    BoundFunction{.func = set_no_loot_beam_func, .object = obj}
                        .call<void, UBoolProperty>(!obj->get<UBoolProperty>(no_loot_beam_prop));
                    return false;
                });

            // From the client map, all we do is remove entries which have timed out.
            auto now = std::chrono::steady_clock::now();
            std::erase_if(client_seen_blinks,
                          [now](decltype(client_seen_blinks)::value_type& entry) {
                              return entry.second.timeout < now;
                          });

            if (need_blinky_thread_running()) {
                // Sleep one interval, until we next need to blink again
                lock.unlock();
                std::this_thread::sleep_for(BLINK_INTERVAL);
                lock.lock();
            }

            if (stop_blinky) {
                stop_blinky = false;
                return;
            }
        }
    }
}

const constexpr std::wstring_view CLIENT_CONSTRUCT_HOOK_FUNC_NAME =
    L"/Script/GbxInventory.InventoryItemPickup:OnRep_PickupActorClientSpawnData";

bool client_construct_hook(unrealsdk::hook_manager::Details& details) {
    const std::lock_guard<std::mutex> lock(blinky_mutex);
    client_seen_blinks.emplace(
        std::piecewise_construct, std::forward_as_tuple(details.obj),
        std::forward_as_tuple(
            0, std::chrono::steady_clock::now() + (BLINK_INTERVAL * total_blink_count)));
    return false;
}

const constexpr std::wstring_view CLIENT_BLINKY_HOOK_FUNC_NAME =
    L"/Script/OakGame.OakInventoryItemPickup:OnRep_NoLootBeam";

bool client_blinky_hook(unrealsdk::hook_manager::Details& details) {
    const std::lock_guard<std::mutex> lock(blinky_mutex);
    auto iter = client_seen_blinks.find(details.obj);
    if (iter == client_seen_blinks.end()) {
        return false;
    }

    iter->second.seen_blinks++;
    if (iter->second.seen_blinks > REQUIRED_BLINK_THRESHOLD) {
        mark_valid_drop(details.obj);
        client_seen_blinks.erase(iter);
    }

    return false;
}

}  // namespace

void transmit_valid_pickup_to_clients(UObject* pickup) {
    // No sense continuing if we have no blinks set
    if (total_blink_count == 0) {
        return;
    }

    {
        const std::lock_guard<std::mutex> lock(blinky_mutex);
        host_upcoming_blinks.emplace_back(pickup, total_blink_count);
    }
    wake_blinky_thread.notify_all();
}

void reset_state_on_world_change(void) {
    const std::lock_guard<std::mutex> lock(blinky_mutex);
    host_upcoming_blinks.clear();
    client_seen_blinks.clear();
}

void enable(void) {
    unrealsdk::hook_manager::add_hook(CLIENT_CONSTRUCT_HOOK_FUNC_NAME,
                                      unrealsdk::hook_manager::Type::PRE, HOOK_ID,
                                      client_construct_hook);
    unrealsdk::hook_manager::add_hook(CLIENT_BLINKY_HOOK_FUNC_NAME,
                                      unrealsdk::hook_manager::Type::PRE, HOOK_ID,
                                      client_blinky_hook);

    std::thread(blinky_thread).detach();
}

void disable(void) {
    unrealsdk::hook_manager::remove_hook(CLIENT_CONSTRUCT_HOOK_FUNC_NAME,
                                         unrealsdk::hook_manager::Type::PRE, HOOK_ID);
    unrealsdk::hook_manager::remove_hook(CLIENT_BLINKY_HOOK_FUNC_NAME,
                                         unrealsdk::hook_manager::Type::PRE, HOOK_ID);

    stop_blinky = true;
    wake_blinky_thread.notify_all();
}

void set_blink_count(uint32_t num_blinks) {
    total_blink_count = num_blinks;
}

}  // namespace hunt::drops::coop
