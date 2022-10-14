
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

from leaf_common.session.grpc_metadata_util import GrpcMetadataUtil


# pylint: disable=too-few-public-methods
class GrpcMetadataForwarder():
    """
    Base class for setting up extra grpc metadata/header information
    to be forwarded from a grpc context.
    """

    def __init__(self, key_list):
        """
        Constructor.

        :param key_list: The list of string keys whose grpc metadata
                is to be forwarded.
        """
        self.key_list = key_list
        if self.key_list is None:
            self.key_list = []

    def forward(self, context):
        """
        Gets metadata key/value pairs from the grpc context
        and forwards them into a new metadata dictionary.

        :param context: The grpc context for the request
        :return: a dictionary of metadata that was able to be forwarded
                from the given context
        """
        forwarded_dict = {}

        # Get the request context metadata in dictionary form
        metadata = context.invocation_metadata()

        meta_dict = GrpcMetadataUtil.to_dict(metadata)
        if meta_dict is None:
            meta_dict = {}

        # Find the keys we want to forward (if they exist)
        # and put them in the returned dictionary
        for key in self.key_list:
            if key in meta_dict:
                forwarded_dict[key] = meta_dict.get(key)

        return forwarded_dict
