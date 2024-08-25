#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/static_py_object.h"
#include "pyunrealsdk/type_casters.h"
#include "unrealsdk/unreal/classes/uobject.h"

#include "balance.h"
#include "coop.h"
#include "hooks.h"
#include "sql.h"

using namespace unrealsdk::unreal;

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

    m.def(
        "set_drop_callback",
        [](const py::object& callback) {
            hunt::drops::set_drop_callback({callback});
            return callback;
        },
        "Sets the callback run when a valid drop is collected.\n"
        "\n"
        "This callback takes a single arg, the balance name of the item which was\n"
        "collected. The return value is ignored.\n"
        "\n"
        "Args:\n"
        "    callback: The callback to set.\n"
        "Returns:\n"
        "    The passed callback, so that this may be used as a decorator.",
        "callback"_a);

    m.def("set_coop_blink_count", hunt::drops::coop::set_blink_count,
          "Sets the number of times items will blink during coop transmission.\n"
          "\n"
          "Set to 0 to disable coop support.\n"
          "\n"
          "Args:\n"
          "    num_blinks: The number of times to blink."
          "num_blinks"_a);

    m.def("close_db", hunt::sql::close_db,
          "Closes the db connection, to allow the file to be replaced.\n"
          "\n"
          "Note the connection will be re-opened the next time it's required.");

    m.def(
        "get_inventory_balance_name",
        [](const py::object& bal_comp) {
            return hunt::balance::get_inventory_balance_name(
                pyunrealsdk::type_casters::cast<UObject*>(bal_comp));
        },
        "Gets the name of this item's inventory balance.\n"
        "\n"
        "Args:\n"
        "    bal_comp: The InventoryBalanceStateComponent to inspect.\n"
        "Return:\n"
        "    The inventory balance's name.",
        "bal_comp"_a);

    m.def(
        "enable",
        []() {
            hunt::drops::enable();
            hunt::drops::coop::enable();
        },
        "Enables the drop detection hooks.");
    m.def(
        "disable",
        []() {
            hunt::drops::disable();
            hunt::drops::coop::disable();
        },
        "Disables the drop detection hooks.");
}
