import functools
import inspect

from math import pi
from typing import List
from json import loads as load_json

from beam_interactive_unofficial.beam_interactive_modified import proto


# <editor-fold desc="Helper Functions">

def _accepts(*types, none_accepted=True):
    def check_accepts(f):
        assert len(types) == len(inspect.signature(f).parameters)

        def new_f(*args, **kwargs):
            for (a, t) in zip(args, types):
                assert (isinstance(a, t) or (a is None if none_accepted else False)), \
                    "arg %r does not match %s" % (a, t)
            return f(*args, **kwargs)

        return functools.update_wrapper(new_f, f)

    return check_accepts


# </editor-fold>


class ProgressUpdate:
    def __init__(self):
        self.state = None  # type: str
        self.tactile_updates = []  # type: List[TactileUpdate]
        self.joystick_updates = []  # type: List[JoystickUpdate]
        self.screen_updates = []  # type: List[ScreenUpdate]

    # noinspection SpellCheckingInspection
    def to_probuf(self) -> proto.ProgressUpdate:
        self._check_vars()
        progress = proto.ProgressUpdate()
        if self.state is not None:
            progress.state = self.state

        for tactile_update in self.tactile_updates:
            tactile = progress.tactile.add()
            tactile.id = tactile_update.id

            if tactile_update.cooldown is not None:
                tactile.cooldown = tactile_update.cooldown

            if tactile_update.fired is not None:
                tactile.fired = tactile_update.fired

            if tactile_update.progress is not None:
                tactile.progress = tactile_update.progress

            if tactile_update.disabled is not None:
                tactile.disabled = tactile_update.disabled

        for joystick_update in self.joystick_updates:
            joystick = progress.joystick.add()
            joystick.id = joystick_update.id

            if joystick_update.angle is not None:
                joystick.id = joystick_update.angle

            if joystick_update.intensity is not None:
                joystick.intensity = joystick_update.intensity

            if joystick_update.disabled is not None:
                joystick.disabled = joystick_update.disabled

        for screen_update in self.screen_updates:
            screen = progress.screen.add()
            screen.id = screen_update.id

            for click_dict in screen_update.clicks:
                click = screen.clicks.add()
                click.intensity = click_dict["intensity"]
                click.coordinate.x = click_dict["coordinate"]["x"]
                click.coordinate.y = click_dict["coordinate"]["y"]

            if screen_update.disabled is not None:
                screen.disabled = screen_update.disabled

        return progress

    @classmethod
    def from_dict(cls, data: dict):
        update = cls()
        if "state" in data:
            update.state = str(data["state"])
        if "tactile" in data:
            assert isinstance(data["tactile"], list), "'tactile' in progress update data must be a list!"
            for tactile in data["tactile"]:
                update.tactile_updates.append(TactileUpdate.from_dict(tactile))
        if "joystick" in data:
            assert isinstance(data["joystick"], list), "'joystick' in progress update data must be a list!"
            for joystick in data["joystick"]:
                update.joystick_updates.append(JoystickUpdate.from_dict(joystick))
        if "screen" in data:
            assert isinstance(data["screen"], list), "'screen' in progress update data must be a list!"
            for screen in data["screen"]:
                update.screen_updates.append(ScreenUpdate.from_dict(screen))

        return update

    @classmethod
    def from_json(cls, json: str):
        return cls.from_dict(load_json(json))

    def _check_vars(self):
        assert isinstance(self.state, str) or self.state is None, \
            "'state' of ProgressUpdate must be of type 'str'"
        assert not any((not isinstance(i, TactileUpdate) for i in self.tactile_updates)), \
            "'tactile_updates' of ProgressUpdate must be a list of type 'TactileUpdate"
        assert not any((not isinstance(i, JoystickUpdate) for i in self.joystick_updates)), \
            "'joystick_updates' of ProgressUpdate must be a list of type 'JoystickUpdate"
        assert not any((not isinstance(i, ScreenUpdate) for i in self.screen_updates)), \
            "'screen_updates' of ProgressUpdate must be a list of type 'ScreenUpdate"

        for i in self.tactile_updates:
            i.check()
        for i in self.joystick_updates:
            i.check()
        for i in self.screen_updates:
            i.check()

    pass


# <editor-fold desc="Update Classes">

