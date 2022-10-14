
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
import random
import time

from threading import current_thread
from threading import RLock
from concurrent import futures

import grpc

from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from leaf_common.logging.logging_setup import LoggingSetup
from leaf_common.session.grpc_metadata_util import GrpcMetadataUtil

from leaf_server_common.logging.request_logger_adapter \
    import RequestLoggerAdapter
from leaf_server_common.logging.service_log_record \
    import ServiceLogRecord
from leaf_server_common.logging.structured_log_record \
    import StructuredLogRecord
from leaf_server_common.server.request_logger import RequestLogger
from leaf_server_common.server.server_loop_callbacks \
    import ServerLoopCallbacks

ONE_MINUTE_IN_SECONDS = 60


class ServerLifetime(RequestLogger):
    """
    A class which safely keeps track of stats for a gRPC service
    and helps it shut down nicely.
    """

    # Tied for Public Enemy #3 for too-many-arguments
    # pylint: disable=too-many-arguments
    # Tied for Public Enemy #2 for too-many-instance-attributes
    # pylint: disable=too-many-instance-attributes,too-many-locals
    def __init__(self, server_name, server_name_for_logs, port,
                 logger, default_log_dir, log_config_env, log_level_env,
                 request_limit=-1, max_workers=10, max_concurrent_rpcs=None,
                 protocol_services_by_name_values=None,
                 loop_sleep_seconds: float = ONE_MINUTE_IN_SECONDS,
                 server_loop_callbacks: ServerLoopCallbacks = None):
        """
        Constructor

        :param server_name: the name of the service for health reporting
                        purposes
        :param server_name_for_logs: the name of the service for logging
                purposes
        :param port: the port which will recieve requests
        :param logger: the logger to send output to
        :param default_log_dir: the default directory for logs
        :param log_config_env: the environment variable for logging config
        :param log_level_env: the environment variable for logging level
        :param request_limit: the maximum number of requests handled by the
                            service until the service attempts to exit and
                            restart to free up resource leaks. By default this
                            is -1, indicating there is no limit on the
                            number of requests. Note: to avoid the "reverse thundering herd" effect
                            where each replica of the service shuts down at the same time causing
                             an outage, the actual number of requests before shutdown is "fuzzed"
                             randomly at 10% either side of this value.
        :param max_workers: the maximum number of worker threads handling
                            requests
        :param max_concurrent_rpcs: the maximum number of concurrent RPCS
                            handled by the server.
        :param protocol_services_by_name_values: result of:
                    <protocol>_pb2.DESCRIPTOR.services_by_name.values()
                    Default is None
        :param loop_sleep_seconds: Number of seconds to sleep in the request
                    polling loop
        :param server_loop_callbacks: A ServerLoopCallbacks instance to allow
                    app-specific hooks into the main loop of the server.
        """

        self.start_time_since_epoch = time.time()

        # Before anything else, set up the logging
        self.server_name_for_logs = server_name_for_logs
        self.port = port
        self.logger = logger
        self.default_extra_logging_fields = {
            "source": self.server_name_for_logs,
            "thread_name": "Unknown",
            "request_id": "None",
            "user_id": "None",
            "group_id": "None",
            "run_id": "None",
            "experiment_id": "None"
        }
        self._setup_logging(default_log_dir, log_config_env, log_level_env)

        # Set up the remaining member variables from args
        self.server_name = server_name

        # Lower and upper bounds for number of requests before shutting down
        if request_limit == -1:
            # Unlimited requests
            self.shutdown_at = -1
        else:
            request_limit_lower = round(request_limit * 0.90)
            request_limit_upper = round(request_limit * 1.10)
            self.shutdown_at = random.randint(request_limit_lower, request_limit_upper)

        self.logger.info("Shutting down in %d requests.", self.shutdown_at)

        self.max_workers = max_workers
        self.max_concurrent_rpcs = max_concurrent_rpcs

        # Some placeholders for things we will set later on
        self.lock = RLock()
        self.server = None
        self.health = None

        # Turn this on to see request metadata for every request.
        self.log_request_metadata = False
        self.protocol_services_by_name_values = protocol_services_by_name_values

        # Initialize the stats table
        self.stats = {
            'NumProcessing': 0,
            'Serving': True,
            'Total': 0
        }
        self.loop_sleep_seconds = loop_sleep_seconds

        self.server_loop_callbacks = server_loop_callbacks
        if self.server_loop_callbacks is None:
            self.server_loop_callbacks = ServerLoopCallbacks()

    def create_server(self):
        """
        Called by client code to create the GRPC server instance.
        :return: A GRPC Server instance with health checking set up.
            This instance needs to be coupled to the GRPC *service* instance
            which is particular to the implementation (the service is the guy
            that has the request handling methods)
        """

        # pylint-protobuf cannot find enums defined within scope of a message
        # pylint: disable=protobuf-undefined-attribute,consider-using-with
        health_thread_pool = futures.ThreadPoolExecutor(max_workers=1)
        self.health = health.HealthServicer(
                        experimental_non_blocking=True,
                        experimental_thread_pool=health_thread_pool)
        self.health.set(self.server_name,
                        health_pb2.HealthCheckResponse.ServingStatus.NOT_SERVING)

        max_message_length = -1     # No limit to message length
        # pylint: disable=consider-using-with
        thread_pool = futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.server = grpc.server(
            thread_pool,
            maximum_concurrent_rpcs=self.max_concurrent_rpcs,
            options=[('grpc.max_send_message_length', max_message_length),
                     ('grpc.max_receive_message_length', max_message_length)])

        return self.server

    def run(self):
        """
        Called by client code after the service is all connected up.
        This encapsulates some other setup, the main loop, and code for
        smooth exiting.
        """

        self._set_up_health()
        self._set_up_ports()
        self._start_server()

        # Main polling loop in here
        self._poll_until_request_limit()

        self._drain_last_requests()

        self.server_loop_callbacks.shutdown_callback()

        # Finally stop the service
        self.server.stop(None)

    def setup_extra_logging_fields(self, context=None):
        """
        Sets up extra thread-specific fields to be logged with each
        log message.

        :param context: The grpc.ServicerContext. Default is None
        """

        extra = copy.copy(self.default_extra_logging_fields)
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

    def start_request(self, caller, requestor_id, context):
        """
        Called by client services to mark the beginning of a request
        inside their request methods.
        :param caller: A String representing the method called
                Stats will be kept as to how many times each method is called.
        :param requestor_id: A String representing other information about
                the requestor which will be logged in a uniform fashion.
        :param context: a grpc.ServicerContext
        :return: The RequestLoggerAdapter for the request
        """

        # Create the RequestLoggerAdapter
        self.setup_extra_logging_fields(context)
        request_log = RequestLoggerAdapter(self.logger, None)

        # Log that the request was received by the caller
        request_log.api("Received a %s request for %s",
                        str(caller), str(requestor_id))

        # Maybe log the request metadata
        if self.log_request_metadata and \
                context is not None:

            metadata = context.invocation_metadata()
            metadata_dict = GrpcMetadataUtil.to_dict(metadata)
            request_log.api("Request metadata %s", str(metadata_dict))

        # Update stats for the caller.
        # Take the lock because we are modifying stats
        is_serving = True
        stats_str = ""
        with self.lock:
            is_serving = self._is_still_serving()
            if is_serving:

                # Add to the total number of requests and check the value
                # to see if we should block any further request from being
                # processed because we will be shutting down
                self.stats['Total'] = self.stats.get('Total', 0) + 1

                # Keep track of the number of requests actively being processed
                self.stats['NumProcessing'] = self.stats.get('NumProcessing', 0) + 1

                # Keep track how many times the caller invoked us
                self.stats[caller] = self.stats.get(caller, 0) + 1

                # Maybe stop serving
                keep_going = self._keep_going()
                if not keep_going:
                    self._stop_serving()

                stats_str = str(self.stats)

        # We can do all this without the lock, making smaller critical section
        if not is_serving:
            message = f"Service refusing {str(caller)} request from {str(requestor_id)} to shut down cleanly"
            self.logger.info(message)
            context.abort(grpc.StatusCode.UNAVAILABLE, message)

        # Report
        request_log.metrics("Stats : %s", stats_str)
        return request_log

    def finish_request(self, caller, requestor_id, request_log):
        """
        Called by client services to mark the end of a request
        inside their request methods.
        :param caller: A String representing the method called
        :param requestor_id: A String representing other information about
                the requestor which will be logged in a uniform fashion.
        :param request_log: The RequestLoggerAdapter for the request
        """

        # Log that the request was finsihed by the caller
        request_log.api("Done with %s request for %s",
                        str(caller), str(requestor_id))

        # Keep track of the number of requests actively being processed
        # Take the lock because we are modifying stats
        stats_str = ""
        with self.lock:
            self.stats['NumProcessing'] = self.stats.get('NumProcessing', 0) - 1
            stats_str = str(self.stats)

        # Report
        request_log.metrics("Stats : %s", stats_str)

    def get_start_time_since_epoch(self):
        """
        :return: The start time of the server since the epoch
        """
        return self.start_time_since_epoch

    def get_server_name_for_logs(self):
        """
        :return: The server name for the logs
        """
        return self.server_name_for_logs

    def _setup_logging(self, default_log_dir, log_config_env, log_level_env):
        """
        Called by constructor
        """

        logging_setup = LoggingSetup(default_log_config_dir=default_log_dir,
                                     default_log_config_file="logging.json",
                                     default_log_level="DEBUG",
                                     log_config_env=log_config_env,
                                     log_level_env=log_level_env)
        logging_setup.setup()

        # Enable translation of log message args to MessageType
        StructuredLogRecord.set_up_record_factory()

        # Enable thread-local information to go into log messages
        ServiceLogRecord.set_up_record_factory(self.default_extra_logging_fields)
        self.setup_extra_logging_fields()

        self.logger.info("Starting %s on port %s...",
                         str(self.server_name_for_logs),
                         str(self.port))

    def _get_num_processing(self):
        return self.stats.get('NumProcessing', 0)

    def _is_still_serving(self):
        """
        Called by start_request() while holding the lock and also by
        _poll_until_request_limit() while not holding the lock (fine).
        """
        return self.stats.get('Serving', True)

    def _stop_serving(self):
        """
        Called from start_request() from a block that holds the lock.
        """

        self.stats['Serving'] = False

        self.logger.info("Registered as no longer serving")

        # Turn down the service in an orderly fashion so that the mesh can
        # turn up another replica if it is told too with in the policies cfg
        # pylint-protobuf cannot find enums defined within scope of a message
        # pylint: disable=protobuf-undefined-attribute
        self.health.set(self.server_name,
                        health_pb2.HealthCheckResponse.ServingStatus.NOT_SERVING)
        self.health.enter_graceful_shutdown()

    def _keep_going(self):
        '''
        Called by the start_request() method while holding a lock to see if
        we should continue with the current server instance or shut down so
        the infrastructure can stand up a new instance.
        '''

        # DEF: HACK!
        #
        # Normally we would just return True here, but...
        #
        # To counteract the effects of potential resource leaks, we report
        # NOT_SERVING after every (REQUEST_LIMIT ± 10%) requests so that the service
        # itself can be restarted by the kubernetes infrastructure.

        keep_at_it = self.shutdown_at == -1 or \
            self.stats['Total'] <= self.shutdown_at

        return keep_at_it

    def _set_up_health(self):

        # default setup
        services = [self.server_name, 'grpc.health.v1.Health']

        if self.protocol_services_by_name_values is not None:
            # Add by the example here:
            # https://github.com/grpc/grpc/blob/master/examples/python/xds/server.py#L61
            services = tuple(
                service.full_name
                for service in self.protocol_services_by_name_values) + (
                    reflection.SERVICE_NAME, health.SERVICE_NAME)

        reflection.enable_server_reflection(services, self.server)
        health_pb2_grpc.add_HealthServicer_to_server(self.health, self.server)

    def _set_up_ports(self):

        # All IPv6 interfaces should listen
        self.server.add_insecure_port(f"[::]:{self.port}")

    def _start_server(self):

        self.server.start()

        # Activate the instance as healthy
        # pylint-protobuf cannot find enums defined within scope of a message
        # pylint: disable=protobuf-undefined-attribute
        self.health.set(self.server_name,
                        health_pb2.HealthCheckResponse.ServingStatus.SERVING)
        self.logger.info("%s started.", str(self.server_name_for_logs))

    def _poll_until_request_limit(self):

        # Poll the service every so often to see if it thinks its instance
        # should keep going.  When it says no, break out of the loop
        # and report ill health so infrastructure can restart this service.
        try:
            while self._is_still_serving():
                self.server_loop_callbacks.loop_callback()
                time.sleep(self.loop_sleep_seconds)

        except KeyboardInterrupt:
            pass

    def _drain_last_requests(self):

        # Wait for the NumProcessing to go to 0 before issuing the stop
        # so that existing requests doesn't get truncated.
        # But we don't want to wait forever
        num_minutes_wait = 15
        while self._get_num_processing() > 0 \
                and num_minutes_wait > 0:

            time.sleep(ONE_MINUTE_IN_SECONDS)
            num_minutes_wait = num_minutes_wait - 1
