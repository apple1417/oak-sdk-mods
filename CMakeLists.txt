cmake_minimum_required(VERSION 3.24)

project(oak_sdk_mods)

set(UNREALSDK_ARCH "x64")
set(UNREALSDK_UE_VERSION "UE4")
add_subdirectory(.libs/pyunrealsdk EXCLUDE_FROM_ALL)

include(sqlite3.cmake)

file(GLOB_RECURSE subfolders RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "*/CMakeLists.txt")
foreach(cmakelists ${subfolders})
    if (${cmakelists} MATCHES "^\\.")
        continue()
    endif()

    get_filename_component(folder "${cmakelists}" DIRECTORY)
    message(STATUS "Including mod folder: ${folder}")
    add_subdirectory(${folder})
endforeach()
