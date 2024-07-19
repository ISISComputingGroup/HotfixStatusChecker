"""The script checks for uncommitted changes and unpushed/unpulled commits."""

import os
import sys
from enum import (
    Enum,
)
from typing import Union

import requests

import constants
from utils.communication_utils.channel_access import (
    ChannelAccessUtils,
)
from utils.communication_utils.ssh_access import (
    SSHAccessUtils,
)
from utils.jenkins_utils.jenkins_utils import JenkinsUtils


class CHECK(Enum):
    """An enumeration of the possible results of a check."""

    UNDETERMINABLE = 0
    TRUE = 1
    FALSE = 2


class Instrument:
    """A class to represent an instrument in relation to the it's repo status."""

    def __init__(self, hostname: str) -> None:
        """Initialize the Instrument object.

        Args:
            hostname (str): The hostname of the instrument.

        """
        self._hostname = hostname
        self._unpushed_commits_enum = None
        self._unpushed_commit_messages = None

        self.uncommitted_changes_enum = None

    @property
    def hostname(self) -> str:
        """Get the hostname of the instrument.

        Returns:
            str: The hostname of the instrument.

        """
        return self._hostname


    @property
    def unpushed_commits_enum(self) -> CHECK:
        """Get the result of the check for unpushed commits.

        Returns:
            CHECK: The result of the check.

        """
        return self._unpushed_commits_enum
    
    @unpushed_commits_enum.setter
    def unpushed_commits_enum(self, value: CHECK) -> None:
        """Set the result of the check for unpushed commits.

        Args:
            value (CHECK): The result of the check.

        """
        self._unpushed_commits_enum = value
    
    @property
    def unpushed_commit_messages(self) -> dict:
        """Get the commit messages of the unpushed commits.

        Returns:
            dict: A dictionary with the commit messages and their hashes.

        """
        return self._unpushed_commit_messages
    
    @unpushed_commit_messages.setter
    def unpushed_commit_messages(self, value: dict) -> None:
        """Set the commit messages of the unpushed commits.

        Args:
            value (dict): A dictionary with the commit messages and their hashes.

        """
        self._unpushed_commit_messages = value

    
    
    @property
    def uncommitted_changes_enum(self) -> CHECK:
        """Get the result of the check for uncommitted changes.

        Returns:
            CHECK: The result of the check.

        """
        return self._uncommitted_changes_enum
    
    @uncommitted_changes_enum.setter
    def uncommitted_changes_enum(self, value: CHECK) -> None:
        """Set the result of the check for uncommitted changes.

        Args:
            value (CHECK): The result of the check.

        """
        self._uncommitted_changes_enum = value
    



    def check_for_uncommitted_changes(self) -> CHECK:
        """Check if there are any uncommitted changes on the instrument via SSH.

        Args:
            hostname (str): The hostname to connect to.

        Returns:
            CHECK: The result of the check.

        """
        command = f"cd {constants.REPO_DIR} && git status --porcelain"
        ssh_process = SSHAccessUtils.runSSHCommand(
            self.hostname,
            constants.SSH_USERNAME,
            constants.SSH_PASSWORD,
            command,
        )

        if constants.DEBUG_MODE:
            print(f"DEBUG: {ssh_process}")

        if ssh_process["success"]:
            status = ssh_process["output"]

            JenkinsUtils.save_git_status(self.hostname, status)

            if status.strip() != "":
                return CHECK.TRUE
            else:
                return CHECK.FALSE
        else:
            return CHECK.UNDETERMINABLE


    # def get_parent_branch(
    #     hostname: str,
    # ) -> Union[str | bool]:
    #     """Get the parent branch of the instrument branch.

    #     Args:
    #         hostname (str): The hostname to connect to.

    #     Returns:
    #         str: The name of the parent branch.

    #     """
    #     command = f"cd {constants.REPO_DIR} && git log"
    #     ssh_process = SSHAccessUtils.runSSHCommand(
    #         hostname,
    #         constants.SSH_USERNAME,
    #         constants.SSH_PASSWORD,
    #         command,
    #     )
    #     if ssh_process["success"]:
    #         if "galil-old" in ssh_process["output"]:
    #             return "origin/galil-old"
    #         else:
    #             return "origin/main"
    #     else:
    #         return False


    def git_branch_comparer(self, 
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
        fetch_command = f"cd {constants.REPO_DIR} && git fetch origin"
        ssh_process_fetch = SSHAccessUtils.runSSHCommand(
            hostname,
            constants.SSH_USERNAME,
            constants.SSH_PASSWORD,
            fetch_command,
        )

        if constants.DEBUG_MODE:
            print(f"DEBUG: {ssh_process_fetch}")

        if not ssh_process_fetch["success"]:
            return (
                CHECK.UNDETERMINABLE,
                None,
            )

        command = f'cd {constants.REPO_DIR} && git log --format="%h %s" {branch_details}'
        if constants.DEBUG_MODE:
            print(f"DEBUG: Running command {command}")

        ssh_process = SSHAccessUtils.runSSHCommand(
            hostname,
            constants.SSH_USERNAME,
            constants.SSH_PASSWORD,
            command,
        )

        if constants.DEBUG_MODE:
           print(f"DEBUG: {ssh_process}")

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

    #TODO: Improve this function to allow selecting of what checks to run and combine the uncommited one to this function   
    def check_instrument(self
    ) -> dict:
        """Check if there are any hotfixes or uncommitted changes on AN instrument.

        Returns:
            dict: A dictionary with the result of the checks.

        """

        

        # Examples of how to use the git_branch_comparer function decided to not be used in this iteration of the check
        # Check if any hotfixes run on the instrument with the prefix "Hotfix:"
        # hotfix_commits_enum, hotfix_commits_messages = git_branch_comparer(
        #     hostname, prefix="Hotfix:")

        # Check if any upstream commits are not on the instrument, default to the parent origin branch, either main or galil-old
        # commits_pending_pulling_enum = git_branch_comparer(
        #     hostname, changes_on=get_parent_branch(hostname), subtracted_against=hostname, prefix=None)

        # Check if any unpushed commits run on the instrument
        upstream_branch = None
        if constants.UPSTREAM_BRANCH == "hostname":
            upstream_branch = "origin/" + self.hostname
        else:
            upstream_branch = "origin/" + constants.UPSTREAM_BRANCH
        (
            self._unpushed_commits_enum,
            self._unpushed_commit_messages,
        ) = self.git_branch_comparer(
            self.hostname,
            changes_on="HEAD",
            # subtracted_against="origin/" + self.hostname,
            subtracted_against=upstream_branch, # for inst scripts repo
            prefix=None,
        )

        # Check if any uncommitted changes run on the instrument
        self.uncommitted_changes_enum = self.check_for_uncommitted_changes()

        # # return the result of the checks
        # instrument_status = {
        #     "commits_not_pushed_messages": unpushed_commit_messages,
        #     "commits_not_pushed": unpushed_commits_enum,
        #     "uncommitted_changes": uncommitted_changes_enum,
        # }

        # return instrument_status

    


class InstrumentRepoChecker:

    @staticmethod
    def get_insts_on_latest_ibex_via_inst_congif() -> list:
        """Get a list of instruments that are on the latest version of IBEX.

        Returns:
            list: A list of instruments that are on the latest version of IBEX.

        """
        instrument_list = ChannelAccessUtils().get_inst_list()
        result_list = []
        for instrument in instrument_list:
            if not instrument["seci"]:
                version = requests.get(
                    constants.INST_CONFIG_VERSION_TXT_RAW_DATA_URL + instrument["hostName"]
                ).text
                version_first_number = int(version.strip().split(".")[0])
                if constants.DEBUG_MODE:
                    print(
                        f"DEBUG: Found instrument {instrument['name']} on IBEX version {version_first_number}"
                    )
                if (
                    version_first_number is not None
                    and version_first_number != "None"
                    and version_first_number != ""
                ):
                    result_list.append(
                        {
                            "hostname": instrument["hostName"],
                            "version": version_first_number,
                        }
                    )

        # Get the latest version of IBEX
        latest_version = max([inst["version"] for inst in result_list])
        second_latest_version = sorted(set([inst["version"] for inst in result_list]))[-2]

        # filter out the instruments that are not on the latest version
        insts_on_latest_ibex = [
            inst["hostname"] for inst in result_list if (inst["version"] == latest_version or inst["version"] == second_latest_version)
        ]

        return insts_on_latest_ibex


    

    

    def check_instruments(self) -> None:
        """Run checks on all instruments to find hotfix/changes and log the results.

        Returns:
            None

        """
        if constants.USE_TEST_INSTRUMENT_LIST:
            instrument_list = constants.TEST_INSTRUMENT_LIST.split(",")
            instrument_list = [instrument.strip() for instrument in instrument_list]
            if "" in instrument_list:
                instrument_list.remove("")
        else:
            instrument_list = self.get_insts_on_latest_ibex_via_inst_congif()

        instrument_status_lists = {
            "uncommitted_changes": [],
            "undeterminable_at_some_point": [],
            "unpushed_commits": [],
        }

        #TODO - sort out this shitshow of a loop

        for instrument in instrument_list:
            instrument = Instrument(instrument)
            try:
                print(f"INFO: Checking {instrument.hostname}")
                instrument.check_instrument()
                if instrument.unpushed_commits_enum == CHECK.TRUE:
                    instrument_status_lists["unpushed_commits"].append(
                        instrument.hostname
                        + " "
                        + str(instrument.unpushed_commit_messages)
                    )
                elif (
                    instrument.unpushed_commits_enum == CHECK.UNDETERMINABLE
                    and instrument
                    not in instrument_status_lists["undeterminable_at_some_point"]
                ):
                    instrument_status_lists["undeterminable_at_some_point"].append(instrument.hostname)

                if instrument.uncommitted_changes_enum == CHECK.TRUE:
                    instrument_status_lists["uncommitted_changes"].append(instrument.hostname)
                elif (
                    instrument.uncommitted_changes_enum == CHECK.UNDETERMINABLE
                    and instrument
                    not in instrument_status_lists["undeterminable_at_some_point"]
                ):
                    instrument_status_lists["undeterminable_at_some_point"].append(instrument.hostname)
            except Exception as e:
                print(f"ERROR: Could not connect to {instrument.hostname} ({str(e)})")
                if instrument not in instrument_status_lists["undeterminable_at_some_point"]:
                    instrument_status_lists["undeterminable_at_some_point"].append(instrument.hostname)

        print("INFO: Summary of results")
        if len(instrument_status_lists["uncommitted_changes"]) > 0:
            message_prefix = "ERROR: Uncommitted changes:"
            print(f"{message_prefix} { instrument_status_lists['uncommitted_changes']}")
        else:
            print(f"Uncommitted changes: { instrument_status_lists['uncommitted_changes']}")
        if len(instrument_status_lists["unpushed_commits"]) > 0:
            message_prefix = "ERROR: Commits not pushed:"
            print(f"{message_prefix} { instrument_status_lists['unpushed_commits']}")
        else:
            message_prefix = "Commits not pushed:"
            print(f"{message_prefix} {instrument_status_lists['unpushed_commits']}")

        if len(instrument_status_lists["undeterminable_at_some_point"]) > 0:
            message_prefix = "ERROR: undeterminable at some point: "
            print(
                f"{message_prefix} {instrument_status_lists['undeterminable_at_some_point']}"
            )
        else:
            message_prefix = "undeterminable at some point: "
            print(
                f"{message_prefix} {instrument_status_lists['undeterminable_at_some_point']}"
            )

        # Check if any instrument in hotfix_status_each_instrument
        # has uncommitted changes or is undeterminable
        if len(instrument_status_lists["uncommitted_changes"]) > 0:
            sys.exit(1)
        if len(instrument_status_lists["undeterminable_at_some_point"]) > 0:
            sys.exit(1)
        if len(instrument_status_lists["unpushed_commits"]) > 0:
            sys.exit(1)

        # If no instruments have uncommitted changes or are undeterminable,
        # exit with ok status
        sys.exit(0)


if __name__ == "__main__": 
    InstrumentRepoChecker().check_instruments()
