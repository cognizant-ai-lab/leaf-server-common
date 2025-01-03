
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

from logging import LoggerAdapter

from leaf_server_common.logging.message_types import API
from leaf_server_common.logging.message_types import METRICS


class RequestLoggerAdapter(LoggerAdapter):
    """
    Class carrying around context for logging messages that arise
    within the context of processing a single service request.

    This class only does rudimentary logging, but other versions
    of this class might (for instance) be instantiated with trace ID
    information from the gRPC headers so that information can be
    collated and logged in a standard manner.
    """

    def metrics(self, msg, *args):
        """
        Intended only to be used by service-level code.
        Method to which metrics logging within the context of a single
        request is funneled.

        :param msg: The string message to log
        :param args: arguments for the formatting of the string to be logged
        :return: Nothing
        """
        self.log(METRICS, msg, *args)

    def api(self, msg, *args):
        """
        Intended only to be used by service-level code.
        Method to which api logging within the context of a single
        request is funneled.

        :param msg: The string message to log
        :param args: arguments for the formatting of the string to be logged
        :return: Nothing
        """
        self.log(API, msg, *args)
