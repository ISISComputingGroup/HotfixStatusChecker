# HotfixStatusChecker Jenkins Pipeline
This program is designed to check the status of repositories on instrument machines, controlled by environment variables. It identifies issues such as uncommitted changes, local commits not present on the upstream branch, and vice versa, as well as instrument inaccessibility.

## Usage
To use this program, you can create a Jenkinsfile for the repository you want to check, set the appropriate environment variables, and create a pipeline for this on the Jenkins dashboard. Additionally, the program can be run locally using a local .env file. If running locally or on the machine executing the Jenkins check, remember to run pip install -r requirements.txt. Include this installation in the Jenkinsfile or any .bat files as necessary.

## Important Notes
- Temporary Workspace: This is used for the Git files when running locally; however, this should be passed as an argument.
- Environment Variables: Ensure all required environment variables are correctly set.
- Install Dependencies: Run pip install -r requirements.txt on both the local machine and the Jenkins machine.
- 
## Example Usage
1. Jenkins Integration:
- Create a Jenkinsfile for the repository you want to check.
- Set the appropriate environment variables.
- Create a pipeline on the Jenkins dashboard using the Jenkinsfile.
2. Local Execution:
- Use a local .env file to set environment variables.
- Run pip install -r requirements.txt to install dependencies.
 
## Purpose
1. Check EPICS Directory:
Focuses on detecting commits and/or uncommitted changes that could indicate a HOTFIX.
2. Check Config Common Directory:
Focuses on identifying commits and/or uncommitted changes in the repository that may have been made by scientists or others without prior knowledge.