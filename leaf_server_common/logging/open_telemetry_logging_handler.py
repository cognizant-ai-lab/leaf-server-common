
# Copyright (C) 2019-2023 Cognizant Digital Business, Evolutionary AI.
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

OTLP_TRACE_ID_KEY = "trace_id_key"
OTLP_SPAN_ID_KEY = "span_id_key"

# In OpenTelemetryLoggingHandler configuration parameters,
# this key specifies OpenTelemetry collector endpoint
# to be used for exporting logs.
OTLP_ENDPOINT_KEY = "endpoint"

# In OpenTelemetryLoggingHandler configuration parameters,
# this key specifies a path to certificate file to be used
# if our connection to OpenTelemetry collector is TLS encrypted.
# Otherwise it should be omitted.
OTLP_CERTIFICATE_KEY = "certificate_file"


class OpenTelemetryLoggingHandler(logging.Handler):
    """
    Python logging handler that sends log messages to Open-telemetry collector.
    Services typically instantiate one of these
    by configuring the logging.json file for their service.

    Note that we use print() in here, as this stuff gets called when
    logging is just getting set up.

    This is sample OTLPLoggingHandler configuration:
    "handlers": {
        "otlp": {
            "class": "leaf_server_common.logging.otlp_logging_handler.OpenTelemetryLoggingHandler",
            "level": "INFO",
            # endpoint for OTLP collector
            "endpoint": "http://localhost:4318/v1/logs",
            # "substitution" keys: specify key names to be extracted
            # from LogRecord dictionary and put in "trace_id" and "span_id"
            # fields of outgoing OpenTelemetry Logger record.
            # This is done so we can better map our internal logging data structures
            # into values expected by OpenTelemetry backends (trace_id, span_id)
            "trace_id_key": "run_id",
            "span_id_key": "request_id"
        }
    },
    """

    def __init__(self, level=logging.NOTSET, **kwargs):
        super().__init__(level)

        # This variable prevents infinite recursion when init gets passed
        # debug=True
        self._already_called = False

        # In case log records don't have all the fields we need.
        # This happens in some print() statements during the early stages
        # of service setup.
        self._backup_formatter = logging.Formatter()

        # endpoint for target OpenTelemetry collector:
        self.endpoint: str = kwargs.get(OTLP_ENDPOINT_KEY, None)
        # path to certificate file to be used if our connection
        # to OpenTelemetry collector is TLS encrypted.
        # Should be None otherwise.
        self.certificate_file = kwargs.get(OTLP_CERTIFICATE_KEY, None)

        # Get the names for LogRecord members which we want to serve
        # as "trace_id" and "span_id" elements in outgoing OpenTelemetry log message:
        # This is done so we can better map our internal logging data structures
        # into values universally expected by OpenTelemetry backends,
        # namely trace_id and span_id.
        self.trace_id_key: str = kwargs.get(OTLP_TRACE_ID_KEY, None)
        self.span_id_key: str = kwargs.get(OTLP_SPAN_ID_KEY, None)

        try:
            self.exporter = \
                OTLPLogExporter(endpoint=self.endpoint,
                                certificate_file=self.certificate_file)
        except Exception as exc:
            # If we fail to create OTLPLogExporter for any reason
            # (for example we have no open-telemetry endpoint available)
            # print a message once and disable this LogExporter
            print(f"FAILED to create OTLPLogExporter: {exc}")
            # That will make any "emit" calls a no-action
            self._already_called = True

    def emit(self, record: logging.LogRecord):
        """
        Do whatever it takes to actually log the specified logging record

        :param record: The LogRecord from the Python logging infrastructure
                       to handle
        """
        if self._already_called:
            return
        self._already_called = True

        # Format the LogRecord per the pre-configured python logging.Formatter
        # With this, we get a string.
        # Try using our basic formatting.
        try:
            formatted = self.format(record)
        except ValueError:
            # That didn't work. Now try using something stock
            formatted = self._backup_formatter.format(record)

        # OTLP LoggingHandler only expects strings as "body" of LogRecord;
        # so lets check that we have a string:
        if formatted is None:
            formatted = ""
        if not isinstance(formatted, str):
            formatted = "<message is NOT a string>"

        # Try to extract LogRecord elements that will work
        # as our "trace_id" and "span_id" keys in output LogRecord:
        trace_id_val = self._get_substitute_key(self.trace_id_key, 0, record)
        span_id_val = self._get_substitute_key(self.span_id_key, 0, record)

        try:
            lrec = LogRecord(body=formatted,
                             span_id=span_id_val, trace_id=trace_id_val, trace_flags=0,
                             severity_number=SeverityNumber.UNSPECIFIED,
                             resource=_DEFAULT_RESOURCE)
            ldata = LogData(log_record=lrec, instrumentation_scope=InstrumentationScope(name=""))
            self.exporter.export([ldata])
        # pylint: disable=broad-except
        except BaseException as exc:
            # We want to catch as much as possible here:
            # don't really care about failures in logging.
            print(f"FAILED to send OTLP log data: {exc}")
        finally:
            self._already_called = False

    def _get_substitute_key(self, key: str, default_value: int, record: logging.LogRecord) -> int:
        """
        Interpreting "record" as a Python dictionary,
        extract value mapped to "key" in this dictionary.
        We expect value to be convertable to integer,
        any failure results in "default_value" being returned.
        """
        if key is None:
            return default_value
        subst_value = record.__dict__.get(key, None)
        if subst_value is None:
            return default_value
        if isinstance(subst_value, str) and subst_value.lower() == "none":
            return default_value
        try:
            return int(subst_value)
        except ValueError:
            return default_value

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
