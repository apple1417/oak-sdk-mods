#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/static_py_object.h"

#include "sql.h"

namespace hunt::sql {

namespace {

pyunrealsdk::StaticPyObject db_getter{};

std::shared_ptr<sqlite3> database{};
std::vector<std::shared_ptr<sqlite3_stmt>> all_statements{};

}  // namespace

void set_db_getter(const pyunrealsdk::StaticPyObject&& getter) {
    db_getter = getter;
}

void close_db(void) {
    all_statements.clear();
    database = nullptr;
}

bool ensure_prepared(std::weak_ptr<sqlite3_stmt>& statement, std::string_view query) {
    if (!statement.expired()) {
        return true;
    }

    if (database == nullptr) {
        if (!db_getter) {
            return false;
        }

        std::string path;
        {
            const py::gil_scoped_acquire gil{};
            path = py::cast<std::string>(db_getter());
        }

        {
            sqlite3* new_db = nullptr;
            auto res = sqlite3_open_v2(path.c_str(), &new_db, SQLITE_OPEN_READONLY, nullptr);
            if (res != SQLITE_OK) {
                LOG(DEV_WARNING, "Failed to open database: {}", sqlite3_errstr(res));
                sqlite3_close_v2(new_db);
                return false;
            }
            database = std::shared_ptr<sqlite3>{
                new_db, [](sqlite3* db_to_close) {
                    auto res = sqlite3_close_v2(db_to_close);
                    if (res != SQLITE_OK) {
                        LOG(DEV_WARNING, "Failed to close database: {}", sqlite3_errstr(res));
                    }
                }};
        }

        auto res = sqlite3_extended_result_codes(database.get(), 1);
        if (res != SQLITE_OK) {
            LOG(DEV_WARNING, "Failed to enable extended error codes: {}", sqlite3_errstr(res));
        }
    }

    sqlite3_stmt* raw_statement = nullptr;
    auto res = sqlite3_prepare_v3(database.get(), query.data(), static_cast<int>(query.size() + 1),
                                  SQLITE_PREPARE_PERSISTENT, &raw_statement, nullptr);
    if (res != SQLITE_OK) {
        LOG(DEV_WARNING, "Failed to prepare statement: {}", sqlite3_errmsg(database.get()));
        return false;
    }

    all_statements.emplace_back(raw_statement, sqlite3_finalize);
    statement = all_statements.back();
    return true;
}

}  // namespace hunt::sql
