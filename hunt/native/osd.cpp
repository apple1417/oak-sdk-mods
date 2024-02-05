#include "pyunrealsdk/pch.h"
#include "unrealsdk/hook_manager.h"
#include "unrealsdk/unreal/cast.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/properties/uobjectproperty.h"
#include "unrealsdk/unreal/classes/properties/ustrproperty.h"
#include "unrealsdk/unreal/classes/properties/ustructproperty.h"
#include "unrealsdk/unreal/classes/ufunction.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/wrappers/bound_function.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"

using namespace unrealsdk::unreal;

namespace {

const constexpr std::wstring_view DRAW_HUD_FUNC_NAME = L"/Script/Engine.HUD:ReceiveDrawHUD";
const constexpr std::wstring_view DRAW_HOOK_ID = L"hunt_draw_osd";
const constexpr std::wstring_view UPDATE_HOOK_ID = L"hunt_update_osd";

bool draw_hud_hook(unrealsdk::hook_manager::Details& details);

void show(void) {
    unrealsdk::hook_manager::add_hook(DRAW_HUD_FUNC_NAME, unrealsdk::hook_manager::Type::PRE,
                                      DRAW_HOOK_ID, draw_hud_hook);
}
void hide(void) {
    unrealsdk::hook_manager::remove_hook(DRAW_HUD_FUNC_NAME, unrealsdk::hook_manager::Type::PRE,
                                         DRAW_HOOK_ID);
}

/*
The main draw hud function is called every frame, so we try optimize it as much as possible - hence
writing this in C++ in the first place.

Looking up functions (or any property really) is O(n), so just cache them outside of the hook.
Putting together the function args is also O(n), including a bunch of safety checks, so instead we
build the params structs beforehand and pass them directly. This does rely on the game not modifying
them, but luckily that works out.
*/

UFunction* draw_text_func =
    validate_type<UFunction>(unrealsdk::find_object(L"Function", L"/Script/Engine.HUD:DrawText"));
UFunction* draw_rect_func =
    validate_type<UFunction>(unrealsdk::find_object(L"Function", L"/Script/Engine.HUD:DrawRect"));

WrappedStruct background_to_draw{draw_rect_func};
std::vector<WrappedStruct> text_to_draw{};

bool draw_hud_hook(unrealsdk::hook_manager::Details& details) {
    BoundFunction{draw_rect_func, details.obj}.call<void>(background_to_draw);

    BoundFunction draw_text{draw_text_func, details.obj};
    for (auto& text : text_to_draw) {
        draw_text.call<void>(text);
    }
    return false;
}

// For some reason, trying to call `HUD::GetTextSize` out of band just returns 0. To deal with this,
// we throw another hook on the exact same function, which we'll only run once when it's time to
// update the data we're drawing.
// This is a bit less optimized (but should still be far better than Python)

UFunction* get_text_size_func = validate_type<UFunction>(
    unrealsdk::find_object(L"Function", L"/Script/Engine.HUD:GetTextSize"));
UObject* font = unrealsdk::find_object(L"Font", L"/Game/UI/_Shared/Fonts/OAK_BODY.OAK_BODY");

std::vector<std::wstring> pending_lines_to_draw{};
// To handle the case where someone calls `update_text` then `show` before the hook runs
bool show_after_update = false;

const constexpr auto OUTER_PADDING = 10;
const constexpr auto INTER_LINE_PADDING = 1;

bool update_data_hook(unrealsdk::hook_manager::Details& details) {
    unrealsdk::hook_manager::remove_hook(DRAW_HUD_FUNC_NAME, unrealsdk::hook_manager::Type::PRE,
                                         UPDATE_HOOK_ID);

    if (pending_lines_to_draw.empty()) {
        hide();
        text_to_draw.clear();
        return false;
    }
    text_to_draw.clear();

    BoundFunction get_text_size{get_text_size_func, details.obj};
    WrappedStruct args{get_text_size_func};
    args.set<UObjectProperty>(L"Font"_fn, font);
    args.set<UFloatProperty>(L"Scale"_fn, 1.0);

    float max_width = 0;
    float total_height = OUTER_PADDING;

    for (const auto& line : pending_lines_to_draw) {
        args.set<UStrProperty>(L"text"_fn, line);
        get_text_size.call<void>(args);

        const float width = args.get<UFloatProperty>(L"OutWidth"_fn);
        const float height = args.get<UFloatProperty>(L"OutHeight"_fn);

        text_to_draw.emplace_back(draw_text_func);
        auto& text_args = text_to_draw.back();

        text_args.set<UStrProperty>(L"text"_fn, line);
        text_args.set<UFloatProperty>(L"ScreenX"_fn, OUTER_PADDING);
        text_args.set<UFloatProperty>(L"ScreenY"_fn, total_height);
        text_args.set<UObjectProperty>(L"Font"_fn, font);
        text_args.set<UFloatProperty>(L"Scale"_fn, 1.0);

        auto text_colour = text_args.get<UStructProperty>(L"TextColor"_fn);
        text_colour.set<UFloatProperty>(L"R"_fn, 1.0);
        text_colour.set<UFloatProperty>(L"G"_fn, 1.0);
        text_colour.set<UFloatProperty>(L"B"_fn, 1.0);
        text_colour.set<UFloatProperty>(L"A"_fn, 1.0);

        total_height += height + INTER_LINE_PADDING;
        max_width = std::max(width, max_width);
    }

    // Add the outer padding for both sides
    background_to_draw.set<UFloatProperty>(L"ScreenW"_fn, max_width + 2 * OUTER_PADDING);
    // Remove the inner padding from the bottom, and add the outer padding - we already started with
    // the outer padding at the top
    background_to_draw.set<UFloatProperty>(L"ScreenH"_fn,
                                           total_height - INTER_LINE_PADDING + OUTER_PADDING);

    pending_lines_to_draw.clear();
    if (show_after_update) {
        show();
        show_after_update = false;
    }

    return false;
}

};  // namespace

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(osd, m) {
    // We can leave all other background args as zero-init
    // NOLINTNEXTLINE(readability-magic-numbers)
    background_to_draw.get<UStructProperty>(L"RectColor"_fn).set<UFloatProperty>(L"A"_fn, 0.5);

    m.def(
        "show",
        []() {
            if (text_to_draw.empty()) {
                if (pending_lines_to_draw.empty()) {
                    hide();
                } else {
                    show_after_update = true;
                }
            } else {
                show();
            }
        },
        "Shows the on screen display, if there are lines available.");

    m.def("hide", &hide, "Hides the on screen display.");
    m.def(
        "update_lines",
        [](const std::vector<std::wstring>&& lines) {
            pending_lines_to_draw = lines;

            if (pending_lines_to_draw.empty()) {
                hide();
                text_to_draw.clear();
            } else {
                unrealsdk::hook_manager::add_hook(DRAW_HUD_FUNC_NAME,
                                                  unrealsdk::hook_manager::Type::PRE,
                                                  UPDATE_HOOK_ID, update_data_hook);
            }
        },
        "Updates the lines the on screen display should show.\n"
        "\n"
        "Args:\n"
        "    lines: A list of the lines to display.",
        "lines"_a);
}
