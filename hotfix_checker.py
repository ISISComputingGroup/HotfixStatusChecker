# hotfix_checker.py
from dotenv import load_dotenv, find_dotenv
import os

# Load environment variables from .env file
load_dotenv(find_dotenv())

from utils.hotfix_utils.RepoChecker import RepoChecker

if __name__ == "__main__":
    repoChecker = RepoChecker()
    repoChecker.check_instruments()
