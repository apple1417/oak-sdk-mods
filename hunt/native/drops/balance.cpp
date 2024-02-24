#include "pyunrealsdk/pch.h"
#include "unrealsdk/unreal/classes/properties/uarrayproperty.h"
#include "unrealsdk/unreal/classes/properties/uobjectproperty.h"
#include "unrealsdk/unreal/classes/uclass.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unrealsdk.h"

#include "balance.h"
#include "sql.h"

/*
Some of the legendary artifact/com balances are "expandable". Based on parts, these can roll into
one of multiple different items names. Normally we'd consider these all the same item - but in these
specific cases, each individual item also has it's own dedicated balance. The DB only contains the
dedicated balance.

Generally speaking, the dedicated balance is only for the dedicated drop (that's why they were
added), and world drops are always the generic balance. This means if we get a world drop from the
dedicated source, or if you just try redeem a world drop token, we won't match the balance and won't
count the item - which looks identical to one which would work.

To fix this, we look through the parts on the item, and map it back to the dedicated balance.
*/

using namespace unrealsdk::unreal;

namespace {

using InventoryBalanceData = UObject;
using InventoryPartData = UObject;

using ExpandableBalanceDataMap =
    std::unordered_map<InventoryBalanceData*, std::unordered_map<InventoryPartData*, std::wstring>>;

ExpandableBalanceDataMap load_expandable_balance_data(void) {
    static const constinit std::string_view load_query =
        "SELECT RootBalance, Part, ExpandedBalance FROM ExpandableBalances";

    // Not bothering with a static since this should only get called once
    std::weak_ptr<sqlite3_stmt> load_statement;
    if (!hunt::sql::ensure_prepared(load_statement, load_query)) {
        throw std::runtime_error("Failed to load expandable balance data!");
    }

    const std::shared_ptr<sqlite3_stmt> statement{load_statement};
    sqlite3_reset(statement.get());

    ExpandableBalanceDataMap output{};

    while (true) {
        auto res = sqlite3_step(statement.get());
        if (res == SQLITE_DONE) {
            break;
        }
        if (res != SQLITE_ROW) {
            throw std::runtime_error(unrealsdk::fmt::format(
                "Failed to load expandable balance data: {}", sqlite3_errstr(res)));
        }

        // Sqlite docs say we must call text16 before bytes16 to make sure that type conversions
        // have been done first
        static_assert(sizeof(wchar_t) == sizeof(char16_t));

        auto root_bal_ptr =
            reinterpret_cast<const wchar_t*>(sqlite3_column_text16(statement.get(), 0));
        const size_t root_bal_size = sqlite3_column_bytes16(statement.get(), 0) / sizeof(wchar_t);

        auto part_ptr = reinterpret_cast<const wchar_t*>(sqlite3_column_text16(statement.get(), 1));
        const size_t part_size = sqlite3_column_bytes16(statement.get(), 1) / sizeof(wchar_t);

        auto expanded_bal_ptr =
            reinterpret_cast<const wchar_t*>(sqlite3_column_text16(statement.get(), 2));
        const size_t expanded_bal_size =
            sqlite3_column_bytes16(statement.get(), 2) / sizeof(wchar_t);

        auto root_obj =
            unrealsdk::find_object(L"InventoryBalanceData"_fn, {root_bal_ptr, root_bal_size});
        auto part_obj = unrealsdk::find_object(L"InventoryPartData"_fn, {part_ptr, part_size});

        output[root_obj].emplace(std::piecewise_construct, std::forward_as_tuple(part_obj),
                                 std::forward_as_tuple(expanded_bal_ptr, expanded_bal_size));
    }

    return output;
}

}  // namespace

namespace hunt::balance {

std::wstring get_inventory_balance_name(InventoryBalanceStateComponent* bal_comp) {
    static const ExpandableBalanceDataMap expandable_balance_data = load_expandable_balance_data();

    static auto inv_bal_prop =
        bal_comp->Class->find_prop_and_validate<UObjectProperty>(L"InventoryBalanceData"_fn);
    static auto part_list_prop =
        bal_comp->Class->find_prop_and_validate<UArrayProperty>(L"PartList"_fn);

    auto bal_obj = bal_comp->get<UObjectProperty>(inv_bal_prop);

    if (expandable_balance_data.contains(bal_obj)) {
        const auto& part_mappings = expandable_balance_data.at(bal_obj);

        auto arr = bal_comp->get<UArrayProperty>(part_list_prop);
        for (size_t idx = 0; idx < arr.size(); idx++) {
            auto part = arr.get_at<UObjectProperty>(idx);

            if (part_mappings.contains(part)) {
                return part_mappings.at(part);
            }
        }
    }

    return bal_obj->get_path_name();
}

}  // namespace hunt::balance
