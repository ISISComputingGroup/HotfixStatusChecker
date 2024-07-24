"""Contains the RepoChecker class which is used to check the status of a specified repo on an instrument."""

import os
import sys

import requests

from utils.hotfix_utils.InstrumentChecker import InstrumentChecker

from ..communication_utils.channel_access import (
    ChannelAccessUtils,
)
from ..hotfix_utils.check import CHECK


class RepoChecker:
    """A class to represent a repo checker."""

    _uncommitted_changes_key = "uncommitted_changes"
    _undeterminable_at_some_point_key = "undeterminable_at_some_point"
    _commits_on_local_not_upstream_key = "commits_on_local_not_upstream"
    _commits_on_upstream_not_local_key = "commits_on_upstream_not_local"

    def __init__(self) -> None:
        """Initialize the RepoChecker object."""
        self.use_test_inst_list = os.environ["USE_TEST_INSTRUMENT_LIST"] == "true"
        self.test_inst_list = os.environ["TEST_INSTRUMENT_LIST"]
        self.debug_mode = os.environ["DEBUG_MODE"] == "true"

    # you can get the versions of insts a variety of ways, inst config, CS:VERSION:SVN:REV pv etc
    def get_insts_on_latest_ibex_via_inst_congif(self) -> list:
        """Get a list of instruments that are on the latest version of IBEX.

        Returns:
            list: A list of instruments that are on the latest version of IBEX.

        """
        instrument_list = ChannelAccessUtils().get_inst_list()
        result_list = []
        for instrument in instrument_list:
            if not instrument["seci"]:
                version = requests.get(
                    "https://control-svcs.isis.cclrc.ac.uk/git/?p=instconfigs/inst.git;a=blob_plain;f=configurations/config_version.txt;hb=refs/heads/"
                    + instrument["hostName"]
                ).text
                version_first_number = int(version.strip().split(".")[0])
                if self.debug_mode:
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
        versions = sorted(set([inst["version"] for inst in result_list]))
        latest_version = versions[-1]
        second_latest_version = versions[-2]

        # filter out the instruments that are not on the latest version
        insts_on_latest_ibex = [
            inst["hostname"]
            for inst in result_list
            if (
                inst["version"] == latest_version
                or inst["version"] == second_latest_version
            )
        ]

        return insts_on_latest_ibex

    def check_instruments(self) -> None:
        """Run checks on all instruments to find hotfix/changes and log the results.

        Returns:
            None

        """
        if self.use_test_inst_list:
            instrument_list = self.test_inst_list.split(",")
            instrument_list = [instrument.strip() for instrument in instrument_list]
            if "" in instrument_list:
                instrument_list.remove("")
        else:
            print("INFO: Getting list of instruments on the 2 latest versions of IBEX")
            instrument_list = self.get_insts_on_latest_ibex_via_inst_congif()

        instrument_status_lists = {
            self._uncommitted_changes_key: [],
            self._undeterminable_at_some_point_key: [],
            self._commits_on_local_not_upstream_key: [],
            self._commits_on_upstream_not_local_key: [],
        }

        # TODO - sort out this shitshow of a loop

        for hostname in instrument_list:
            instrument = InstrumentChecker(hostname)
            try:
                print(f"INFO: Checking {instrument.hostname}")
                instrument.check_instrument()
                if os.environ["DEBUG_MODE"] == "true":
                    print(instrument.as_string())

                if instrument.commits_local_not_on_upstream_enum == CHECK.TRUE:
                    instrument_status_lists[
                        self._commits_on_local_not_upstream_key
                    ].append(
                        f"{instrument.hostname} {instrument.commits_local_not_on_upstream_messages}"
                    )
                elif (
                    instrument.commits_local_not_on_upstream_enum
                    == CHECK.UNDETERMINABLE
                    and instrument.hostname
                    not in instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ]
                ):
                    instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ].append(instrument.hostname)

                if instrument.uncommitted_changes_enum == CHECK.TRUE:
                    instrument_status_lists[self._uncommitted_changes_key].append(
                        instrument.hostname
                    )
                elif (
                    instrument.uncommitted_changes_enum == CHECK.UNDETERMINABLE
                    and instrument.hostname
                    not in instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ]
                ):
                    instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ].append(instrument.hostname)

                if instrument.commits_upstream_not_on_local_enum == CHECK.TRUE:
                    instrument_status_lists[
                        self._commits_on_upstream_not_local_key
                    ].append(
                        f"{instrument.hostname} {instrument.commits_upstream_not_on_local_messages}"
                    )

                elif (
                    instrument.commits_upstream_not_on_local_enum
                    == CHECK.UNDETERMINABLE
                    and instrument.hostname
                    not in instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ]
                ):
                    instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ].append(instrument.hostname)

            except Exception as e:
                print(f"ERROR: Could not connect to {instrument.hostname} ({str(e)})")
                if (
                    instrument
                    not in instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ]
                ):
                    instrument_status_lists[
                        self._undeterminable_at_some_point_key
                    ].append(instrument.hostname)

        print("INFO: Summary of results")
        if len(instrument_status_lists[self._uncommitted_changes_key]) > 0:
            message_prefix = "ERROR: Uncommitted changes:"
            print(f"{message_prefix} { instrument_status_lists['uncommitted_changes']}")
        else:
            print(
                f"Uncommitted changes: { instrument_status_lists['uncommitted_changes']}"
            )
        if len(instrument_status_lists[self._commits_on_local_not_upstream_key]) > 0:
            message_prefix = "ERROR: Commits on local not upstream:"
            print(
                f"{message_prefix} { instrument_status_lists[self._commits_on_local_not_upstream_key]}"
            )
        else:
            message_prefix = "Commits on local not upstream:"
            print(
                f"{message_prefix} {instrument_status_lists[self._commits_on_local_not_upstream_key]}"
            )

        if len(instrument_status_lists[self._commits_on_upstream_not_local_key]) > 0:
            message_prefix = "ERROR: Commits on upstream not on local:"
            print(
                f"{message_prefix} {instrument_status_lists['commits_on_upstream_not_local']}"
            )
        else:
            message_prefix = "Commits on upstream not on local:"
            print(
                f"{message_prefix} {instrument_status_lists['commits_on_upstream_not_local']}"
            )

        if len(instrument_status_lists[self._undeterminable_at_some_point_key]) > 0:
            message_prefix = "ERROR: undeterminable at some point: "
            print(
                f"{message_prefix} {instrument_status_lists[self._undeterminable_at_some_point_key]}"
            )
        else:
            message_prefix = "undeterminable at some point: "
            print(
                f"{message_prefix} {instrument_status_lists[self._undeterminable_at_some_point_key]}"
            )

        for key in instrument_status_lists:
            if len(instrument_status_lists[key]) > 0:
                sys.exit(1)

        # If no instruments have uncommitted changes or are undeterminable,
        # exit with ok status
        sys.exit(0)
