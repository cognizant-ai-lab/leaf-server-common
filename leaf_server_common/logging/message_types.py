
# Copyright (C) 2019-2022 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# leaf-server-common SDK Software in commercial settings.
#
# END COPYRIGHT
from enum import Enum
from logging import INFO
from logging import addLevelName


# We need to use specific logging levels for our own message types to
# have our LogRecord derivitives be compatible with stock python loggers.
# To be sure the API and METRICS log levels show up when log-level INFO is on,
# we make their log level intefer value a few clicks up from INFO.
# Seeing API is more important than seeing METRICS
API = INFO + 7
METRICS = INFO + 5

# Give the new log levels names for standard reporting
addLevelName(API, "API")
addLevelName(METRICS, "METRICS")


class MessageType(str, Enum):
    """
    Represents the various types of log messages an application may generate.
    """

    # For messages that do not fit into any of the other categories
    # Used for DEBUG and INFO
    OTHER = 'Other'

    # Error messages intended for technical personnel, such as internal errors, stack traces
    # Used for CRITICAL, ERROR, and exception()
    ERROR = 'Error'

    # Warning only
    WARNING = 'Warning'

    # Metrics messages, for example, API call counts
    METRICS = 'Metrics'

    # Tracking API calls
    API = 'API'
