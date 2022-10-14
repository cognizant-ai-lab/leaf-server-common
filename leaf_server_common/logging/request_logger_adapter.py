
# Copyright (C) 2019-2021 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
#
# This software is a trade secret, and contains proprietary and confidential
# materials of Cognizant Digital Business Evolutionary AI.
# Cognizant Digital Business prohibits the use, transmission, copying,
# distribution, or modification of this software outside of the
# Cognizant Digital Business EAI organization.
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
