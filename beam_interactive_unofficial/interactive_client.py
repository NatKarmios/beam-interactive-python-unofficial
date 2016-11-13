import asyncio
from urllib.parse import urljoin

from beam_interactive_unofficial.progress_update import ProgressUpdate
from beam_interactive_unofficial.beam_interactive_modified import start, proto, connection
from requests import Session

URL = "https://beam.pro/api/v1/"


# noinspection PyAttributeOutsideInit
class BeamInteractiveClient:
    def __init__(self, auth_details, on_connect=None, on_report=None, on_error=None):
        self._auth_details = auth_details
        self._handlers = {
            proto.id.handshake_ack: asyncio.coroutine(on_connect),
            proto.id.report: asyncio.coroutine(on_report),
            proto.id.error: asyncio.coroutine(on_error)
        }
        self._session = Session()

    def start(self):
        self.loop = asyncio.get_event_loop()

        try:
            self.loop.run_until_complete(self._run())
        finally:
            self.loop.close()

    @asyncio.coroutine
    def _run(self):
        self.login_response = self._login()  # type: dict
        self.channel_id = self.login_response["channel"]["id"]
        self.data = self._join_interactive()  # type: dict
        self.connection = \
            yield from start(self.data["address"], self.channel_id, self.data["key"], self.loop)  # type: connection
        while (yield from self.connection.wait_message()):
            yield from self._handle_packet(self.connection.get_packet())

        self.connection.close()

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

    @asyncio.coroutine
    def send(self, progress: ProgressUpdate):
        progress_probuf = progress.to_probuf()
        yield from self.connection.send(progress_probuf)

    # <editor-fold desc="connection helper functions">
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

    pass
