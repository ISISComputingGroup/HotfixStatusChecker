"""Contains the RepoChecker class which is used to check the status of a specified repo on an instrument."""

import os
import sys

import requests
from packaging.version import InvalidVersion, Version

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

    # You can get the versions of insts a variety of ways, inst config, CS:VERSION:SVN:REV pv etc
    def get_insts_on_latest_ibex_via_inst_config(self) -> list:
        """Get a list of instruments that are on the latest version of IBEX.

        Returns:
            list: A list of instruments that are on the latest version of IBEX.

        """
        instrument_list = ChannelAccessUtils().get_inst_list()
        result_list = []
        for instrument in instrument_list:
            if not instrument["seci"]:
                version_string = requests.get(
                    "https://control-svcs.isis.cclrc.ac.uk/git/?p=instconfigs/inst.git;a=blob_plain;f=configurations/config_version.txt;hb=refs/heads/"
                    + instrument["hostName"]
                ).text
                try:
                    version = Version(version_string)

                    if self.debug_mode:
                        print(
                            f"DEBUG: Found instrument {instrument['name']} on IBEX version {version}"
                        )
                    result_list.append(
                        {
                            "hostname": instrument["hostName"],
                            "version": version,
                        }
                    )
                except InvalidVersion as e:
                    print(
                        f"Could not parse {instrument['name']}'s Version({version_string}): {str(e)}"
                    )

        # Get the latest versions of IBEX
        versions = sorted(set([inst["version"] for inst in result_list]))

        latest_major_version = versions[-1].major
        second_latest_major_version = latest_major_version - 1
        print(
            f"INFO: checking versions {latest_major_version}.x.x and {second_latest_major_version}.x.x"
        )

        # filter out the instruments that are not on the latest version
        insts_on_latest_ibex = [
            inst["hostname"]
            for inst in result_list
            if (inst["version"].major in [latest_major_version, second_latest_major_version])
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
            instrument_list = self.get_insts_on_latest_ibex_via_inst_config()

        instrument_status_lists = {
            self._uncommitted_changes_key: [],
            self._undeterminable_at_some_point_key: [],
            self._commits_on_local_not_upstream_key: [],
            self._commits_on_upstream_not_local_key: [],
        }

        def update_instrument_status_lists(instrument, status_list_key, messages=None):
            if messages:
                instrument_status_lists[status_list_key].append({instrument.hostname: messages})
            else:
                instrument_status_lists[status_list_key].append(instrument.hostname)

        for hostname in instrument_list:
            instrument = InstrumentChecker(hostname)
            try:
                print(f"INFO: Checking {instrument.hostname}")
                instrument.check_instrument()
                if os.environ["DEBUG_MODE"] == "true":
                    print(instrument.as_string())

                if instrument.commits_local_not_on_upstream_enum == CHECK.TRUE:
                    update_instrument_status_lists(
                        instrument,
                        self._commits_on_local_not_upstream_key,
                        instrument.commits_local_not_on_upstream_messages,
                    )

                if instrument.uncommitted_changes_enum == CHECK.TRUE:
                    update_instrument_status_lists(
                        instrument,
                        self._uncommitted_changes_key,
                        instrument.uncommitted_changes_messages,
                    )

                if instrument.commits_upstream_not_on_local_enum == CHECK.TRUE:
                    update_instrument_status_lists(
                        instrument,
                        self._commits_on_upstream_not_local_key,
                        instrument.commits_upstream_not_on_local_messages,
                    )

                if (
                    instrument.commits_local_not_on_upstream_enum == CHECK.UNDETERMINABLE
                    or instrument.uncommitted_changes_enum == CHECK.UNDETERMINABLE
                    or instrument.commits_upstream_not_on_local_enum == CHECK.UNDETERMINABLE
                ):
                    update_instrument_status_lists(
                        instrument, self._undeterminable_at_some_point_key
                    )

            except Exception as e:
                print(f"ERROR: Could not connect to {instrument.hostname} ({str(e)})")
                update_instrument_status_lists(instrument, self._undeterminable_at_some_point_key)

        keys_and_prefixes = [
            (self._uncommitted_changes_key, "Uncommitted changes"),
            (self._commits_on_local_not_upstream_key, "Commits on local not upstream"),
            (self._commits_on_upstream_not_local_key, "Commits on upstream not on local"),
            (self._undeterminable_at_some_point_key, "Undeterminable at some point"),
        ]

        print("INFO: Summary of results")
        for key, prefix in keys_and_prefixes:
            status_list = instrument_status_lists[key]
            if len(status_list) > 0:
                print(f"ERROR: {prefix}: {status_list}".replace("'", '"'))
            else:
                print(f"{prefix}: {status_list}".replace("'", '"'))

        for key in instrument_status_lists:
            if len(instrument_status_lists[key]) > 0:
                sys.exit(1)

        # If no instruments have uncommitted changes, local branch matches upstream branch, and no undeterminable results then
        # exit with ok status
        sys.exit(0)
