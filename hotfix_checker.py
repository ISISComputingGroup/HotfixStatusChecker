from enum import Enum
import os
import sys
import git
from util.channel_access import ChannelAccessUtils
import paramiko
import requests

EPICS_DIR = "C:\\Instrument\\Apps\\EPICS\\"
SSH_PORT = 22
SSH_USERNAME = os.environ["SSH_CREDENTIALS_USR"]
SSH_PASSWORD = os.environ["SSH_CREDENTIALS_PSW"]

USE_TEST_INSTRUMENT_LIST = os.environ["USE_TEST_INSTRUMENT_LIST"] == "true"
TEST_INSTRUMENT_LIST = os.environ["TEST_INSTRUMENT_LIST"]
INST_CONFIG_VERSION_TXT_RAW_DATA_URL = "https://control-svcs.isis.cclrc.ac.uk/git/?p=instconfigs/inst.git;a=blob_plain;f=configurations/config_version.txt;hb=refs/heads/"

DEBUG_MODE = os.environ["DEBUG_MODE"] == "true"


class CHECK(Enum):
    UNDETERMINABLE = 0
    TRUE = 1
    FALSE = 2


def get_insts_on_latest_ibex_via_inst_congif():
    """ Get a list of instruments that are on the latest version of IBEX via the inst_config file.

    Returns:
        list: A list of instruments that are on the latest version of IBEX.
    """
    instrument_list = ChannelAccessUtils().get_inst_list()
    result_list = []
    for instrument in instrument_list:
        if DEBUG_MODE:
            print(f"DEBUG: Checking instrument {instrument}")
        if not instrument['seci']:
            version = requests.get(
                INST_CONFIG_VERSION_TXT_RAW_DATA_URL + instrument['hostName']).text
            version_first_number = int(version.strip().split(".")[0])
            if DEBUG_MODE:
                print(
                    f"DEBUG: Found instrument {instrument['name']} on IBEX version {version_first_number}")
            if version_first_number is not None and version_first_number != "None" and version_first_number != "":
                result_list.append(
                    {'hostname': instrument['hostName'], 'version': version_first_number})

    # Get the latest version of IBEX
    latest_version = max([inst["version"]
                         for inst in result_list])

    # filter out the instruments that are not on the latest version
    insts_on_latest_ibex = [inst["hostname"] for inst in result_list if
                            inst["version"] == latest_version]

    return insts_on_latest_ibex


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
    command = f"cd {EPICS_DIR} && git status --porcelain"
    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    if ssh_process['success']:
        if ssh_process['output'].strip() != "":
            return CHECK.TRUE
        else:

            return CHECK.FALSE
    else:
        return CHECK.UNDETERMINABLE


def get_parent_branch(hostname):
    """ Get the parent branch of the instrument branch.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        str: The name of the parent branch.
    """
    command = f"cd {EPICS_DIR} && git log"
    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)
    if ssh_process['success']:
        if "galil-old" in ssh_process['output']:
            return "origin/galil-old"
        else:
            return "origin/main"
    else:
        return False


def git_log_analyszer(hostname, changes_on=None, subtracted_against=None, prefix=None):
    """ Get the commit messages between two branches on the instrument.

    Args:
        hostname (str): The hostname to connect to.
        changes_on (str): The branch to start from.
        subtracted_against (str): The branch to end at.
        prefix (str): The prefix to check for in commit messages.

    Returns:
        CHECK: The result of the check.
        dict: A dictionary with the commit messages and their hashes.
    """
    branch_details = None
    if changes_on and subtracted_against:
        branch_details = f"{subtracted_against}..{changes_on}"
    else:
        branch_details = ""

    # fetch latest changes from the remote
    fetch_command = f"cd {EPICS_DIR} && git fetch origin"
    ssh_process_fetch = runSSHCommand(
        hostname, SSH_USERNAME, SSH_PASSWORD, fetch_command)
    if not ssh_process_fetch['success']:
        return CHECK.UNDETERMINABLE, None

    command = f"cd {EPICS_DIR} && git log --format=\"%h %s\" {branch_details}"

    ssh_process = runSSHCommand(hostname, SSH_USERNAME, SSH_PASSWORD, command)

    commit_dict = {}

    if ssh_process['success']:
        output = ssh_process['output']
        commit_lines = output.split("\n")
        commit_lines = [line for line in commit_lines if line.strip() != ""]
        for line in commit_lines:
            split_line = line.split(" ", 1)
            hash = split_line[0]
            message = split_line[1]
            if message.startswith(prefix) or prefix == None:
                commit_dict[hash] = message
    else:
        return CHECK.UNDETERMINABLE, None

    if len(commit_dict) > 0:
        return CHECK.TRUE, commit_dict
    else:
        return CHECK.FALSE, None


