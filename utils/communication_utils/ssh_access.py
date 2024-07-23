"""This module provides utilities for SSH access."""
import paramiko

SSH_PORT = 22


class SSHAccessUtils(object):
    """Class containing utility methods for SSH access."""

    @staticmethod
    def run_ssh_commandd(
        host : str,
        username : str,
        password : str,
        command : str,
    ):
        """Run a command on a remote host using SSH.

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
            client.connect(
                host,
                port=SSH_PORT,
                username=username,
                password=password,
            )
            (
                stdin,
                stdout,
                stderr,
            ) = client.exec_command(command)
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
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
        except Exception as e:
            print(str(e))
            return {
                "success": False,
                "output": str(e),
            }
