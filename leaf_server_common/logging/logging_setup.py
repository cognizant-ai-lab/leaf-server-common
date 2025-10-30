
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
from threading import current_thread
from typing import Any
from typing import Dict

from leaf_common.logging.logging_setup \
    import LoggingSetup
from leaf_server_common.logging.service_log_record \
    import ServiceLogRecord
from leaf_server_common.logging.structured_log_record \
    import StructuredLogRecord


def setup_extra_logging_fields(metadata_dict: Dict[str, Any] = None,
                               extra_logging_fields: Dict[str, str] = None):
    """
    Sets up extra thread-specific fields to be logged with each
    log message.

    :param metadata_dict: Metadata dictionary. Default is None
    :param extra_logging_fields: Additional fields dictionary. Default is None
    """

    # Assumes ServiceLogRecord.set_up_record_factory() has already been called once
    # what is returned is really a copy.
    extra = ServiceLogRecord.get_default_extra_logging_fields()
    if extra is None:
        extra = {}
    if extra_logging_fields is not None:
        extra.update(extra_logging_fields)

    extra["thread_name"] = current_thread().name

    # Get information from the GRPC client context that is to be
    # put into the logs.
    if metadata_dict is not None:

        for key in extra:
            if key in ("source", "thread_name"):
                # Pass these up. They should not be coming from
                # any metadata dictionary in the request
                continue

            # Override the defaults with what was in the metadata_dict
            # Do not incorporate any fields that were not already
            # in the accumulated extra dictionary.
            value = metadata_dict.get(key, None)
            if value is not None:
                extra[key] = str(value)

    # Create the ServiceLogRecord thread-local context.
    # In doing so like this, we actually are setting up global variables.
    service_log_record = ServiceLogRecord()
    service_log_record.set_logging_fields_dict(extra)


def setup_logging(server_name_for_logs: str,
                  default_log_dir,
                  log_config_env,
                  log_level_env,
                  extra_logging_fields_defaults: Dict[str, str] = None):
    """
    Setup logging to be used by ServerLifeTime
    """
    default_extra_logging_fields = {
        "source": server_name_for_logs,
        "thread_name": "Unknown",
        "request_id": "None",
        "user_id": "None",
        "group_id": "None",
        "run_id": "None",
        "experiment_id": "None"
    }

    extras = extra_logging_fields_defaults
    if extras is None:
        extras = default_extra_logging_fields

    logging_setup = LoggingSetup(default_log_config_dir=default_log_dir,
                                 default_log_config_file="logging.json",
                                 default_log_level="DEBUG",
                                 log_config_env=log_config_env,
                                 log_level_env=log_level_env)
    logging_setup.setup()

    # Enable translation of log message args to MessageType
    StructuredLogRecord.set_up_record_factory()

    # Enable thread-local information to go into log messages
    ServiceLogRecord.set_up_record_factory(extras)
    setup_extra_logging_fields(extra_logging_fields=extras)
