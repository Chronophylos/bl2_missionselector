import webbrowser
from typing import Dict, Iterable
from Mods.ModMenu import (
    SDKMod,
    Mods,
    ModTypes,
    EnabledSaveType,
    KeybindManager,
    Keybind,
    RegisterMod,
)
from Mods.Eridium import log
from Mods.Eridium.keys import KeyBinds
from Mods.Eridium.missions import MissionTracker, Mission

NEXT_MISSION_DESC: str = "Select next Mission"
NEXT_MISSION_KEY: str = KeyBinds.RightBracket
PREV_MISSION_DESC: str = "Select previous Mission"
PREV_MISSION_KEY: str = KeyBinds.LeftBracket


def getActiveMissionIndex(
    missionTracker: MissionTracker, missions: Iterable[Mission]
) -> int:
    activeMission = missionTracker.ActiveMission
    for index, mission in enumerate(missions):
        if mission.MissionDef.MissionNumber == activeMission.MissionNumber:
            return index
    return -1


class MissionSelector(SDKMod):
    Name: str = "Mission Selector"
    Author: str = "Chronophylos"
    Description: str = "Switch through missions with hotkeys, like in BL3\n"
    Version: str = "1.2.0"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {KeyBinds.Enter: "Enable", KeyBinds.G: "Github"}

    def __init__(self) -> None:
        super().__init__()

        self.Keybinds = [
            Keybind(NEXT_MISSION_DESC, NEXT_MISSION_KEY),
            Keybind(PREV_MISSION_DESC, PREV_MISSION_KEY),
        ]

    def Enable(self) -> None:
        super().Enable()

        log(self, f"Version: {self.Version}")

    def GameInputPressed(
        self, bind: KeybindManager.Keybind, event: KeybindManager.InputEvent
    ) -> None:
        if event != KeybindManager.InputEvent.Pressed:
            return

        if bind.Name == NEXT_MISSION_DESC:
            self.NextMission()
        elif bind.Name == PREV_MISSION_DESC:
            self.PrevMission()

    def SettingsInputPressed(self, action: str) -> None:
        super().SettingsInputPressed(action)

        if action == "Github":
            webbrowser.open("https://github.com/Chronophylos/bl2_missionselector")

    def NextMission(self) -> None:
        missionTracker = MissionTracker()
        activeMissions = missionTracker.getActiveMissions()
        index = getActiveMissionIndex(missionTracker, activeMissions)

        nextMission: Mission = None
        if index < len(activeMissions) - 1:
            nextMission = activeMissions[index + 1]
        else:
            nextMission = activeMissions[0]

        missionTracker.setActiveMission(nextMission.MissionDef)

    def PrevMission(self) -> None:
        missionTracker = MissionTracker()
        activeMissions = missionTracker.getActiveMissions()
        index = getActiveMissionIndex(missionTracker, activeMissions)

        nextMission = activeMissions[index - 1]

        missionTracker.setActiveMission(nextMission.MissionDef)


instance = MissionSelector()
if __name__ == "__main__":
    log(instance, "Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            log(instance, "Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)
