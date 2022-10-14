
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

import os
import json

from logging import getLogger
from logging import Formatter
from logging import Handler
from logging import LogRecord
from logging import NOTSET
from logging import WARNING

import libhoney

from leaf_common.persistence.easy.easy_hocon_persistence \
    import EasyHoconPersistence


class HoneycombLoggingHandler(Handler):
    """
    Python logging handler that sends log messages to honeycomb
    via libhoney.  Services typically instatiate one of these
    by configuring the logging.json file for their service.

    Note that we use print() in here, as this stuff gets called when
    logging is just getting set up.

    We expect two files to be present on the file system:

        ~/event_dataset.hocon:  contains a dictionary of the form:
            {
                "dataset": <dataset_name_to_use>
            }

            This allows the dataset name to be injected into a service
            container as an argument.  If the dataset name cannot be
            determined in this way, a last resort is to use the
            HONEYCOMB_DATASET environment variable.

        ~/.events/honeycomb_config.hocon: contains a dictionary of the form:
            {
                "datasets": {
                    <dataset_name>: {
                        "write_key": <write_key_secret>
                    }
                }
            }

            This allows data for write_keys to be mounted in a service container
            as a secret, separately from the specification of the dataset to use
            for logging.  Thus, a single honeycomb_config.hocon file can contain
            multiple secrets for multiple services.

            If any write_key is not found, a last resort is to use the O11Y_KEY
            environment variable.

        If a proper dataset and write_key cannot be determined, then no honeycomb
        logging initialization happens at all.
    """

    def __init__(self, level=NOTSET, global_honeycomb_event_params=None):
        """
        Constructor.

        :param level: Sets the threshold for this handler to level.
            Logging messages which are less severe than level will be ignored.
            When a handler is created, the level is set to NOTSET
            (which causes all messages to be processed).
        :param global_honeycomb_event_params: Default None.
            This is an optional dictionary carrying constant key/value pairs
            that should be logged with every honeycomb event
        """
        super().__init__(level=level)

        # This variable prevents infinite recursion when init gets passed
        # debug=True
        self._already_called = False

        # In case log records don't have all the fields we need.
        # This happens in some print() statements during the early stages
        # of service setup.
        self._backup_formatter = Formatter()

        self._global_honeycomb_event_params = global_honeycomb_event_params

        self._initialize()

    def _initialize(self):

        # Specifically disable some logging that causes infinite recursion
        # This seems to need to be done here and not in the logging.json config.
        getLogger("urllib3.connectionpool").setLevel(WARNING)

        # Get the dataset to use
        dataset = self._get_dataset()

        # Load the config with secrets, either from a file or environment
        config = self._get_dataset_config(dataset)

        # No need to initialize if no write key was found
        write_key = config.get("write_key", None)
        if write_key is None:
            print(f"No write_key found for honeycomb_config dataset: {dataset}")
            return

        # Initialize the honeycomb library with what we got from the config
        # Note: when debug=True, some infinite loop and/or recursion can happen.
        print(f"Initializing honeycomb for dataset: {dataset}")
        libhoney.init(writekey=write_key, dataset=dataset, debug=False)

        # Optionally add any global event params
        if self._global_honeycomb_event_params is not None:
            libhoney.add(self._global_honeycomb_event_params)

    def emit(self, record: LogRecord):
        """
        Do whatever it takes to actually log the specified logging record

        :param record: The LogRecord from the Python logging infrastructure
                       to handle
        """
        # Format the LogRecord per the pre-configured python logging.Formatter
        # With this, we get a string.
        if self._already_called:
            return

        self._already_called = True

        # Try using our basic formatting.
        try:
            formatted = self.format(record)
        except ValueError:
            # That didn't work. Now try using something stock
            formatted = self._backup_formatter.format(record)

        # Check to see if we have a structured log message already
        structured_log = None
        try:
            structured_log = json.loads(formatted)
        except json.decoder.JSONDecodeError:
            # Just emit the string with a standard message key
            structured_log = {
                "message": formatted
            }

        # Create the libhoney event and add our structured logging to it
        event = libhoney.new_event()
        event.add(structured_log)

        # Emit via libhoney
        event.send()

        self._already_called = False

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

    @staticmethod
    def _get_dataset():
        """
        Reads a dataset.hocon config file from the home directory to get
        which honeycomb data set to use.

        Note that this file is stored separately from the secrets to
        allow the file containing the write_key secrets and other
        configuration to contain information for more than one dataset.

        :return: the dataset to use
        """
        dataset = None

        # Reads from home directory
        persistence = EasyHoconPersistence(base_name="event_dataset")
        event_dataset_config = persistence.restore()

        if event_dataset_config is not None:
            dataset = event_dataset_config.get("dataset", None)

        if dataset is None:
            dataset = os.environ.get("HONEYCOMB_DATASET", None)

        print(f"Using honeycomb_config dataset: {dataset}")

        return dataset

    @staticmethod
    def _get_dataset_config(dataset: str):
        """
        :param dataset: The string dataset to log honecomb events to.
        :return: the honecomb config dictionary for the given dataset
        """
        # Attempt a restore of the file with write_key secrets.
        persistence = EasyHoconPersistence(base_name="honeycomb_config",
                                           folder=".events")
        honeycomb_config = persistence.restore()

        # We can get a None dict if the file does not exist.
        if honeycomb_config is None:
            print("No file honeycomb_config.hocon")
            honeycomb_config = {
                "datasets": {
                    dataset: {
                        # We assume this comes from the environment
                        # If this fails, all is lost
                        "write_key": os.environ.get("O11Y_KEY", None)
                    }
                }
            }

        datasets_config = honeycomb_config.get("datasets", {})
        dataset_config = datasets_config.get(dataset, {})

        return dataset_config
