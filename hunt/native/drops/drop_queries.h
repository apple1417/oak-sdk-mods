#ifndef HUNT_NATIVE_DROPS_DROP_QUERIES_H
#define HUNT_NATIVE_DROPS_DROP_QUERIES_H

#include "pyunrealsdk/pch.h"

namespace hunt::drops {

/**
 * @brief Checks if an item balance is included in the db.
 *
 * @param balance_name The item balance to check.
 * @return True if the item exists in the db.
 */
bool is_balance_in_db(std::wstring_view balance_name);

/**
 * @brief Checks if an item balance is allowed to world drop.
 *
 * @param balance_name The item balance to check.
 * @return True if the item may world drop.
 */
bool may_balance_world_drop(std::wstring_view balance_name);

/**
 * @brief Checks if a standard drop is valid.
 *
 * @param balance_name The item balance to check.
 * @param actor_cls The class of the actor the drop was from.
 * @param extra_item_pool_name The actor's extra itempool, if one exists.
 * @return True if it's a valid drop.
 */
bool is_valid_drop(std::wstring_view balance_name,
                   std::wstring_view actor_cls,
                   std::optional<std::wstring_view> extra_item_pool_name);

}  // namespace hunt::drops

#endif /* HUNT_NATIVE_DROPS_DROP_QUERIES_H */
