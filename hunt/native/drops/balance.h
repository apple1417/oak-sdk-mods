#ifndef HUNT_NATIVE_DROPS_BALANCE_H
#define HUNT_NATIVE_DROPS_BALANCE_H

namespace unrealsdk::unreal {

class UObject;

}

namespace hunt::balance {

using InventoryBalanceStateComponent = unrealsdk::unreal::UObject;

/**
 * @brief Gets the name of this item's inventory balance.
 *
 * @param bal_comp The InventoryBalanceStateComponent to inspect.
 * @return The inventory balance's name.
 */
std::wstring get_inventory_balance_name(InventoryBalanceStateComponent* bal_comp);

}  // namespace hunt::balance

#endif /* HUNT_NATIVE_DROPS_BALANCE_H */
