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

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(tmp, m) {
    LOG(INFO, "Linked against sqlite version: {}", sqlite3_libversion());

    m.attr("__version__") = 1;
}
