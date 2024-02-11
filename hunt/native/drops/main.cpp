#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/static_py_object.h"
#include "pyunrealsdk/type_casters.h"
#include "unrealsdk/unreal/classes/uobject.h"

#include "sql.h"

using namespace unrealsdk::unreal;

namespace {

sqlite3* database = nullptr;

}

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(drops, m) {
    m.def(
        "set_db_getter",
        [](const py::object& getter) {
            hunt::sql::set_db_getter({getter});
            return getter;
        },
        "Sets the function used to get the db path.\n"
        "\n"
        "This function takes no args, should ensure the db file exists, and return the\n"
        "path to it.\n"
        "\n"
        "Args:\n"
        "    getter: The getter function to set.\n"
        "Returns:\n"
        "    The passed getter, so that this may be used as a decorator.",
        "getter"_a);

    m.def("close_db", hunt::sql::close_db,
          "Closes the db connection, to allow the file to be replaced.\n"
          "\n"
          "Note the connection will be re-opened the next time it's required.");

    m.def("test", []() {
        static const constexpr std::string_view count_query = "select count(*) from Items";
        static std::weak_ptr<sqlite3_stmt> count_statement;

        if (!hunt::sql::ensure_prepared(count_statement, count_query)) {
            return -1;
        }

        std::shared_ptr<sqlite3_stmt> statement{count_statement};
        sqlite3_reset(statement.get());

        auto res = sqlite3_step(statement.get());
        LOG(DEV_WARNING, "Statement result: {}", res);
        if (res != SQLITE_OK && res != SQLITE_ROW && res != SQLITE_DONE) {
            LOG(DEV_WARNING, "Failed to run statement: {}", sqlite3_errmsg(database));
            return -1;
        }
        auto ret = sqlite3_column_int(statement.get(), 0);

        res = sqlite3_step(statement.get());
        LOG(DEV_WARNING, "Statement result: {}", res);

        return ret;
    });
}
