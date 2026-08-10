"""Module provides a utility class for interacting with Jenkins."""

import os


class JenkinsUtils:
    """Utility class for interacting with Jenkins."""

    @staticmethod
    def save_git_status(
        hostname: str,
        status: str,
        file_suffix: str,
        artefact_dir: str,
    ) -> None:
        """Save data to a file in the workspace directory.

        Args:
            hostname (str): The hostname of the Jenkins server.
            status (str): The status to save.
            file_suffix (str): Suffix for filename.
            artefact_dir (str): The directory to save the status to.

        Returns:
            None

        """
        # log the output to a workspace file for viewing later
        if not os.path.exists(os.path.join(artefact_dir, "git_status")):
            os.makedirs(os.path.join(artefact_dir, "git_status"))

        with open(
            os.path.join(artefact_dir, "git_status", f"{hostname}{file_suffix}.txt"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(status)
