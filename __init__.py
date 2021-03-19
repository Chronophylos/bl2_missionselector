import unrealsdk
import webbrowser
import enum
from typing import Dict, Iterable, Optional
from Mods.ModMenu import (
    SDKMod,
    Mods,
    ModTypes,
    EnabledSaveType,
    KeybindManager,
    Keybind,
    RegisterMod,
    ServerMethod,
)

# thank you apple :)
try:
    from Mods.Eridium import log, isClient
    from Mods.Eridium.keys import KeyBinds
except ImportError:
    webbrowser.open("https://github.com/RLNT/bl2_eridium")
    raise

if __name__ == "__main__":
    import importlib
    import sys

    importlib.reload(sys.modules["Mods.Eridium"])
    importlib.reload(sys.modules["Mods.Eridium.keys"])

    # See https://github.com/bl-sdk/PythonSDK/issues/68
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore

NEXT_MISSION_DESC: str = "Select next Mission"
NEXT_MISSION_KEY: str = KeyBinds.RightBracket
PREV_MISSION_DESC: str = "Select previous Mission"
PREV_MISSION_KEY: str = KeyBinds.LeftBracket


class MissionStatus(enum.IntEnum):
    NotStarted = 0
    Active = 1
    RequiredObjectivesComplete = 2
    ReadyToTurnIn = 3
    Complete = 4
    Failed = 5
    MAX = 6

    def canBeActivated(self) -> bool:
        """Returns true if the status is either ReadyToTurnIn or Active."""
        return self in [
            MissionStatus.ReadyToTurnIn,
            MissionStatus.Active,
        ]


class MissionSelector(SDKMod):
    Name: str = "Mission Selector"
    Author: str = "Chronophylos"
    Description: str = "Switch through missions with hotkeys, like in BL3\n"
    Version: str = "1.2.0"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {
        KeyBinds.Enter: "Enable",
        KeyBinds.G: "GitHub",
        KeyBinds.D: "Discord",
    }

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
            self.nextMission()
        elif bind.Name == PREV_MISSION_DESC:
            self.prevMission()

    def SettingsInputPressed(self, action: str) -> None:
        if action == "GitHub":
            webbrowser.open("https://github.com/RLNT/bl2_missionselector")
        elif action == "Discord":
            webbrowser.open("https://discord.com/invite/Q3qxws6")
        else:
            super().SettingsInputPressed(action)

    def nextMission(self) -> None:
        missionTracker = self.getMissionTracker()
        activeMissions = self.getActiveMissions(missionTracker)
        index = self.getActiveMissionIndex(missionTracker, activeMissions)

        nextMission = None
        if index < len(activeMissions) - 1:
            nextMission = activeMissions[index + 1]
        else:
            nextMission = activeMissions[0]

        self.setActiveMission(nextMission.MissionDef)

    def prevMission(self) -> None:
        missionTracker = self.getMissionTracker()
        activeMissions = self.getActiveMissions(missionTracker)
        index = self.getActiveMissionIndex(missionTracker, activeMissions)

        nextMission = activeMissions[index - 1]

        self.setActiveMission(nextMission.MissionDef)

    @staticmethod
    def getActiveMissionIndex(
        missionTracker: unrealsdk.UObject, missions: Iterable[unrealsdk.UObject]
    ) -> int:
        """Returns the index of the current active mission in missions."""
        activeMission = missionTracker.ActiveMission
        for index, mission in enumerate(missions):
            if mission.MissionDef.MissionNumber == activeMission.MissionNumber:
                return index
        return -1

    @staticmethod
    def getMissionTracker() -> unrealsdk.UObject:
        return unrealsdk.GetEngine().GetCurrentWorldInfo().GRI.MissionTracker

    @staticmethod
    def getActiveMissions(
        missionTracker: unrealsdk.UObject,
    ) -> Iterable[unrealsdk.UObject]:
        """Returns all active missions sorted by their MissionNumber.

        For a definition of active see `MissionStatus.isActive`-
        """
        activeMissions = sorted(
            [
                m
                for m in missionTracker.MissionList
                if MissionStatus(m.Status).canBeActivated()
            ],
            key=lambda m: int(m.MissionDef.MissionNumber),
        )

        return activeMissions

    def setActiveMission(self, mission: unrealsdk.UObject) -> None:
        """Set the currently tracked mission to mission."""
        if isClient():
            self._serverSetActiveMission(mission.MissionNumber)
        else:
            self._setActiveMission(mission.MissionNumber)

    def getMissionByNumber(
        self, missionTracker: unrealsdk.UObject, number: int
    ) -> unrealsdk.UObject:
        """Returns the mission with the MissionNumber equal to number.

        Raises an IndexError if the mission was not found.
        """
        for mission in missionTracker.MissionList:
            if mission.MissionDef.MissionNumber == number:
                return mission
        raise IndexError(f"There is nomission with the mission number {number}")

    @ServerMethod
    def _serverSetActiveMission(
        self, number: int, PC: Optional[unrealsdk.UObject] = None
    ) -> None:
        self._setActiveMission(number, PC)

    def _setActiveMission(
        self, number: int, PC: Optional[unrealsdk.UObject] = None
    ) -> None:
        missionTracker = self.getMissionTracker()
        mission = self.getMissionByNumber(missionTracker, number)
        missionTracker.SetActiveMission(mission.MissionDef, True, PC)


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
