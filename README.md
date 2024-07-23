# HotfixStatusChecker Jenkins Pipeline
This program is designed to check the status of repositories on instrument machines, controlled by environment variables. It identifies issues such as uncommitted changes, local commits not present on the upstream branch, and vice versa, as well as instrument inaccessibility.

## Usage
To use this program, you can create a Jenkinsfile for the repository you want to check, set the appropriate environment variables, and create a pipeline for this on the Jenkins dashboard. Additionally, the program can be run locally using a local .env file. If running locally or on the machine executing the Jenkins check, remember to run pip install -r requirements.txt. Include this installation in the Jenkinsfile or any .bat files as necessary.

## Important Notes
- Set workspace to temporary dir when running locally.
- Environment Variables: Ensure all required environment variables are correctly set.
- Install Dependencies: Run pip install -r requirements.txt on both the local machine and the Jenkins machine.
- You can run just on a set few inst machines using test env vars.

## Example Usage
1. Jenkins Integration:
- Create a Jenkinsfile for the repository you want to check.
- Set the appropriate environment variables.
- Create a pipeline on the Jenkins dashboard using the Jenkinsfile.
2. Local Execution:
- Use a local .env file to set environment variables.
- In an EPICS terminal run %PYTHON3% pip install -r requirements.txt to install dependencies.
- Run %PYTHON3% hotfix_checker.py.
 
## Purpose
1. Check EPICS Directory:
Focuses on detecting commits and/or uncommitted changes that could indicate a HOTFIX.
2. Check Config Common Directory:
Focuses on detecting commits and/or uncommitted changes that may have been made by scientists or others.