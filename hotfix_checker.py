import sys
import git
from util.channel_access import ChannelAccessUtils
from enum import Enum
import requests


REMOTE_URL = 'https://github.com/ISISComputingGroup/EPICS'

instruments = ChannelAccessUtils().get_inst_list()
if len(instruments) == 0:
    raise IOError("No instruments found. This is probably because the instrument list PV is unavailable.")
else:
    # make list just the ['name'] part with 'NDX' in-front of it
    instruments = ["NDX" + instrument['name'] for instrument in instruments] 

instruments = ['testBranchForHotfixChecker']

class hotfix_status(Enum):
    NONE = 0
    HOTFIX_DETECTED = 1
    UNCOMMITTED_CHANGES = 2


instrument_no_hotfix = {}
instrument_hotfix_detected = {}
instrument_uncommitted_changes = {}


def check_instrument(hostname):
    print(f'Checking {hostname}')
    # connect to instrument/ get instrument branch details via it auto-pushing to get uncommitted changes
    # check if any hotfix commits on the branch hostname on, dont clone repo do this
    response = requests.get(f"{REMOTE_URL}/commits?sha={hostname}")

    if response.status_code == 200:
        commits = response.json()

        if len(commits) > 0:
            print(f"The branch '{hostname}' has hotfix commits.")
            instrument_hotfix_detected[hostname] = hotfix_status.HOTFIX_DETECTED

        else:
            print(f"The branch '{hostname}' has no hotfix commits.")
            instrument_no_hotfix[hostname] = hotfix_status.NONE
    else:
        print(f"ERROR: Failed to retrieve information. Status code: {response.status_code}")


    # check if any uncommitted changes
    # record details of both
    # disconnect from instrument


def check_all_scripts(instruments):
    print('Starting instrument hotfix checker')

    for instrument in instruments:
        check_instrument(instrument)

# Manual running (for the time being)
check_all_scripts(instruments)

# check if any instrument in hotfix_status_each_instrument has uncommitted changes
if len(instrument_uncommitted_changes) > 0:
    print("INFO: 0 hotfixes detected on: " + str(instrument_no_hotfix))
    print("INFO: 1+ Hotfixes detected on: " + str(instrument_hotfix_detected))
    # print("INFO: Uncommitted changes detected on: " + str(instrument_uncommitted_changes))
    sys.exit(1)
else:
    sys.exit(0)