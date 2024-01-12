import os
import sys
import git
from util.channel_access import ChannelAccessUtils
from enum import Enum



EPICS_DIR = os.environ['EPICS_DIR']
REMOTE_URL = 'https://github.com/ISISComputingGroup/EPICS'

instruments = ChannelAccessUtils().get_inst_list()
if len(instruments) == 0:
    raise IOError("No instruments found. This is probably because the instrument list PV is unavailable.")
else:
    # make list just the ['name'] part with 'NDX' in-front of it
    instruments = ["NDX" + instrument['name'] for instrument in instruments] 

instruments = ['testBranchForHotfixChecker']


instrument_no_hotfix = []
instrument_hotfix_detected = []
instrument_uncommitted_changes = []
unreachable_instruments = []


def check_instrument(hostname):
    print(f'Checking {hostname}')
    # connect to instrument/ get instrument branch details via it auto-pushing to get uncommitted changes
    # set repo from file path

    repo = git.Repo(EPICS_DIR)
    try:
        repo.git.checkout(hostname)
    except git.GitCommandError:
        print(f"Could not checkout branch '{hostname}'")
        unreachable_instruments.append(hostname)
        return
    
    repo.git.pull()

    commits = list(repo.iter_commits('HEAD', max_count=1))

    if len(commits) > 0:
        print(f"The branch '{hostname}' has hotfix commits.")
        instrument_hotfix_detected.append(hostname)
    else:
        print(f"The branch '{hostname}' has no hotfix commits.")
        instrument_no_hotfix.append(hostname)


    # check if any uncommitted changes run on each instrument
        
    # if repo.is_dirty():
    #     print(f"The branch '{hostname}' has uncommitted changes.")
    #     instrument_uncommitted_changes.append(hostname)
    # else:
    #     print(f"The branch '{hostname}' has no uncommitted changes.") 
    # record details of both
    # disconnect from instrument


def check_all_scripts(instruments):
    print('Starting instrument hotfix checker')

    for instrument in instruments:
        check_instrument(instrument)

# Manual running (for the time being)
check_all_scripts(instruments)

print("INFO: NO HOTFIXES detected on: " + str(instrument_no_hotfix))
print("INFO: 1+ HOTFIXES detected on: " + str(instrument_hotfix_detected))

# check if any instrument in hotfix_status_each_instrument has uncommitted changes
if len(instrument_uncommitted_changes) > 0 or len(unreachable_instruments) > 0: 
    print("ERROR: Uncommitted changes detected on: " + str(instrument_uncommitted_changes))
    print("ERROR: Unreachable instruments: " + str(unreachable_instruments))
    sys.exit(1)
else:
    sys.exit(0)