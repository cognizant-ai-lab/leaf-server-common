

class ServerLoopCallbacks:
    """
    An interface for the the ServerLifetime to call which will
    reach out at certain points in the main server loop.
    """

    def loop_callback(self):
        """
        Periodically called by the main server loop of ServerLifetime.
        """
        # Do nothing

    def shutdown_callback(self):
        """
        Called by the main server loop when it's time to shut down.
        """
        # Do nothing
