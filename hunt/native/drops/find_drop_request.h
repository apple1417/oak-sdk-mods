#ifndef HUNT_NATIVE_DROPS_DROP_REQUESTS_H
#define HUNT_NATIVE_DROPS_DROP_REQUESTS_H

#include "pyunrealsdk/pch.h"

namespace unrealsdk::unreal {

class UObject;

}

namespace hunt::drops {

/**
 * @brief Tries to find the matching drop request for the given balance.
 *
 * @param balance The balance of the item to find the drop request of.
 * @return A tuple of the actor and it's extra itempool, if found.
 */
std::optional<std::pair<unrealsdk::unreal::UObject*, std::optional<std::wstring>>>
find_matching_drop_request(unrealsdk::unreal ::UObject* balance);

}  // namespace hunt::drops

#endif /* HUNT_NATIVE_DROPS_DROP_REQUESTS_H */
