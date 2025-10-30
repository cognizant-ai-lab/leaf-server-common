
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
from typing import Dict


class RequestLogger():
    """
    An interface defining an API for services to call for logging
    the beginning and end of servicing their requests.
    """

    def start_request(self, caller, requestor_id, context,
                      service_logging_dict: Dict[str, str] = None):
        """
        Called by services to mark the beginning of a request
        inside their request methods.
        :param caller: A String representing the method called
                Stats will be kept as to how many times each method is called.
        :param requestor_id: A String representing other information about
                the requestor which will be logged in a uniform fashion.
        :param context: a grpc.ServicerContext
                from which structured logging fields can be derived from
                request metadata
        :param service_logging_dict: An optional service-specific dictionary
                from which structured logging fields can be derived from
                request-specific fields. When included, similarly named keys here
                will be overriden by those from the context above.
        :return: The RequestLoggerAdapter to be used throughout the
                processing of the request
        """
        raise NotImplementedError()

    def finish_request(self, caller, requestor_id, request_log):
        """
        Called by client services to mark the end of a request
        inside their request methods.
        :param caller: A String representing the method called
        :param requestor_id: A String representing other information about
                the requestor which will be logged in a uniform fashion.
        :param request_log: The RequestLoggerAdapter to be used throughout the
                processing of the request
        """
        raise NotImplementedError()
