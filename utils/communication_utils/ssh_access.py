"""Module provides utilities for SSH access."""

import paramiko

SSH_PORT = 22


class SSHAccessUtils:
    """Class containing utility methods for SSH access."""

    @staticmethod
    def run_ssh_command(
        host: str,
        username: str,
        key_file: str,
        passphrase: str,
        command: str,
    ) -> dict[str, bool | str]:
        """Run a command on a remote host using SSH.

        Args:
            host (str): The hostname to connect to.
            username (str): The username to use to connect.
            key_file (str): The ssh key file to use to connect.
            passphrase (str): The ssh key passphrase to use.
            command (str): The command to run on the remote host.

        Returns:
            dict: A dictionary with the success status and the output of the command.

        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                host,
                port=SSH_PORT,
                username=username,
                key_filename=key_file,
                passphrase=passphrase,
            )
            (
                _stdin,
                stdout,
                stderr,
            ) = client.exec_command(command)
            output = stdout.read().decode("utf-8", errors="backslashreplace")
            error = stderr.read().decode("utf-8", errors="backslashreplace")
            client.close()
            if error:
                return {
                    "success": False,
                    "output": error,
                }
            else:
                return {
                    "success": True,
                    "output": output,
                }
        except Exception as e:  # noqa: BLE001
            print(str(e))
            return {
                "success": False,
                "output": str(e),
            }
