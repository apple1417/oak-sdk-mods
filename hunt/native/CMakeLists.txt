pyunrealsdk_add_module(osd osd.cpp)

pyunrealsdk_add_module(tmp tmp.cpp)
target_link_libraries(tmp PRIVATE sqlite3)

install(
    TARGETS
        osd
        tmp
    DESTINATION
        ${CMAKE_CURRENT_SOURCE_DIR}
)
