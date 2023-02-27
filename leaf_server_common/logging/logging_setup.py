
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

import copy
from threading import current_thread

from leaf_common.logging.logging_setup import LoggingSetup
from leaf_common.session.grpc_metadata_util import GrpcMetadataUtil

from leaf_server_common.logging.service_log_record \
    import ServiceLogRecord
from leaf_server_common.logging.structured_log_record \
    import StructuredLogRecord


def setup_extra_logging_fields(context=None,
                               extra_logging_fields=None):
    """
    Sets up extra thread-specific fields to be logged with each
    log message.

    :param context: The grpc.ServicerContext. Default is None
    """

    extra = copy.copy(extra_logging_fields) if extra_logging_fields else {}
    extra["thread_name"] = current_thread().name

    # Get information from the GRPC client context that is to be
    # put into the logs.
    if context is not None:
        metadata = context.invocation_metadata()
        metadata_dict = GrpcMetadataUtil.to_dict(metadata)

        # Add fields from the GRPC Header metadata to the logging info
        request_id = metadata_dict.get("request_id", None)
        if request_id is not None:
            extra["request_id"] = str(request_id)

        user_id = metadata_dict.get("user_id", None)
        if user_id is not None:
            extra["user_id"] = str(user_id)

        group_id = metadata_dict.get("group_id", None)
        if group_id is not None:
            extra["group_id"] = str(group_id)

        experiment_id = metadata_dict.get("experiment_id", None)
        if experiment_id is not None:
            extra["experiment_id"] = str(experiment_id)

        run_id = metadata_dict.get("run_id", None)
        if run_id is not None:
            extra["run_id"] = str(run_id)

    # Create the ServiceLogRecord thread-local context.
    # In doing so like this, we actually are setting up global variables.
    service_log_record = ServiceLogRecord()
    service_log_record.set_logging_fields_dict(extra)


def setup_logging(server_name_for_logs: str,
                  default_log_dir, log_config_env, log_level_env):
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

    logging_setup = LoggingSetup(default_log_config_dir=default_log_dir,
                                 default_log_config_file="logging.json",
                                 default_log_level="DEBUG",
                                 log_config_env=log_config_env,
                                 log_level_env=log_level_env)
    logging_setup.setup()

    # Enable translation of log message args to MessageType
    StructuredLogRecord.set_up_record_factory()

    # Enable thread-local information to go into log messages
    ServiceLogRecord.set_up_record_factory(default_extra_logging_fields)
    setup_extra_logging_fields(extra_logging_fields=default_extra_logging_fields)
