include(FetchContent)

# Downloading the same version used by the Python version the SDK ships with.
# To find the download link:
#   import sqlite3
#   con = sqlite3.connect(":memory:")
#   cur = con.cursor()
#   cur.execute("select sqlite_version()")
#   print(cur.fetchall())
# Then check against the release date on https://www.sqlite.org/changes.html

FetchContent_Declare(
    sqlite3_amalgamation
    URL      https://www.sqlite.org/2023/sqlite-amalgamation-3420000.zip
    URL_HASH MD5=eb9a6e56044bc518e6705521a1a929ed
)
FetchContent_MakeAvailable(sqlite3_amalgamation)

add_library(sqlite3 SHARED "${sqlite3_amalgamation_SOURCE_DIR}/sqlite3.c")
target_include_directories(sqlite3 PUBLIC "${sqlite3_amalgamation_SOURCE_DIR}")
if(MSVC)
    target_compile_definitions(sqlite3 PRIVATE "SQLITE_API=__declspec(dllexport)")
else()
    target_compile_definitions(sqlite3 PRIVATE "SQLITE_API=__attribute__((dllexport))")
endif()
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    # Sqlite uses a few intrinsics which clang doesn't implement, but it compiles fine ignoring them
    target_compile_options(sqlite3 PRIVATE -Wno-ignored-pragma-intrinsic)
endif()

set_target_properties(sqlite3 PROPERTIES
    DEBUG_POSTFIX "_d"
)
