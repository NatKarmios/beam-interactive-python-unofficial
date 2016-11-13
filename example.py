from beam_interactive_unofficial import BeamInteractiveClient, ProgressUpdate

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

    progress = ProgressUpdate()
    progress.state = "TEST_STATE"
    yield from client.send(progress)


def on_error(error):
    # Handle error packets
    print("Error!")
    print(error.message)

client = BeamInteractiveClient(auth_details={"username": "USERNAME", "password": "PASSWORD"},
                               on_connect=on_connect, on_report=on_report, on_error=on_error)
