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

    @classmethod
    def tactile_cooldown(cls, length: int, num_buttons: int):
        update = cls()
        for i in range(num_buttons):
            update.tactile_updates.append(TactileUpdate(id_=i, cooldown=length))

        return update

    def _check_vars(self):
        assert isinstance(self.state, str), \
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
        assert isinstance(self.id, int) and self.id >= 0, \
            "'id' of TactileUpdate must be of type 'int' and be 0 or greater"
        assert (isinstance(self.cooldown, int) and self.cooldown >= 0) or self.cooldown is None, \
            "'cooldown' of TactileUpdate must be of type 'int' and be 0 or greater"
        assert (isinstance(self.fired, bool)) or self.fired is None, \
            "'fired' of TactileUpdate must be of type 'bool'"
        assert (isinstance(self.progress, float) and 0 <= self.progress <= 1) or self.progress is None, \
            "'progress' of TactileUpdate must be of type 'float' and be between 0 and 1"
        assert (isinstance(self.disabled, bool)) or self.disabled is None, \
            "'disabled' of TactileUpdate must be of type 'bool'"

    @classmethod
    def from_dict(cls, data: dict):
        tactile = cls()
        assert "id" in data, "tactile update must have an id!"
        tactile.id = data["id"]
        if "cooldown" in data:
            tactile.cooldown = data["cooldown"]
        if "fired" in data:
            tactile.fired = data["fired"]
        if "progress" in data:
            tactile.progress = data["progress"]
        if "disabled" in data:
            tactile.disabled = data["disabled"]

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
        assert isinstance(self.id, int) and self.id >= 0, \
            "'id' of JoystickUpdate must be of type 'int' and be 0 or greater"
        assert (isinstance(self.angle, float) and 0 <= self.angle <= 2 * pi) or self.angle is None, \
            "'angle' of JoystickUpdate must be of type 'float' and be between 0 and 2π"
        assert (isinstance(self.intensity, float) and self.intensity >= 0) or self.intensity is None, \
            "'intensity' of JoystickUpdate must be of type 'float' and be 0 or greater"
        assert (isinstance(self.disabled, bool)) or self.disabled is None, \
            "'disabled' of JoystickUpdate must be of type 'bool'"

    @classmethod
    def from_dict(cls, data: dict):
        joystick = cls()
        assert "id" in data, "joystick update must have an id!"
        if "angle" in data:
            joystick.angle = data["angle"]
        if "intensity" in data:
            joystick.intensity = data["intensity"]
        if "disabled" in data:
            joystick.disabled = data["disabled"]

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
        assert isinstance(self.id, int) and self.id >= 0, \
            "'id' of ScreenUpdate must be of type 'int' and be 0 or greater"
        assert (isinstance(self.clicks, list) and not any(not isinstance(click, dict) for click in self.clicks)), \
            "'clicks' of ScreenUpdate must be a list of dicts!"
        assert (isinstance(self.disabled, bool)) or self.disabled is None, \
            "'disabled' of ScreenUpdate must be of type 'bool'"

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
