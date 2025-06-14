#include "pyunrealsdk/pch.h"
#include "unrealsdk/unreal/classes/properties/uarrayproperty.h"
#include "unrealsdk/unreal/classes/properties/uobjectproperty.h"
#include "unrealsdk/unreal/classes/properties/ustructproperty.h"
#include "unrealsdk/unreal/classes/uclass.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/wrappers/wrapped_array.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"
#include "unrealsdk/unrealsdk.h"

#include "find_drop_request.h"

using namespace unrealsdk::unreal;

namespace hunt::drops {

std::optional<std::pair<UObject*, std::optional<std::wstring>>> find_matching_drop_request(
    UObject* balance) {
    static const UObject* engine =
        unrealsdk::find_object(L"OakGameEngine"_fn, L"/Engine/Transient.OakGameEngine_0");

    static const auto game_instance_prop =
        engine->Class()->find_prop_and_validate<UObjectProperty>(L"GameInstance"_fn);
    auto game_instance = engine->get<UObjectProperty>(game_instance_prop);

    static const auto oak_singletons_prop =
        game_instance->Class()->find_prop_and_validate<UObjectProperty>(L"OakSingletons"_fn);
    auto oak_singletons = game_instance->get<UObjectProperty>(oak_singletons_prop);

    static const auto spawn_loot_manager_prop =
        oak_singletons->Class()->find_prop_and_validate<UObjectProperty>(L"SpawnLootManager"_fn);
    auto spawn_loot_manager = oak_singletons->get<UObjectProperty>(spawn_loot_manager_prop);

    static const auto dropped_pickup_requests_prop =
        spawn_loot_manager->Class()->find_prop_and_validate<UArrayProperty>(
            L"DroppedPickupRequests"_fn);
    auto dropped_pickup_requests =
        spawn_loot_manager->get<UArrayProperty>(dropped_pickup_requests_prop);

    for (size_t i = 0; i < dropped_pickup_requests.size(); i++) {
        auto request = dropped_pickup_requests.get_at<UStructProperty>(i);

        static const auto context_actor_prop =
            request.type->find_prop_and_validate<UObjectProperty>(L"ContextActor"_fn);
        auto actor = request.get<UObjectProperty>(context_actor_prop);
        if (actor == nullptr) {
            continue;
        }

        static const auto selected_inv_info_prop =
            request.type->find_prop_and_validate<UArrayProperty>(L"SelectedInventoryInfos"_fn);
        auto selected_inv_info = request.get<UArrayProperty>(selected_inv_info_prop);

        auto found_any = false;
        for (size_t j = 0; j < selected_inv_info.size(); j++) {
            auto info = selected_inv_info.get_at<UStructProperty>(j);

            static const auto inv_bal_prop =
                info.type->find_prop_and_validate<UObjectProperty>(L"InventoryBalanceData"_fn);
            if (info.get<UObjectProperty>(inv_bal_prop) == balance) {
                found_any = true;
                break;
            }
        }
        if (!found_any) {
            continue;
        }

        UObject* bal_comp = nullptr;
        try {
            // Deliberately not using a cached property, since this does not exist on all actors
            bal_comp = actor->get<UObjectProperty>(L"BalanceComponent"_fn);
        } catch (const std::invalid_argument&) {
            return {{actor, std::nullopt}};
        }

        if (bal_comp == nullptr) {
            return {{actor, std::nullopt}};
        }

        UObject* extra_item_pool = nullptr;
        try {
            extra_item_pool = bal_comp->get<UObjectProperty>(L"ExtraItemPoolToDropOnDeath"_fn);
        } catch (const std::invalid_argument&) {
            return {{actor, std::nullopt}};
        }
        if (extra_item_pool == nullptr) {
            return {{actor, std::nullopt}};
        }

        return {{actor, extra_item_pool->get_path_name()}};
    }

    return std::nullopt;
}

}  // namespace hunt::drops
