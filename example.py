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


# Note: all of these parameters *except* `auth_details` and `timeout` are OPTIONAL.
client = BeamInteractiveClient(auth_details={"username": "USERNAME", "password": "PASSWORD"}, timeout=1,
                               on_connect=on_connect, on_report=on_report, on_error=on_error,
                               auto_reconnect=True, max_reconnect_attempts=10, reconnect_delay=3)

try:
    client.start()
except ConnectionFailedError as e:
    print(str(e), file=sys.stderr)
except InvalidAuthenticationError:
    print("Your login details are incorrect!", file=sys.stderr)
