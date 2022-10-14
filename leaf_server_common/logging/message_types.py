
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
