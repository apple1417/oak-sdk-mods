cmake_minimum_required(VERSION 3.24)

project(oak_sdk_mods)

set(UNREALSDK_ARCH "x64")
set(UNREALSDK_UE_VERSION "UE4")
add_subdirectory(.libs/pyunrealsdk EXCLUDE_FROM_ALL)
