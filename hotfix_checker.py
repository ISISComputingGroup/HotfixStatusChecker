from enum import Enum
import os
import sys
import git
from util.channel_access import ChannelAccessUtils
import paramiko

EPICS_DIR = os.environ['EPICS_DIR']
REMOTE_URL = 'https://github.com/ISISComputingGroup/EPICS'
SSH_PORT = 22
SSH_USERNAME = os.environ["SSH_CREDENTIALS_USR"]
SSH_PASSWORD = os.environ["SSH_CREDENTIALS_PSW"]
USE_TEST_INSTRUMENT_LIST = os.environ["USE_TEST_INSTRUMENT_LIST"]
TEST_INSTRUMENT_LIST = os.environ["TEST_INSTRUMENT_LIST"]


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
            return CHECK.TRUE
        else:
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
    repo.git.fetch()
    repo.git.pull()
    try:
        repo.git.checkout(hostname)
    except git.GitCommandError:
        print(f"Could not checkout branch '{hostname}'")
        return CHECK.UNDETERMINABLE

    repo.git.pull()

    commits = repo.git.rev_list('--count', hostname)
    if int(commits) > 1:
        return CHECK.TRUE
    else:
        return CHECK.FALSE


def check_for_upstream_commits_pending(hostname):
    """ Check if there are any upstream commits waiting to be pulled into the local NDXMOTION branch.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        CHECK: The result of the check.
    """
    # Run the command to check for upstream commits
    fetch_command = "cd C:\\Instrument\\Apps\\EPICS\\ && git fetch origin"
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git log {hostname}..origin/{hostname}"

    ssh_process_fetch = runSSHCommand(
        hostname, SSH_USERNAME, SSH_PASSWORD, fetch_command)
    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        output = ssh_process['output']
        # Check if there are any differences in commit history
        if "commit" in output:
            print(f"Upstream commits pending for {hostname}")
            return CHECK.TRUE
        else:
            print(f"No upstream commits pending for {hostname}")
            return CHECK.FALSE
    else:
        return CHECK.UNDETERMINABLE


def check_for_commits_not_pushed_upstream(hostname):
    """ Check if there are any commits in NDXMOTION branch missing upstream hotfixes.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        CHECK: The result of the check.
    """
    # if git log has galil-old in it then compare with origin/galil-old else compare with origin/main
    # Run the command to check if galil-old is in the commit history
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git log --grep='galil-old' --oneline | wc -l"
    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)
    host_branch = ""
    if ssh_process['success']:
        commit_count = int(ssh_process['output'].strip())
        if commit_count > 0:
            host_branch = "origin/galil-old"
        else:
            host_branch = "origin/main"

    # Run the command to compare with origin/galil-old and origin/main
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git log {host_branch}..{hostname}"

    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        output = ssh_process['output']
        # Check if there are any differences in commit history
        if "commit" in output:
            print(
                f"Commits not pushed upstream on {hostname} (to {host_branch})")
            return CHECK.TRUE
        else:
            print(
                f"No commits not pushed upstream on {hostname} (to {host_branch})")
            return CHECK.FALSE
    else:
        return CHECK.UNDETERMINABLE


def check_for_commits_with_prefix(hostname, commit_prefix):
    """ Check if there are any commits with a specific prefix on the instrument via SSH.

    Args:
        hostname (str): The hostname to connect to.
        commit_prefix (str): The prefix to check for in commit messages.

    Returns:
        CHECK: The result of the check.
    """
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git log"
    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        output = ssh_process['output']
        # check for any commit messages with the prefix
        commit_count = output.count(commit_prefix)
        if commit_count > 0:
            print(f"Hotfix/es detected on {hostname}")
            return CHECK.TRUE
        else:
            print(f"No hotfix/es detected on {hostname}")
            return CHECK.FALSE
    else:
        return CHECK.UNDETERMINABLE


