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
    def __init__(self, auth_details, on_connect=lambda x: None, on_report=lambda x: None, on_error=lambda x: None,
                 on_disconnect=lambda x: None):
        self._auth_details = auth_details
        self._handlers = {
            proto.id.handshake_ack: asyncio.coroutine(on_connect),
            proto.id.report: asyncio.coroutine(on_report),
            proto.id.error: asyncio.coroutine(on_error)
        }
        self._session = Session()
        self._on_disconnect = on_disconnect
        self.state = None

    def start(self):
        """Start the connection to Beam."""

        self.loop = asyncio.get_event_loop()

        try:
            self.loop.run_until_complete(self._run())
        finally:
            self.loop.close()

    def send(self, update: (ProgressUpdate, JoystickUpdate, TactileUpdate, ScreenUpdate, dict, str)):
        """Send a progress update to Beam."""
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
        self.send(state)

    # <editor-fold desc="Private Functions">

    @asyncio.coroutine
    def _run(self):
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
        while (yield from self.connection.wait_message()):
            yield from self._handle_packet(self.connection.get_packet())

        self.connection.close()
        self._on_disconnect()

    @asyncio.coroutine
    def _handle_packet(self, packet):
        decoded, _ = packet
        packet_id = proto.id.get_packet_id(decoded)

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
    # </editor-fold>

    # </editor-fold>

    pass
