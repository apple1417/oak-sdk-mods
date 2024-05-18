cmake_minimum_required(VERSION 3.24)

project(oak_sdk_mods)

include(FetchContent)

FetchContent_Declare(
    oak_mod_manager

    EXCLUDE_FROM_ALL True
    # Rather not have a copy of this for every single preset
    # Switching presets still re-downloads unfortunately, so this only saves storage space
    SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/.out/oak-mod-manager"

    GIT_REPOSITORY git@github.com:bl-sdk/oak-mod-manager.git
    # For future versions we'll set this to a version tag `origin/v1.3`, but the 1.2 tag doesn't
    # have the right python downloading logic we need, so using the first commit that works instead
    # GIT_SHALLOW True
    GIT_TAG d85c60f2a7f54d35681a0305262f9121c02ffc2a
)
FetchContent_MakeAvailable(oak_mod_manager)

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