class TactileUpdate:
    def __init__(self, id_=None, cooldown=None, fired=None, progress=None, disabled=None):
        self.id = id_
        self.cooldown = cooldown
        self.fired = fired
        self.progress = progress
        self.disabled = disabled

    def check(self):
        self.id = int(self.id)
        assert self.id >= 0, \
            "'id' of TactileUpdate must  be 0 or greater"
        
        self.cooldown = int(self.cooldown) if self.cooldown is not None else None
        assert self.cooldown is None or self.cooldown >= 0, \
            "'cooldown' of TactileUpdate must be 0 or greater"

        self.fired = bool(self.fired) if self.fired is not None else None

        self.progress = float(self.progress) if self.progress is not None else None
        assert self.progress is None or 0 <= self.progress <= 1, \
            "'progress' of TactileUpdate must be between 0 and 1"

        self.disabled = bool(self.disabled) if self.disabled is not None else None

    @classmethod
    def from_dict(cls, data: dict):
        tactile = cls()
        assert "id" in data, "tactile update must have an id!"
        tactile.id = int(data["id"])
        if "cooldown" in data:
            tactile.cooldown = int(data["cooldown"])
        if "fired" in data:
            tactile.fired = bool(data["fired"])
        if "progress" in data:
            tactile.progress = float(data["progress"])
        if "disabled" in data:
            tactile.disabled = bool(data["disabled"])

        return tactile

    @classmethod
    def from_json(cls, json: str):
        return cls.from_dict(load_json(json))

    def wrap(self)-> ProgressUpdate:
        update = ProgressUpdate()
        update.tactile_updates.append(self)
        return update


class JoystickUpdate:
    def __init__(self, id_=None, angle=None, intensity=None, disabled=None):
        self.id = id_
        self.angle = angle
        self.intensity = intensity
        self.disabled = disabled

    def check(self):
        self.id = int(self.id)
        assert self.id >= 0, \
            "'id' of JoystickUpdate must be 0 or greater"
        
        self.angle = float(self.angle) if self.angle is not None else None
        assert self.angle is None or 0 <= self.angle <= 2 * pi, \
            "'angle' of JoystickUpdate must be between 0 and 2π"
        
        self.intensity = float(self.intensity) if self.intensity is not None else None
        assert self.intensity is None or self.intensity >= 0, \
            "'intensity' of JoystickUpdate must be 0 or greater"

        self.disabled = bool(self.disabled) if self.disabled is not None else None

    @classmethod
    def from_dict(cls, data: dict):
        joystick = cls()
        assert "id" in data, "joystick update must have an id!"
        joystick.id = int(data["id"])
        if "angle" in data:
            joystick.angle = float(data["angle"])
        if "intensity" in data:
            joystick.intensity = float(data["intensity"])
        if "disabled" in data:
            joystick.disabled = bool(data["disabled"])

    @classmethod
    def from_json(cls, json: str):
        return cls.from_dict(load_json(json))

    def wrap(self)-> ProgressUpdate:
        update = ProgressUpdate()
        update.joystick_updates.append(self)
        return update


class ScreenUpdate:
    def __init__(self, id_=None, clicks=None, disabled=None):
        self.id = id_
        self.clicks = clicks  # type: List[dict]
        self.disabled = disabled

        if self.clicks is None:
            self.clicks = []

    def check(self):
        self.id = int(self.id)
        assert self.id >= 0, \
            "'id' of ScreenUpdate must be of type 'int' and be 0 or greater"

        for click in self.clicks:
            click["intensity"] = float(click["intensity"])
            click["coordinate"]["x"] = float(click["coordinate"]["x"])
            click["coordinate"]["y"] = float(click["coordinate"]["y"])

        self.disabled = bool(self.disabled) if self.disabled is not None else None

    @classmethod
    def from_dict(cls, data: dict):
        screen = cls()
        assert "id" in data, "screen update must have an id!"
        screen.id = data["id"]
        if "clicks" in data:
            screen.clicks = data["clicks"]

    @classmethod
    def from_json(cls, json: str):
        return cls.from_dict(load_json(json))

    def wrap(self)-> ProgressUpdate:
        update = ProgressUpdate()
        update.screen_updates.append(self)
        return update

# </editor-fold>
