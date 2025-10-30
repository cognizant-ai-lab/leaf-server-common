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

import json
import logging

from google.protobuf.json_format import MessageToDict


# pylint: disable=too-few-public-methods
class Probe():
    '''
    Class to probe a particular object inside the service.
    '''

    def __init__(self, name, myobj):
        """
        :param name: The name of the object to report
        :param myobj: the object we wish to probe
        """

        obj_dict = None
        if myobj is not None:
            obj_dict = myobj
            if hasattr(myobj, 'DESCRIPTOR'):
                obj_dict = MessageToDict(myobj)

        json_dict = None
        if obj_dict is not None:
            json_dict = json.dumps(obj_dict, indent=4, sort_keys=True)

        logger = logging.getLogger(__name__)
        logger.info("XXX")
        logger.info("%s: %s", str(name), str(json_dict))
        logger.info("ZZZ")
