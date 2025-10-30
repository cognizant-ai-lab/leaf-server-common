
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

class ServerLoopCallbacks:
    """
    An interface for the the ServerLifetime to call which will
    reach out at certain points in the main server loop.
    """

    def loop_callback(self) -> bool:
        """
        Periodically called by the main server loop of ServerLifetime.
        :return: True if the server is considered active. False or None otherwise
        """
        # Do nothing
        return False

    def shutdown_callback(self):
        """
        Called by the main server loop when it's time to shut down.
        """
        # Do nothing
