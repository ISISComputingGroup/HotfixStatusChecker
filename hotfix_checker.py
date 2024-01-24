import os
import subprocess
import sys
import git
from util.channel_access import ChannelAccessUtils
# import socket
# from ssh.session import Session
# from ssh import options
# make sure paramiko is installed on the machine running this script
import paramiko

EPICS_DIR = os.environ['EPICS_DIR']
REMOTE_URL = 'https://github.com/ISISComputingGroup/EPICS'
SSH_PORT = 22

# get the inst username and pw from Jenkins paramters
SSH_USERNAME = os.environ['SSH_USERNAME']
SSH_PASSWORD = os.environ['SSH_PASSWORD']

instruments = ChannelAccessUtils().get_inst_list()
if len(instruments) == 0:
    raise IOError("No instruments found. This is probably because the instrument list PV is unavailable.")
else:
    # make list just the ['name'] part with 'NDX' in-front of it
    instruments = ["NDX" + instrument['name'] for instrument in instruments] 

instruments = ['NDXSCIDEMO']


instrument_no_hotfix = []
instrument_hotfix_detected = []
instrument_uncommitted_changes = []
unreachable_instruments = []


def runssh(host, username, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=SSH_PORT, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        client.close()
        if error:
            return {'success': False, 'output': error}
        else:
            return {'success': True, 'output': output}
    except Exception as e:
        print(str(e))
        return {'success': False, 'output': str(e)}

def check_for_uncommitted_changes(hostname):
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git status"
    ssh_process = runssh(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        if "nothing to commit, working tree clean" not in ssh_process['output']:
            print(f"Uncommitted changes detected on {hostname}")
            instrument_uncommitted_changes.append(hostname)
    else:
        print(f"Error: {ssh_process['output']}")


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

    commits = repo.git.rev_list('--count', hostname)
    # print(commits)
    # initial creation fo branch seems to count as a commit when using git rev-list --count branch-name
    if int(commits) > 1:
        print(f"The branch '{hostname}' has hotfix commits.")
        instrument_hotfix_detected.append(hostname)
    else:
        print(f"The branch '{hostname}' has no hotfix commits.")
        instrument_no_hotfix.append(hostname)

    # check if any uncommitted changes run on each instrument
    check_for_uncommitted_changes(hostname)
    if hostname in instrument_uncommitted_changes:
        print(f"The branch '{hostname}' has uncommitted changes.")




def check_all_scripts(instruments):
    print('Starting instrument hotfix checker')

    for instrument in instruments:
        check_instrument(instrument)

# Manual running (for the time being)
check_all_scripts(instruments)

print("INFO: NO HOTFIXES detected on: " + str(instrument_no_hotfix))
print("INFO: 1+ HOTFIXES detected on: " + str(instrument_hotfix_detected))

# check if any instrument in hotfix_status_each_instrument has uncommitted changes or is unreachable
if len(instrument_uncommitted_changes) > 0 or len(unreachable_instruments) > 0: 
    print("ERROR: Uncommitted changes detected on: " + str(instrument_uncommitted_changes))
    print("ERROR: Unreachable instruments: " + str(unreachable_instruments))
    sys.exit(1)
else:
    sys.exit(0)