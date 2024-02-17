#include "pyunrealsdk/pch.h"

#include "sql.h"

namespace {

// This doesn't seem to want to play well with templated string pointers
// NOLINTBEGIN(cppcoreguidelines-pro-bounds-array-to-pointer-decay)

/**
 * @brief Runs a query which takes a single balance name as input, and returns a single bool.
 *
 * @tparam query The query to run.
 * @tparam name The name to give the query in error messages.
 * @param balance_name The name of the balance to check.
 * @return The result of the query
 */
template <const char* query, const char* name>
bool run_single_bal_bool_query(std::wstring_view balance_name) {
    static const constexpr std::string_view query_sv = query;
    static std::weak_ptr<sqlite3_stmt> static_statement;
    if (!hunt::sql::ensure_prepared(static_statement, query_sv)) {
        LOG(DEV_WARNING, "Failed to prepare '{}' query!", name);
        return false;
    }

    const std::shared_ptr<sqlite3_stmt> statement{static_statement};
    sqlite3_reset(statement.get());

    static_assert(sizeof(wchar_t) == sizeof(char16_t));

    auto res =
        sqlite3_bind_text16(statement.get(), 1, balance_name.data(),
                            static_cast<int>(balance_name.size() * sizeof(wchar_t)), SQLITE_STATIC);
    if (res != SQLITE_OK) {
        LOG(DEV_WARNING, "Failed to bind balance name for '{}' query: {}", name,
            sqlite3_errstr(res));
        return false;
    }

    res = sqlite3_step(statement.get());
    if (res != SQLITE_ROW) {
        LOG(DEV_WARNING, "Failed to step '{}' query: {}", name, sqlite3_errstr(res));
        return false;
    }

    return sqlite3_column_int(statement.get(), 0) != 0;
}
// NOLINTEND(cppcoreguidelines-pro-bounds-array-to-pointer-decay)
}  // namespace

namespace hunt::drops {

bool is_balance_in_db(std::wstring_view balance_name) {
    static const constexpr char query[] = "SELECT EXISTS (SELECT 1 FROM Items WHERE Balance = ?)";
    static const constexpr char name[] = "is_balance_in_db";
    return run_single_bal_bool_query<query, name>(balance_name);
}

bool may_balance_world_drop(std::wstring_view balance_name) {
    static const constexpr char query[] =
        "SELECT EXISTS (SELECT 1 FROM Drops WHERE ItemBalance = ? and EnemyClass IS NULL)";
    static const constexpr char name[] = "may_balance_world_drop";
    return run_single_bal_bool_query<query, name>(balance_name);
}

bool is_valid_drop(std::wstring_view balance_name,
                   std::wstring_view actor_cls,
                   std::optional<std::wstring_view> extra_item_pool_name) {
    static const std::string_view query =
        "SELECT EXISTS ("
        "SELECT 1 FROM Drops WHERE"
        " ItemBalance = ?"
        " and EnemyClass = ?"
        " and (ExtraItemPool IS NULL or ExtraItemPool = ?)"
        ")";
    static std::weak_ptr<sqlite3_stmt> static_statement;
    if (!hunt::sql::ensure_prepared(static_statement, query)) {
        LOG(DEV_WARNING, "Failed to prepare 'is_valid_drop' query!");
        return false;
    }

    const std::shared_ptr<sqlite3_stmt> statement{static_statement};
    sqlite3_reset(statement.get());

    static_assert(sizeof(wchar_t) == sizeof(char16_t));

    auto bind_str = [&statement](std::wstring_view str, int idx, std::string_view field) {
        auto res =
            sqlite3_bind_text16(statement.get(), idx, str.data(),
                                static_cast<int>(str.size() * sizeof(wchar_t)), SQLITE_STATIC);
        if (res != SQLITE_OK) {
            LOG(DEV_WARNING, "Failed to bind {} for 'is_valid_drop' query: {}", field,
                sqlite3_errstr(res));
            return false;
        }
        return true;
    };

    if (!bind_str(balance_name, 1, "balance name")) {
        return false;
    }
    if (!bind_str(actor_cls, 2, "actor class")) {
        return false;
    }
    if (extra_item_pool_name) {
        if (!bind_str(*extra_item_pool_name, 3, "extra item pool")) {
            return false;
        }
    } else {
        auto res = sqlite3_bind_null(statement.get(), 3);
        if (res != SQLITE_OK) {
            // Note hardcoding the field in the hopes it gets inlined with the other call
            LOG(DEV_WARNING, "Failed to bind {} for 'is_valid_drop' query: {}", "extra item pool",
                sqlite3_errstr(res));
            return false;
        }
    }

    auto res = sqlite3_step(statement.get());
    if (res != SQLITE_ROW) {
        LOG(DEV_WARNING, "Failed to step 'is_valid_drop' query: {}", sqlite3_errstr(res));
        return false;
    }

    return sqlite3_column_int(statement.get(), 0) != 0;
}

}  // namespace hunt::drops
