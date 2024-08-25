pyunrealsdk_add_module(osd osd.cpp)

pyunrealsdk_add_module(drops
    drops/balance.cpp
    drops/coop.cpp
    drops/drop_queries.cpp
    drops/find_drop_request.cpp
    drops/hooks.cpp
    drops/main.cpp
    drops/sql.cpp
)
target_link_libraries(drops PRIVATE sqlite3)

install(
    TARGETS
        osd
        drops
    DESTINATION
        ${CMAKE_CURRENT_SOURCE_DIR}
)
