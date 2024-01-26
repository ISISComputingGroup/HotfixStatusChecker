import os
import subprocess
import sys
import git
from util.channel_access import ChannelAccessUtils
# Make sure paramiko is installed on the machine running this script
import paramiko

EPICS_DIR = os.environ['EPICS_DIR']
REMOTE_URL = 'https://github.com/ISISComputingGroup/EPICS'
SSH_PORT = 22


def _get_env_var(var_name):
    """
    Return the value of environment variable with given name, or raise an exception if it doesn't exist.
    """
    var = os.environ.get(var_name)
    if var is None:
        raise MissingEnvironmentVariable(
            f'Tried accessing environment variable "{var_name}" that does not exist')
    return var


# Get the inst username and pw from Jenkins paramters
SSH_USERNAME = _get_env_var("SSH_CREDENTIALS_USR")
SSH_PASSWORD = _get_env_var("SSH_CREDENTIALS_PSW")


def runssh(host, username, password, command):
    """ Run a command on a remote host using SSH."""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=SSH_PORT,
                       username=username, password=password)
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
    """ Check if there are any uncommitted changes on the instrument via SSH."""
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git status --porcelain"
    ssh_process = runssh(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        if ssh_process['output'].strip() != "":
            print(f"Uncommitted changes detected on {hostname}")
            return True
    else:
        print(f"Error: {ssh_process['output']}")
        return ssh_process['output']


def check_instrument(hostname):
    """ Check if there are any hotfixes or uncomitted changes on AN instrument."""
    print(f'Checking {hostname}')
    # Connect to instrument/ get instrument branch details via it auto-pushing to get uncommitted changes
    # Set repo from file path

    instrument_result = {"hotfix_detected": False, "no_hotfix": False,
                         "uncommitted_changes": False, "unreachable": False}

    repo = git.Repo(EPICS_DIR)
    try:
        repo.git.checkout(hostname)
    except git.GitCommandError:
        print(f"Could not checkout branch '{hostname}'")
        instrument_result["unreachable"] = True
        return

    repo.git.pull()

    commits = repo.git.rev_list('--count', hostname)
    # print(commits)
    # Initial creation fo branch seems to count as a commit when using git rev-list --count branch-name
    if int(commits) > 1:
        print(f"The branch '{hostname}' has hotfix commits.")
        instrument_result["hotfix_detected"] = True
    else:
        print(f"The branch '{hostname}' has no hotfix commits.")
        instrument_result["no_hotfix"] = True

    # Check if any uncommitted changes run on each instrument
    uncommitted_changes = check_for_uncommitted_changes(hostname)
    if uncommitted_changes == True:
        instrument_result["uncommitted_changes"] = True
    elif uncommitted_changes == False:
        instrument_result["uncommitted_changes"] = False
    else:
        instrument_result["unreachable"] = True

    return instrument_result


def check_instruments():
    """ Run checks on all instruments to find hotfix/changes and log the results."""
    instruments = ChannelAccessUtils().get_inst_list()
    if len(instruments) == 0:
        raise IOError(
            "No instruments found. This is probably because the instrument list PV is unavailable.")
    else:
        # Make list just the ['name'] part with 'NDX' in-front of it
        instruments = ["NDX" + instrument['name']
                       for instrument in instruments]

    instruments = ['NDXSCIDEMO']

    result = {"instrument_hotfix_detected": [], "instrument_no_hotfix": [],
              "instrument_uncommitted_changes": [], "unreachable_instruments": []}

    print('Starting instrument hotfix checker')

    for instrument in instruments:
        instrument_result = check_instrument(instrument)
        if instrument_result["unreachable"] == True:
            result["unreachable_instruments"].append(instrument)

        if instrument_result["uncommitted_changes"] == True:
            result["instrument_uncommitted_changes"].append(instrument)

        if instrument_result["hotfix_detected"] == True:
            result["instrument_hotfix_detected"].append(instrument)

        if instrument_result["no_hotfix"] == True:
            result["instrument_no_hotfix"].append(instrument)

    print("INFO: NO HOTFIXES detected on: " +
          str(result["instrument_no_hotfix"]))
    print("INFO: 1+ HOTFIXES detected on: " +
          str(result["instrument_hotfix_detected"]))

    # Check if any instrument in hotfix_status_each_instrument has uncommitted changes or is unreachable
    if len(result["instrument_uncommitted_changes"]) > 0:
        print("ERROR: Uncommitted changes detected on: " +
              str(result["instrument_uncommitted_changes"]))
        sys.exit(1)
    elif len(result["unreachable_instruments"]) > 0:
        print("ERROR: Could not connect to: " +
              str(result["unreachable_instruments"]))
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    check_instruments()
