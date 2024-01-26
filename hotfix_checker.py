from enum import Enum
import os
import sys
import git
from util.channel_access import ChannelAccessUtils
import paramiko

EPICS_DIR = os.environ['EPICS_DIR']
REMOTE_URL = 'https://github.com/ISISComputingGroup/EPICS'
SSH_PORT = 22
SSH_USERNAME = os.environ("SSH_CREDENTIALS_USR")
SSH_PASSWORD = os.environ("SSH_CREDENTIALS_PSW")


class CHECK(Enum):
    UNDETERMINABLE = 0
    TRUE = 1
    FALSE = 2


def runSSHCommand(host, username, password, command):
    """ Run a command on a remote host using SSH.

    Args:
        host (str): The hostname to connect to.
        username (str): The username to use to connect.
        password (str): The password to use to connect.
        command (str): The command to run on the remote host.

    Returns:
        dict: A dictionary with the success status and the output of the command.
    """
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
    """ Check if there are any uncommitted changes on the instrument via SSH.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        CHECK: The result of the check.
    """
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git status --porcelain"
    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        if ssh_process['output'].strip() != "":
            print(f"Uncommitted changes detected on {hostname}")
            return CHECK.TRUE
        else:
            print(f"No uncommitted changes detected on {hostname}")
            return CHECK.FALSE
    else:
        return CHECK.UNDETERMINABLE


def check_for_pushed_changes(hostname):
    """ Check if there are any hotfixes on the instrument via SSH.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        CHECK: The result of the check.
    """
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
    """ Check if there are any hotfixes or uncomitted changes on AN instrument.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        dict: A dictionary with the result of the checks.
    """
    print(f'Checking {hostname}')

    # Check if any hotfixes run on each instrument
    pushed_changes_enum = check_for_pushed_changes(hostname)

    # Check if any uncommitted changes run on each instrument
    uncommitted_changes_enum = check_for_uncommitted_changes(hostname)

    # return the result of the checks
    instrument_status = {"hotfix_detected": pushed_changes_enum,
                         "uncommitted_changes": uncommitted_changes_enum}

    return instrument_status


def get_instrument_list():
    """ Get a list of instruments from the instrument list PV.

    Returns:
        list: A list of instruments.
    """
    instrument_list = ChannelAccessUtils().get_inst_list()
    if len(instrument_list) == 0:
        raise IOError(
            "No instruments found. This is probably because the instrument list PV is unavailable.")
    else:
        # Make list just the ['name'] part with 'NDX' in-front of it
        instrument_list = ["NDX" + instrument['name']
                           for instrument in instrument_list]

    instrument_list = ['NDXSCIDEMO']
    return instrument_list


def check_instruments():
    """ Run checks on all instruments to find hotfix/changes and log the results.

    Returns:
        None
        """
    print('INFO: Starting instrument hotfix checker')

    instrument_list = get_instrument_list()

    instrument_status_lists = {"instrument_hotfix_detected": [], "instrument_no_hotfix": [],
                               "instrument_uncommitted_changes": [], "unreachable_instruments": []}

    for instrument in instrument_list:
        instrument_result = check_instrument(instrument)
        for key in instrument_result:
            if instrument_result[key] == CHECK.TRUE:
                instrument_status_lists["instrument_" + key].append(instrument)
            elif instrument_result[key] == CHECK.UNDETERMINABLE:
                instrument_status_lists["unreachable_instruments"].append(
                    instrument)

    print("INFO: NO HOTFIXES detected on: " +
          str(instrument_status_lists["instrument_no_hotfix"]))
    print("INFO: 1+ HOTFIXES detected on: " +
          str(instrument_status_lists["instrument_hotfix_detected"]))

    # Check if any instrument in hotfix_status_each_instrument has uncommitted changes or is unreachable
    if len(instrument_status_lists["instrument_uncommitted_changes"]) > 0:
        print("ERROR: Uncommitted changes detected on: " +
              str(instrument_status_lists["instrument_uncommitted_changes"]))
        sys.exit(1)
    elif len(instrument_status_lists["unreachable_instruments"]) > 0:
        print("ERROR: Could not connect to: " +
              str(instrument_status_lists["unreachable_instruments"]))
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    check_instruments()
