#include "pyunrealsdk/pch.h"
#include "unrealsdk/unreal/classes/uclass.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/properties/zarrayproperty.h"
#include "unrealsdk/unreal/properties/zobjectproperty.h"
#include "unrealsdk/unreal/properties/zstructproperty.h"
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
        engine->Class()->find_prop_and_validate<ZObjectProperty>(L"GameInstance"_fn);
    auto game_instance = engine->get<ZObjectProperty>(game_instance_prop);

    static const auto oak_singletons_prop =
        game_instance->Class()->find_prop_and_validate<ZObjectProperty>(L"OakSingletons"_fn);
    auto oak_singletons = game_instance->get<ZObjectProperty>(oak_singletons_prop);

    static const auto spawn_loot_manager_prop =
        oak_singletons->Class()->find_prop_and_validate<ZObjectProperty>(L"SpawnLootManager"_fn);
    auto spawn_loot_manager = oak_singletons->get<ZObjectProperty>(spawn_loot_manager_prop);

    static const auto dropped_pickup_requests_prop =
        spawn_loot_manager->Class()->find_prop_and_validate<ZArrayProperty>(
            L"DroppedPickupRequests"_fn);
    auto dropped_pickup_requests =
        spawn_loot_manager->get<ZArrayProperty>(dropped_pickup_requests_prop);

    for (size_t i = 0; i < dropped_pickup_requests.size(); i++) {
        auto request = dropped_pickup_requests.get_at<ZStructProperty>(i);

        static const auto context_actor_prop =
            request.type->find_prop_and_validate<ZObjectProperty>(L"ContextActor"_fn);
        auto actor = request.get<ZObjectProperty>(context_actor_prop);
        if (actor == nullptr) {
            continue;
        }

        static const auto selected_inv_info_prop =
            request.type->find_prop_and_validate<ZArrayProperty>(L"SelectedInventoryInfos"_fn);
        auto selected_inv_info = request.get<ZArrayProperty>(selected_inv_info_prop);

        auto found_any = false;
        for (size_t j = 0; j < selected_inv_info.size(); j++) {
            auto info = selected_inv_info.get_at<ZStructProperty>(j);

            static const auto inv_bal_prop =
                info.type->find_prop_and_validate<ZObjectProperty>(L"InventoryBalanceData"_fn);
            if (info.get<ZObjectProperty>(inv_bal_prop) == balance) {
                found_any = true;
                break;
            }
        }
        if (!found_any) {
            continue;
        }

        const UObject* bal_comp = nullptr;
        try {
            // Deliberately not using a cached property, since this does not exist on all actors
            bal_comp = actor->get<ZObjectProperty>(L"BalanceComponent"_fn);
        } catch (const std::invalid_argument&) {
            return {{actor, std::nullopt}};
        }

        if (bal_comp == nullptr) {
            return {{actor, std::nullopt}};
        }

        const UObject* extra_item_pool = nullptr;
        try {
            extra_item_pool = bal_comp->get<ZObjectProperty>(L"ExtraItemPoolToDropOnDeath"_fn);
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
