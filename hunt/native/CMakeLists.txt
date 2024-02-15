pyunrealsdk_add_module(osd osd.cpp)

pyunrealsdk_add_module(drops
    drops/main.cpp
    drops/balance.cpp
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
