# Copyright 2019-2025 Cognizant Technology Solutions Corp, www.cognizant.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#  END COPYRIGHT

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
