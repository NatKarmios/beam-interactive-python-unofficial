import sys

from beam_interactive_unofficial import *

"""
EXAMPLE USAGE
The functions passed as handlers are automatically wrapped with asyncio.coroutine.
"""


def on_connect(_):
    # Acknowledge connection
    print("connected")


def on_report(report):
    # Print how many of each button has been pressed (if button has been pressed at least once)
    for tactile in report.tactile:
        if tactile.pressFrequency > 0:
            print(str(tactile.id) + " : " + str(int(tactile.pressFrequency)))

    client.set_state("TEST_STATE")


def on_error(error):
    # Handle error packets
    print("Error!")
    print(error.message)


def on_disconnect():
    print("Disconnected from Beam.")


client = BeamInteractiveClient(auth_details={"username": "USERNAME", "password": "PASSWORD"}, on_connect=on_connect,
                               on_report=on_report, on_error=on_error, on_disconnect=on_disconnect)

try:
    client.start()
except ConnectionFailedError as e:
    print(str(e), file=sys.stderr)
except InvalidAuthenticationError:
    print("Your login details are incorrect!", file=sys.stderr)
