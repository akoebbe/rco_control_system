import supervisor
import traceback

class TimeIt:
    def __init__(self):
        self.start_msecs = supervisor.ticks_ms()

    def stop(self):
        print(f"Took {(supervisor.ticks_ms() - self.start_msecs)} ms at: {__file__}")
