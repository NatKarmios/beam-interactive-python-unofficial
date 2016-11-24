import asyncio
from urllib.parse import urljoin

from beam_interactive_unofficial.progress_update import *
from beam_interactive_unofficial.exceptions import *
from beam_interactive_unofficial.beam_interactive_modified import start, proto, connection

from requests import Session
from requests.exceptions import ConnectionError

URL = "https://beam.pro/api/v1/"


# noinspection PyAttributeOutsideInit
class BeamInteractiveClient:
    def __init__(self, auth_details, timeout: int, on_connect=lambda x: None, on_report=lambda x: None,
                 on_error=lambda x: None, auto_reconnect=False, max_reconnect_attempts=-1, reconnect_delay=5):

        self._on_connect, self._on_report, self._on_error = on_connect, on_report, on_error
        self._max_reconn, self._auto_reconnect = max_reconnect_attempts, auto_reconnect
        self._reconnect_delay = reconnect_delay
        self._auth_details = auth_details
        self._timeout = timeout
        self._handlers = {
            proto.id.handshake_ack: asyncio.coroutine(on_connect),
            proto.id.report: asyncio.coroutine(on_report),
            proto.id.error: asyncio.coroutine(on_error)
        }

    def start(self, _attempt=0, _reconnect=False):
        """Start the connection to Beam."""
        self._session = Session()

        self.state = None
        self._started = False
        self._num_buttons = None

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        e = None
        try:
            e = self.loop.run_until_complete(asyncio.gather(
                self._run(delay=(self._reconnect_delay if _reconnect else None)), return_exceptions=True))
        finally:
            tasks = asyncio.gather(*asyncio.Task.all_tasks(), return_exceptions=True)
            tasks.cancel()
            self.loop.run_until_complete(tasks)
            self.loop.close()

            if e is not None:
                if isinstance(e[0], asyncio.TimeoutError):
                    print("Disconnected from Beam!")
                    self.start(_attempt=1, _reconnect=True)
                if isinstance(e[0], ConnectionError):
                    if _attempt == self._max_reconn or not _reconnect or not self._auto_reconnect:
                        raise ConnectionFailedError("Failed to {}connect to Beam{}!"
                                                    .format("re" if _reconnect else "",
                                                            " after {} attempts"
                                                            .format(self._max_reconn)) if _reconnect else "")
                    self.start(_attempt=_attempt + 1, _reconnect=True)

    def send(self, update: (ProgressUpdate, JoystickUpdate, TactileUpdate, ScreenUpdate, dict, str)):
        """Send a progress update to Beam."""
        self._check_started()

        if isinstance(update, ProgressUpdate):
            progress = update
        elif isinstance(update, (JoystickUpdate, TactileUpdate, ScreenUpdate)):
            progress = update.wrap()
        elif isinstance(update, dict):
            progress = ProgressUpdate.from_dict(update)
        elif isinstance(update, str):
            progress = ProgressUpdate.from_json(update)
        else:
            raise ValueError("Invalid data type - must be a ProgressUpdate, TactileUpdate, ScreenUpdate, dict or str.")

        if progress.state is not None:
            self.state = progress.state
        progress_probuf = progress.to_probuf()
        self.connection.send(progress_probuf)

    def set_state(self, state):
        progress = ProgressUpdate()
        progress.state = str(state)
        self.send(progress)

    def tactile_fire(self, tactile_id=None):
        if tactile_id is None:
            update_on = ProgressUpdate()
            update_off = ProgressUpdate()
            for i in range(self._num_buttons):
                update_on.tactile_updates.append(TactileUpdate(id_=i, fired=True))
                update_off.tactile_updates.append(TactileUpdate(id_=i, fired=False))
            self.send(update_on)
            self.send(update_off)
            return

        self.send(TactileUpdate(id_=tactile_id, fired=True))
        self.send(TactileUpdate(id_=tactile_id, fired=False))

    def tactile_cooldown(self, length, tactile_id=None):
        if tactile_id is None:
            update = ProgressUpdate()
            for i in range(self._num_buttons):
                update.tactile_updates.append(TactileUpdate(id_=i, cooldown=length))
            self.send(update)
            return

        try:
            progress = ProgressUpdate()
            for id_ in tactile_id:
                progress.tactile_updates.append(TactileUpdate(id_, length))
            self.send(progress)

        except TypeError:
            self.send(TactileUpdate(id_=tactile_id, cooldown=length))

    # <editor-fold desc="Private Functions">

    @asyncio.coroutine
    def _run(self, delay=None):
        if delay is not None:
            print("Couldn't connect to Beam - trying again in 5 seconds...")
            yield from asyncio.sleep(delay)
        try:
            self.login_response = self._login()  # type: dict
        except (KeyError, TypeError):
            raise InvalidAuthenticationError()

        try:
            self.channel_id = self.login_response["channel"]["id"]
        except ConnectionError:
            raise ConnectionFailedError("Please check your internet connection.")
        except (KeyError, ValueError):
            raise ConnectionFailedError(self.login_response["message"])

        self.data = self._join_interactive()  # type: dict
        self.connection = \
            yield from start(self.data["address"], self.channel_id, self.data["key"], self.loop)  # type: connection
        self._started = True
        while (yield from asyncio.wait_for(self.connection.wait_message(), self._timeout)):
            yield from self._handle_packet(self.connection.get_packet())

    @asyncio.coroutine
    def _handle_packet(self, packet):
        decoded, _ = packet
        packet_id = proto.id.get_packet_id(decoded)

        if packet_id == proto.id.report:
            self._num_buttons = len(decoded.tactile)

        if packet_id in self._handlers:
            yield from self._handlers[packet_id](decoded)
        elif decoded is None:
            print("Unknown bytes were received. Uh oh!", packet_id)
        else:
            print("We got packet {} but didn't handle it!".format(packet_id))

    # <editor-fold desc="helper functions">
    def _login(self):
        """Log into Beam via the API."""
        return self._session.post(self._build("/users/login"), data=self._auth_details).json()

    @staticmethod
    def _build(endpoint):
        """Build an address for an API endpoint."""
        return urljoin(URL, endpoint.lstrip('/'))

    def _join_interactive(self):
        """Retrieve interactive connection information."""
        return self._session.get(self._build("/interactive/{channel}/robot").format(
            channel=self.channel_id)).json()

    def _check_started(self):
        if not self._started:
            raise ClientNotConnectedError()

    # </editor-fold>

    # </editor-fold>

    pass
