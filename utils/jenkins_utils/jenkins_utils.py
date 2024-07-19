"""Module provides a utility class for interacting with Jenkins."""

import os
import constants


class JenkinsUtils:
    """Utility class for interacting with Jenkins."""

    @staticmethod
    def save_git_status(
        hostname: str,
        status: str,
    ) -> None:
        """Save data to a file in the workspace directory.

        Args:
            hostname (str): The hostname of the Jenkins server.
            status (str): The status to save.

        Returns:
            None

        """

     # log the output to a workspace file for viewing later
        if not os.path.exists(os.path.join(constants.ARTEFACT_DIR + os.path.dirname("/git_status/"))):
            os.makedirs(os.path.join(constants.ARTEFACT_DIR + "/git_status/"))

        with open(
            os.path.join(constants.ARTEFACT_DIR + "/git_status/" + hostname + ".txt"),
            "w",
        ) as file:
            file.write(status)
