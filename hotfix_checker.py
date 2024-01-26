from enum import Enum
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

# write enum with undeterminable, true, false


class CHECK(Enum):
    UNDETERMINABLE = 0
    TRUE = 1
    FALSE = 2


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
    print(ssh_process)

    if ssh_process['success']:
        if ssh_process['output'].strip() != "":
            print(f"Uncommitted changes detected on {hostname}")
            return CHECK.TRUE
        else:
            print(f"No uncommitted changes detected on {hostname}")
            return CHECK.FALSE
    else:
        print(f"Error: {ssh_process['output']}")
        return CHECK.UNDETERMINABLE


def check_for_pushed_changes(hostname):
    repo = git.Repo(EPICS_DIR)
    try:
        repo.git.checkout(hostname)
    except git.GitCommandError:
        print(f"Could not checkout branch '{hostname}'")
        return CHECK.UNDETERMINABLE

    repo.git.pull()

    commits = repo.git.rev_list('--count', hostname)
    if int(commits) > 1:
        print(f"The branch '{hostname}' has hotfix commits.")
        return CHECK.TRUE
    else:
        print(f"The branch '{hostname}' has no hotfix commits.")
        return CHECK.FALSE


def check_instrument(hostname):
    """ Check if there are any hotfixes or uncomitted changes on AN instrument."""
    print(f'Checking {hostname}')

    # Check if any hotfixes run on each instrument
    pushed_changes_enum = check_for_pushed_changes(hostname)

    # Check if any uncommitted changes run on each instrument
    uncommitted_changes_enum = check_for_uncommitted_changes(hostname)

    # return the result of the checks
    instrument_result = {"hotfix_detected": pushed_changes_enum,
                         "uncommitted_changes": uncommitted_changes_enum}

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
        for key in instrument_result:
            if instrument_result[key] == CHECK.TRUE:
                result["instrument_" + key].append(instrument)
            elif instrument_result[key] == CHECK.UNDETERMINABLE:
                result["unreachable_instruments"].append(instrument)

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
