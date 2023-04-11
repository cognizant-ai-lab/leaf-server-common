
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
