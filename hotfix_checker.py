"""Creates a RepoChecker object and calls the check_instruments method to check for changes in the instruments repository."""
from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# importing here so it doesn't set variables that are populated from env vars before actually having the env vars loaded
# needed for when running locally to get the contents of a .env fil
# Jenkins will have the env vars set in the pipeline
from utils.hotfix_utils.RepoChecker import RepoChecker

if __name__ == "__main__":
    repo_checker = RepoChecker()
    repo_checker.check_instruments()
