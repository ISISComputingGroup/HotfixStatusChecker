"""Module contains the constants used in the application."""

import os

import dotenv

dotenv.load_dotenv()

REPO_DIR = os.environ["REPO_DIR"]
UPSTREAM_BRANCH = os.environ["UPSTREAM_BRANCH"]
SSH_USERNAME = os.environ["SSH_CREDENTIALS_USR"]
SSH_PASSWORD = os.environ["SSH_CREDENTIALS_PSW"]
ARTEFACT_DIR = os.environ["WORKSPACE"]

USE_TEST_INSTRUMENT_LIST = os.environ["USE_TEST_INSTRUMENT_LIST"] == "true"
TEST_INSTRUMENT_LIST = os.environ["TEST_INSTRUMENT_LIST"]
INST_CONFIG_VERSION_TXT_RAW_DATA_URL = "https://control-svcs.isis.cclrc.ac.uk/git/?p=instconfigs/inst.git;a=blob_plain;f=configurations/config_version.txt;hb=refs/heads/"

DEBUG_MODE = os.environ["DEBUG_MODE"] == "true"
