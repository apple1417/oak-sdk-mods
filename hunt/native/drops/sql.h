#ifndef HUNT_NATIVE_DROPS_SQL_H
#define HUNT_NATIVE_DROPS_SQL_H

#include "pyunrealsdk/pch.h"

#ifdef __clang__
// Sqlite, detecting `_MSC_VER`, tries to use `__int64`, which is an MSVC extension
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wlanguage-extension-token"
#endif

#include "sqlite3.h"

#ifdef __clang__
#pragma clang diagnostic pop
#endif

namespace pyunrealsdk {

class StaticPyObject;

}

namespace hunt::sql {

/**
 * @brief Set the db getter.
 *
 * @param getter A python function which returns the path to the db (and ensures it exists).
 */
void set_db_getter(const pyunrealsdk::StaticPyObject&& getter);

/**
 * @brief Closes the db connection, to allow the file to be replaced.
 * @note Will be re-opened the next time it's required.
 */
void close_db(void);

/**
 * @brief Checks if a prepared statement is valid, and if not tries to re-create it.
 * @note May fail.
 *
 * @param statement The statement. Modified in place.
 * @param query The query to run.
 * @return True if prepared, false on failure.
 */
bool ensure_prepared(std::weak_ptr<sqlite3_stmt>& statement, std::string_view query);

}  // namespace hunt::sql

#endif /* HUNT_NATIVE_DROPS_SQL_H */