def check_instrument(hostname):
    """ Check if there are any hotfixes or uncomitted changes on AN instrument.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        dict: A dictionary with the result of the checks.
    """
    # Check if any hotfixes run on each instrument
    pushed_changes_enum = check_for_commits_with_prefix(hostname, "Hotfix:")

    # Check if any commits are not pushed upstream on each instrument
    upstream_commits_enum = check_for_commits_not_pushed_upstream(hostname)

    # Check if any upstream commits arnet on each instrument
    upstream_commits_enum = check_for_upstream_commits_pending(hostname)

    # Check if any uncommitted changes run on each instrument
    uncommitted_changes_enum = check_for_uncommitted_changes(hostname)

    # return the result of the checks
    instrument_status = {"hotfix_detected": pushed_changes_enum, "upstream_commits_pending_pulling": upstream_commits_enum, "upstream_commits_not_pushed": upstream_commits_enum,
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

    return instrument_list


def check_instruments():
    """ Run checks on all instruments to find hotfix/changes and log the results.

    Returns:
        None
        """
    print('INFO: Starting instrument hotfix checker')
    print(f"INFO: Using test instrument list: {USE_TEST_INSTRUMENT_LIST}")
    print(f"INFO: Test instrument list: {TEST_INSTRUMENT_LIST}")
    if USE_TEST_INSTRUMENT_LIST == "true":
        instrument_list = TEST_INSTRUMENT_LIST.split(",")
        instrument_list = [instrument.strip()
                           for instrument in instrument_list]
        if "" in instrument_list:
            instrument_list.remove("")
    else:
        instrument_list = get_instrument_list()

    instrument_status_lists = {"instrument_hotfix_detected": [], "instrument_upstream_commits_pending_pulling": [], "instrument_upstream_commits_not_pushed": [],
                               "instrument_uncommitted_changes": [], "unreachable_instruments": []}

    for instrument in instrument_list:
        try:
            instrument_status = check_instrument(instrument)
            print(f"INFO: {instrument} status: {instrument_status}")
            if instrument_status["hotfix_detected"] == CHECK.TRUE:
                instrument_status_lists["instrument_hotfix_detected"].append(
                    instrument)
            # elif instrument_status["hotfix_detected"] == CHECK.FALSE:
            #     instrument_status_lists["instrument_no_hotfix"].append(
            #         instrument)
            elif instrument_status["hotfix_detected"] == CHECK.UNDETERMINABLE:
                instrument_status_lists["unreachable_instruments"].append(
                    instrument)

            if instrument_status["upstream_commits_pending_pulling"] == CHECK.TRUE:
                instrument_status_lists["instrument_upstream_commits_pending_pulling"].append(
                    instrument)
            if instrument_status["upstream_commits_not_pushed"] == CHECK.TRUE:
                instrument_status_lists["instrument_upstream_commits_not_pushed"].append(
                    instrument)
            if instrument_status["uncommitted_changes"] == CHECK.TRUE:
                instrument_status_lists["instrument_uncommitted_changes"].append(
                    instrument)
        except Exception as e:
            print(f"ERROR: Could not connect to {instrument} ({str(e)})")
            instrument_status_lists["unreachable_instruments"].append(
                instrument)

    print("INFO: Instrument hotfix checker finished")

    print("INFO: Instruments with hotfixes:")
    print(instrument_status_lists["instrument_hotfix_detected"])
    print("INFO: Instruments with no hotfixes:")
    print(instrument_status_lists["instrument_no_hotfix"])
    print("INFO: Instruments with upstream commits pending pulling:")
    print(
        instrument_status_lists["instrument_upstream_commits_pending_pulling"])
    print("INFO: Instruments with upstream commits not pushed:")
    print(instrument_status_lists["instrument_upstream_commits_not_pushed"])
    print("INFO: Instruments with uncommitted changes:")
    print(instrument_status_lists["instrument_uncommitted_changes"])
    print("INFO: Unreachable instruments:")
    print(instrument_status_lists["unreachable_instruments"])

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
