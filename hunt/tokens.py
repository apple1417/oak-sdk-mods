# ruff: noqa: D103

from typing import Any

import unrealsdk
from bl3_mod_menu import DialogBox, DialogBoxChoice
from mods_base import EInputEvent, KeybindOption, hook, raw_keybinds
from ui_utils import show_hud_message
from unrealsdk.unreal import BoundFunction, UFunction, UObject, WrappedStruct

from .db import open_db

HINT_BAR_APPEND_FUNC: UFunction = unrealsdk.find_object(  # type: ignore
    "Function",
    "/Script/GbxUI.GbxHintBarWidgetContainer:HintBarAppendHint",
)
HUD_STATE_INSPECT_MENU = unrealsdk.find_object(
    "GbxHUDStateData",
    "/Game/UI/HUD/HUDStates/UIData_HUDState_InspectMenu.UIData_HUDState_InspectMenu",
)

redeem_token_option = KeybindOption(
    "Redeem Item",
    "R",
    description="The key to press while inspecting an item in order to redeem it.",
)


inspected_item_balance: str | None = None

redeem_choice = DialogBoxChoice("Redeem")


@DialogBox(
    "Redeem using World Drop Token?",
    (redeem_choice, DialogBox.CANCEL),
    "Are you sure you want to spend a World Drop Token to redeem this Item?",
    dont_show=True,
)
def redeem_confirm_dialog(choice: DialogBoxChoice) -> None:
    global inspected_item_balance
    if choice != redeem_choice:
        return
    assert inspected_item_balance is not None

    with open_db("w") as cur:
        cur.execute(
            """
            INSERT INTO
                Collected (ItemID)
            SELECT
                ID
            FROM
                Items
            WHERE
                Balance = ?
            """,
            (inspected_item_balance,),
        )
        cur.execute(
            """
            INSERT INTO
                TokenRedeems (CollectedID)
            SELECT
                ID
            FROM
                Items
            WHERE
                rowid = ?
            """,
            (cur.lastrowid,),
        )

    inspected_item_balance = None
    raw_keybinds.pop()


@hook("/Script/OakGame.GFxItemInspectionMenu:OnItemCardReady")
def item_inspect_start_hook(
    obj: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    global inspected_item_balance

    if redeem_token_option.value is None:
        return

    # TODO: if this is one of the combined COM/Artifact balances, convert it to the standalone
    bal = obj.InspectionSourceBalanceComponent.InventoryBalanceData._path_name()
    with open_db("r") as cur:
        cur.execute(
            """
            SELECT
                (not AlreadyCollected) and AvailableTokens > 0,
                format('Available Tokens: %d', AvailableTokens)
            FROM
            (
                SELECT
                    EXISTS (
                        SELECT
                            1
                        FROM
                            Collected as c
                        LEFT JOIN
                            Items as i ON c.ItemID = i.ID
                        WHERE
                            i.Balance = ?
                    ) as AlreadyCollected,
                    (SELECT Tokens FROM AvailableTokens) as AvailableTokens
            )
            """,
            (bal,),
        )
        allowed, message = cur.fetchone()
        if not allowed:
            return
    inspected_item_balance = bal

    show_hud_message(
        f"Press [{redeem_token_option.value}] to redeem using World Drop Tokens",
        message,
    )

    raw_keybinds.push()
    raw_keybinds.add(redeem_token_option.value, EInputEvent.IE_Pressed, redeem_confirm_dialog.show)

    # BoundFunction(HINT_BAR_APPEND_FUNC, obj.HintBarContainer)(
    #     unrealsdk.make_struct(
    #         "GbxHintInfo",
    #         InputActions=["GbxMenu_Primary"],
    #         HelpText="World Drops",
    #     ),
    # )


@hook("/Script/OakGame.OakHUD:StateChanged")
def item_inspect_end_hook(
    _1: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    global inspected_item_balance
    if inspected_item_balance is not None:
        raw_keybinds.pop()
    inspected_item_balance = None


@hook("/Script/GbxMission.Mission:MissionComplete")
def mission_complete_hook(
    obj: UObject,
    _2: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    with open_db("w") as cur:
        cur.execute(
            """
            INSERT INTO
                CompletedMissions (MissionClass)
            VALUES
                (?)
            """,
            (obj.Class._path_name(),),
        )
