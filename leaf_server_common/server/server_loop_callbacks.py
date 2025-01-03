
# Copyright (C) 2019-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# leaf-server-common SDK Software in commercial settings.
#
# END COPYRIGHT


class ServerLoopCallbacks:
    """
    An interface for the the ServerLifetime to call which will
    reach out at certain points in the main server loop.
    """

    def loop_callback(self) -> bool:
        """
        Periodically called by the main server loop of ServerLifetime.
        :return: True if the server is considered active. False or None otherwise
        """
        # Do nothing
        return False

    def shutdown_callback(self):
        """
        Called by the main server loop when it's time to shut down.
        """
        # Do nothing