def check_instrument(hostname):
    """ Check if there are any hotfixes or uncommitted changes on AN instrument.

    Args:
        hostname (str): The hostname to connect to.

    Returns:
        dict: A dictionary with the result of the checks.
    """
    # Check if any hotfixes run on the instrument with the prefix "Hotfix:"
    # hotfix_commits_enum, hotfix_commits_messages = git_log_analyszer(
    #     hostname, prefix="Hotfix:")

    # Check if any upstream commits are not on the instrument, default to the parent origin branch, either main or galil-old
    # commits_pending_pulling_enum = git_log_analyszer(
    #     hostname, changes_on=get_parent_branch(hostname), subtracted_against=hostname, prefix=None)

    # Check if any unpushed commits run on the instrument
    unpushed_commits_enum, unpushed_commit_messages = git_log_analyszer(
        hostname, changes_on="HEAD", subtracted_against="origin/" + hostname, prefix=None)

    # Check if any uncommitted changes run on the instrument
    uncommitted_changes_enum = check_for_uncommitted_changes(hostname)

    # return the result of the checks
    instrument_status = {"commits_not_pushed_messages": unpushed_commit_messages, "commits_not_pushed": unpushed_commits_enum,
                         "uncommitted_changes": uncommitted_changes_enum}

    return instrument_status


def check_instruments():
    """ Run checks on all instruments to find hotfix/changes and log the results.

    Returns:
        None
        """
    if USE_TEST_INSTRUMENT_LIST:
        instrument_list = TEST_INSTRUMENT_LIST.split(",")
        instrument_list = [instrument.strip()
                           for instrument in instrument_list]
        if "" in instrument_list:
            instrument_list.remove("")
    else:
        instrument_list = get_insts_on_latest_ibex_via_inst_congif()

    instrument_status_lists = {"uncommitted_changes": [], "unreachable_at_some_point": [
    ], "unpushed_commits": [], "commits_pending_pulling": []}

    for instrument in instrument_list:
        try:
            instrument_status = check_instrument(instrument)
            print(f"INFO: Checking {instrument}")

            if DEBUG_MODE:
                print("DEBUG: " + str(instrument_status))

            if instrument_status['commits_not_pushed'] == CHECK.TRUE:
                instrument_status_lists["unpushed_commits"].append(instrument + " " + str(
                    instrument_status['commits_not_pushed_messages']))
            elif instrument_status['commits_not_pushed'] == CHECK.UNDETERMINABLE:
                instrument_status_lists["unreachable_at_some_point"].append(
                    instrument)

            if instrument_status['uncommitted_changes'] == CHECK.TRUE:
                instrument_status_lists["uncommitted_changes"].append(
                    instrument)
            elif instrument_status['uncommitted_changes'] == CHECK.UNDETERMINABLE:
                instrument_status_lists["unreachable_at_some_point"].append(
                    instrument)
        except Exception as e:
            print(f"ERROR: Could not connect to {instrument} ({str(e)})")
            if instrument not in instrument_status_lists["unreachable_at_some_point"]:
                instrument_status_lists["unreachable_at_some_point"].append(
                    instrument)

    print("INFO: Summary of results")
    if len(instrument_status_lists['uncommitted_changes']) > 0:
        print(
            f"ERROR: Uncommitted changes: {instrument_status_lists['uncommitted_changes']}")
    else:
        print(
            f"Uncommitted changes: {instrument_status_lists['uncommitted_changes']}")
    if len(instrument_status_lists['unpushed_commits']) > 0:
        print(
            f"ERROR: Commits not pushed: {instrument_status_lists['unpushed_commits']}")
    else:
        print(
            f"Commits not pushed: {instrument_status_lists['unpushed_commits']}")

    if len(instrument_status_lists['unreachable_at_some_point']) > 0:
        print(
            f"ERROR: Unreachable at some point: {instrument_status_lists['unreachable_at_some_point']}")
    else:
        print(
            f"Unreachable at some point: {instrument_status_lists['unreachable_at_some_point']}")

    # Check if any instrument in hotfix_status_each_instrument has uncommitted changes or is unreachable
    if len(instrument_status_lists["uncommitted_changes"]) > 0:
        sys.exit(1)
    if len(instrument_status_lists["unreachable_at_some_point"]) > 0:
        sys.exit(1)
    if len(instrument_status_lists["unpushed_commits"]) > 0:
        sys.exit(1)

    # If no instruments have uncommitted changes or are unreachable, exit with ok status
    sys.exit(0)


if __name__ == '__main__':
    check_instruments()
