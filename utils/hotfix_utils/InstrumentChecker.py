"""A module for checking the status of an instrument in relation to it's repo."""
import os
from typing import Union

from ..communication_utils.ssh_access import (
    SSHAccessUtils,
)
from ..jenkins_utils.jenkins_utils import JenkinsUtils
from .check import CHECK


class InstrumentChecker:
    """A class to represent an instrument in relation to the it's repo status."""

    repo_dir = os.environ["REPO_DIR"]

    def __init__(self, hostname: str) -> None:
        """Initialize the Instrument object.

        Args:
            hostname (str): The hostname of the instrument.

        """
        self._hostname = hostname

        self._commits_local_not_on_upstream_enum = None
        self._commits_local_not_on_upstream_messages = None

        self._commits_upstream_not_on_local_enum = None
        self._commits_upstream_not_on_local_enum_messages = None

        self._uncommitted_changes_enum = None

    @property
    def hostname(self) -> str:
        """Get the hostname of the instrument.

        Returns:
            str: The hostname of the instrument.

        """
        return self._hostname

    def check_for_uncommitted_changes(self) -> CHECK:
        """Check if there are any uncommitted changes on the instrument via SSH.

        Args:
            hostname (str): The hostname to connect to.

        Returns:
            CHECK: The result of the check.

        """
        command = f"cd {self.repo_dir} && git status --porcelain"
        ssh_process = SSHAccessUtils.run_ssh_commandd(
            self.hostname,
            os.environ["SSH_CREDENTIALS_USR"],
            os.environ["SSH_CREDENTIALS_PSW"],
            command,
        )

        if os.environ["DEBUG_MODE"] == "true":
            print(f"DEBUG: Running command {command}")

        # if os.environ["DEBUG_MODE"] == "true":
        #     print(f"DEBUG: {ssh_process}")

        if ssh_process["success"]:
            status = ssh_process["output"]

            JenkinsUtils.save_git_status(self.hostname, status, os.environ["WORKSPACE"])

            if status.strip() != "":
                return CHECK.TRUE
            else:
                return CHECK.FALSE
        else:
            return CHECK.UNDETERMINABLE

    def get_parent_epics_branch(
        self,
        hostname: str,
    ) -> Union[str | bool]:
        """Get the parent branch of the instrument branch.

        Args:
            hostname (str): The hostname to connect to.

        Returns:
            str: The name of the parent branch.

        """
        command = f"cd {self.repo_dir} && git log"
        ssh_process = SSHAccessUtils.run_ssh_commandd(
            hostname,
            os.environ["SSH_CREDENTIALS_USR"],
            os.environ["SSH_CREDENTIALS_PSW"],
            command,
        )
        if ssh_process["success"]:
            if "galil-old" in ssh_process["output"]:
                return "origin/galil-old"
            else:
                return "origin/main"
        else:
            return False

    def git_branch_comparer(
        self,
        hostname: str,
        changes_on: str,
        subtracted_against: str = None,
        prefix: str = None,
    ) -> CHECK:
        """Get the commit messages between two branches on the instrument.

        Args:
            hostname (str): The hostname to connect to.
            changes_on (str): The branch to start from.
            subtracted_against (str): The branch to end at.
            prefix (str): The prefix to check for in commit messages.

        Returns:
            CHECK: The result of the check.
            dict: A dictionary with the commit messages and their hashes.

        """
        branch_details = None
        if changes_on and subtracted_against:
            branch_details = f"{subtracted_against}..{changes_on}"
        else:
            branch_details = ""

        # fetch latest changes from the remote
        fetch_command = f"cd {self.repo_dir} && git fetch origin"
        ssh_process_fetch = SSHAccessUtils.run_ssh_commandd(
            hostname,
            os.environ["SSH_CREDENTIALS_USR"],
            os.environ["SSH_CREDENTIALS_PSW"],
            fetch_command,
        )

        if os.environ["DEBUG_MODE"] == "true":
            print(f"DEBUG: Running command {fetch_command}")

        # if os.environ["DEBUG_MODE"] == "true":
        #     print(f"DEBUG: {ssh_process_fetch}")

        if not ssh_process_fetch["success"]:
            return (
                CHECK.UNDETERMINABLE,
                None,
            )

        command = f'cd {self.repo_dir} && git log --format="%h %s" {branch_details}'
        if os.environ["DEBUG_MODE"] == "true":
            print(f"DEBUG: Running command {command}")

        ssh_process = SSHAccessUtils.run_ssh_commandd(
            hostname,
            os.environ["SSH_CREDENTIALS_USR"],
            os.environ["SSH_CREDENTIALS_PSW"],
            command,
        )

        # if os.environ["DEBUG_MODE"] == "true":
        #    print(f"DEBUG: {ssh_process}")

        if ssh_process["success"]:
            output = ssh_process["output"]
            commit_dict = self.split_git_log(output, prefix)

            if len(commit_dict) > 0:
                return (
                    CHECK.TRUE,
                    commit_dict,
                )
            else:
                return (
                    CHECK.FALSE,
                    None,
                )

        else:
            return (
                CHECK.UNDETERMINABLE,
                None,
            )

    def split_git_log(self, git_log: str, prefix: str) -> dict:
        """Split the git log into a dictionary of commit hashes and messages.

        Args:
            git_log (str): The git log to split.

        Returns:
            dict: A dictionary with the commit hashes as keys and the commit messages as values.

        """
        commit_dict = {}
        commit_lines = git_log.split("\n")
        commit_lines = [line for line in commit_lines if line.strip() != ""]
        for line in commit_lines:
            split_line = line.split(
                " ",
                1,
            )
            hash = split_line[0]
            message = split_line[1]
            if prefix is None or message.startswith(prefix):
                commit_dict[hash] = message
        return commit_dict

    # TODO: Improve this function to allow selecting of what checks to run and combine the uncommited one to this function
    def check_instrument(self) -> dict:
        """Check if there are any hotfixes or uncommitted changes on AN instrument.

        Returns:
            dict: A dictionary with the result of the checks.

        """
        # Examples of how to use the git_branch_comparer function decided to not be used in this iteration of the check
        # Check if any hotfixes run on the instrument with the prefix "Hotfix:"
        # hotfix_commits_enum, hotfix_commits_messages = git_branch_comparer(
        #     hostname, prefix="Hotfix:")

        # Check if any unpushed commits run on the instrument
        upstream_branch = None
        if os.environ["UPSTREAM_BRANCH_CONFIG"] == "hostname":
            upstream_branch = "origin/" + self.hostname
        elif os.environ["UPSTREAM_BRANCH_CONFIG"] == "epics":
            # used for EPICS repo to get the parent branch of the instrument branch
            upstream_branch = self.get_parent_epics_branch(self.hostname)
        elif os.environ["UPSTREAM_BRANCH_CONFIG"] == "main":
            upstream_branch = "origin/main"
        elif os.environ["UPSTREAM_BRANCH_CONFIG"] == "master":
            upstream_branch = "origin/master"
        else:
            # if the UPSTREAM_BRANCH_CONFIG is not set to any of the above,  set it to the value of the environment variable assuming user wants custom branch
            upstream_branch = os.environ["UPSTREAM_BRANCH_CONFIG"]

        # Check if any upstream commits are not on the instrument, default to the parent origin branch, either main or galil-old
        (
            self.commits_upstream_not_on_local_enum,
            self.commits_upstream_not_on_local_messages,
        ) = self.git_branch_comparer(
            self.hostname,
            changes_on=upstream_branch,
            subtracted_against="HEAD",
            prefix=None,
        )

        # print(self.commits_upstream_not_on_local_enum, self.commits_upstream_not_on_local_messages)

        (
            self.commits_local_not_on_upstream_enum,
            self.commits_local_not_on_upstream_messages,
        ) = self.git_branch_comparer(
            self.hostname,
            changes_on="HEAD",
            subtracted_against=upstream_branch,  # for inst scripts repo
            prefix=None,
        )

        # Check if any uncommitted changes run on the instrument
        self.uncommitted_changes_enum = self.check_for_uncommitted_changes()


    def as_string(self) -> str:
        """Return the Instrument object as a string.

        Returns:
            str: The Instrument object as a string.

        """
        return f"Hostname: {self.hostname} - Uncommitted changes: {self.uncommitted_changes_enum} - Commits on local not on upstream: {self.commits_local_not_on_upstream_enum} - Commits on upstream not on local: {self.commits_upstream_not_on_local_enum}"
