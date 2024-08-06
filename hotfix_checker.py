"""Creates a RepoChecker object and calls the check_instruments method to check for changes in the instruments repository."""

import os

from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# importing here so it doesn't set variables that are populated from env vars before actually having the env vars loaded
# needed for when running locally to get the contents of a .env fil
# Jenkins will have the env vars set in the pipeline
from utils.hotfix_utils.RepoChecker import RepoChecker

if __name__ == "__main__":
    if os.environ["DEBUG_MODE"] == "true":
        print("INFO: Running in debug mode")
        print(f"INFO: REPO_DIR: {os.environ['REPO_DIR']}")
        print(f"INFO: UPSTREAM_BRANCH: {os.environ['UPSTREAM_BRANCH_CONFIG']}")
        print(f"INFO: ARTEFACT_DIR: {os.environ['WORKSPACE']}")
        print(
            f"INFO: USE_TEST_INSTRUMENT_LIST: {os.environ['USE_TEST_INSTRUMENT_LIST']}"
        )
        print(f"INFO: TEST_INSTRUMENT_LIST: {os.environ['TEST_INSTRUMENT_LIST']}")
        print(f"INFO: DEBUG_MODE: {os.environ['DEBUG_MODE']}")

    repo_checker = RepoChecker()
    repo_checker.check_instruments()
