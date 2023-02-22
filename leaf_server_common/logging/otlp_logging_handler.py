
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

import json
import logging

from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs._internal import LogData, LogRecord
from opentelemetry.sdk.resources import _DEFAULT_RESOURCE
from opentelemetry.sdk.util.instrumentation import InstrumentationScope
from opentelemetry._logs.severity import SeverityNumber

class OTLPLoggingHandler(logging.Handler):
    """
    Python logging handler that sends log messages to Open-telemetry collector.
    Services typically instantiate one of these
    by configuring the logging.json file for their service.

    Note that we use print() in here, as this stuff gets called when
    logging is just getting set up.
    """

    def __init__(self, level=logging.NOTSET, **kwargs):
        super().__init__(level)

        # In case log records don't have all the fields we need.
        # This happens in some print() statements during the early stages
        # of service setup.
        self._backup_formatter = logging.Formatter()

        self.exporter = OTLPLogExporter()
        print(f"OTLPLogHandler called with {kwargs}")

    def emit(self, record: logging.LogRecord):
        print(f"OTLPLogHandler: {record}")

        # Try using our basic formatting.
        try:
            formatted = self.format(record)
        except ValueError:
            # That didn't work. Now try using something stock
            formatted = self._backup_formatter.format(record)

        lrec = LogRecord(body=formatted, span_id=1, trace_id=1, trace_flags=128, severity_number=SeverityNumber.UNSPECIFIED, resource=_DEFAULT_RESOURCE)
        ldata = LogData(log_record=lrec, instrumentation_scope=InstrumentationScope(name="xyz"))
        try:
            self.exporter.export([ldata])
        except BaseException as exc:
            print(f"FAILED to send OTLP log data: {exc}")


    def handleError(self, record: LogRecord):
        """
        Handle errors which occur during an emit() call.

        This method should be called from handlers when an exception is
        encountered during an emit() call. If raiseExceptions is false,
        exceptions get silently ignored. This is what is mostly wanted
        for a logging system - most users will not care about errors in
        the logging system, they are more interested in application errors.
        You could, however, replace this with a custom handler if you wish.
        The record which was being processed is passed in to this method.
        """
        # Slurp up errors. This can happen in early prints when the service
        # is not yet set up for proper log record formatting with the "source"
        # key set.
