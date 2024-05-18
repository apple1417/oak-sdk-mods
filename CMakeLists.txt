cmake_minimum_required(VERSION 3.24)

project(oak_sdk_mods)

add_subdirectory(.oak-mod-manager EXCLUDE_FROM_ALL)

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
