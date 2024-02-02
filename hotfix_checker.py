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


def get_parent_branch(hostname):
    """ Get the parent branch of the instrument branch.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        str: The name of the parent branch.
    """
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git log"
    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)
    if ssh_process['success']:
        if "galil-old" in ssh_process['output']:
            return "origin/galil-old"
        else:
            return "origin/main"
    else:
        return False


def check_for_unpulled_parents_branch_changes(hostname):
    """ Check if there are any upstream commits waiting to be pulled into the local NDXMOTION branch.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        CHECK: The result of the check.
    """
    # Get the parent branch of the instrument branch
    parent_branch = get_parent_branch(hostname)
    if not parent_branch:
        return CHECK.UNDETERMINABLE
    # Run the command to check for upstream commits
    fetch_command = "cd C:\\Instrument\\Apps\\EPICS\\ && git fetch origin"
    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git log {hostname}..{parent_branch}"

    ssh_process_fetch = runSSHCommand(
        hostname, SSH_USERNAME, SSH_PASSWORD, fetch_command)
    if not ssh_process_fetch['success']:
        return CHECK.UNDETERMINABLE

    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        output = ssh_process['output']
        if "commit" in output:
            return CHECK.TRUE
        else:
            return CHECK.FALSE
    else:
        return CHECK.UNDETERMINABLE


def check_for_commits_not_pushed_upstream(hostname, parent_branch=""):
    """ Check if there are any commits in NDXMOTION branch missing upstream hotfixes.

    Args:
        hostname (str): The hostname to connect to.
        parent_branch (str): The parent branch of the instrument branch.

    Returns:
        CHECK: The result of the check.
    """
    if parent_branch == "":
        parent_branch = parent_branch(hostname)
        if not parent_branch:
            return CHECK.UNDETERMINABLE

    command = f"cd C:\\Instrument\\Apps\\EPICS\\ && git log {parent_branch}..{hostname}"

    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        output = ssh_process['output']
        # Check if there are any differences in commit history
        if "commit" in output:
            return CHECK.TRUE
        else:
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
            return CHECK.TRUE
        else:
            return CHECK.FALSE
    else:
        return CHECK.UNDETERMINABLE


def check_instrument(hostname):
    """ Check if there are any hotfixes or uncommitted changes on AN instrument.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        dict: A dictionary with the result of the checks.
    """
    # Check if any hotfixes run on the instrument with the prefix "Hotfix:"
    # pushed_changes_enum = check_for_commits_with_prefix(hostname, "Hotfix:")

    # Check if any unpushed commits run on the instrument
    unpushed_commits_enum = check_for_commits_not_pushed_upstream(
        hostname, "origin/" + hostname)

    # Check if any upstream commits are not on the instrument, default to the parent origin branch, either main or galil-old
    upstream_commits_enum = check_for_unpulled_parents_branch_changes(hostname)

    # Check if any uncommitted changes run on the instrument
    uncommitted_changes_enum = check_for_uncommitted_changes(hostname)

    # return the result of the checks
    instrument_status = {"upstream_commits_pending_pulling": upstream_commits_enum, "commits_not_pushed": unpushed_commits_enum,
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
    if USE_TEST_INSTRUMENT_LIST == "true":
        instrument_list = TEST_INSTRUMENT_LIST.split(",")
        instrument_list = [instrument.strip()
                           for instrument in instrument_list]
        if "" in instrument_list:
            instrument_list.remove("")
    else:
        instrument_list = get_instrument_list()

    instrument_status_lists = {"uncommitted_changes": [], "unreachable_at_some_point": [
    ], "unpushed_commits": [], "commits_pending_pulling": []}

    for instrument in instrument_list:
        try:
            instrument_status = check_instrument(instrument)
            print(f"INFO: {instrument}")
            if instrument_status['commits_not_pushed'] == CHECK.TRUE:
                print(
                    f"WARNING: Commits not pushed: {instrument_status['commits_not_pushed']}")
            elif instrument_status['commits_not_pushed'] == CHECK.FALSE:
                print(
                    f"Commits not pushed: {instrument_status['commits_not_pushed']}")
            else:
                print(
                    f"ERROR: Commits not pushed: Could not determine commits not pushed status")

            if instrument_status['uncommitted_changes'] == CHECK.TRUE:
                print(
                    f"ERROR: Uncommitted changes: {instrument_status['uncommitted_changes']}")
            elif instrument_status['uncommitted_changes'] == CHECK.FALSE:
                print(
                    f"Uncommitted changes: {instrument_status['uncommitted_changes']}")
            else:
                print(
                    f"ERROR: Uncommitted changes: Could not determine uncommitted changes status")

            if instrument_status['upstream_commits_pending_pulling'] == CHECK.TRUE:
                print(
                    f"ERROR: Upstream commits pending pulling: {instrument_status['upstream_commits_pending_pulling']}")
            elif instrument_status['upstream_commits_pending_pulling'] == CHECK.FALSE:
                print(
                    f"Upstream commits pending pulling: {instrument_status['upstream_commits_pending_pulling']}")
            else:
                print(
                    f"ERROR: Upstream commits pending pulling: Could not determine upstream commits pending pulling status")

            if instrument_status['commits_not_pushed'] == CHECK.TRUE:
                instrument_status_lists["unpushed_commits"].append(instrument)
            if instrument_status['uncommitted_changes'] == CHECK.TRUE:
                instrument_status_lists["uncommitted_changes"].append(
                    instrument)
            if instrument_status['upstream_commits_pending_pulling'] == CHECK.TRUE:
                instrument_status_lists["unpushed_commits"].append(instrument)
            for key, value in instrument_status.items():
                if value == CHECK.UNDETERMINABLE:
                    print(f"ERROR: Could not determine {key} status")
                    instrument_status_lists["unreachable_at_some_point"].append(
                        instrument)

        except Exception as e:
            print(f"ERROR: Could not connect to {instrument} ({str(e)})")
            instrument_status_lists["unreachable_instruments"].append(
                instrument)

    print("INFO: Summary of results")
    print(
        f"Uncommitted changes: {instrument_status_lists['uncommitted_changes']}")
    print(f"Unpushed commits: {instrument_status_lists['unpushed_commits']}")
    print(
        f"Upstream commits pending pulling: {instrument_status_lists['commits_pending_pulling']}")
    print(
        f"Unreachable, at some point, instruments: {instrument_status_lists['unreachable_at_some_point']}")

    # Check if any instrument in hotfix_status_each_instrument has uncommitted changes or is unreachable
    if len(instrument_status_lists["uncommitted_changes"]) > 0:
        sys.exit(1)
    if len(instrument_status_lists["unreachable_at_some_point"]) > 0:
        sys.exit(1)
    if len(instrument_status_lists["unpushed_commits"]) > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    check_instruments()
