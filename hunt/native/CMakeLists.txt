pyunrealsdk_add_module(osd osd.cpp)

install(
    TARGETS
        osd
    DESTINATION
        ${CMAKE_CURRENT_SOURCE_DIR}
)
