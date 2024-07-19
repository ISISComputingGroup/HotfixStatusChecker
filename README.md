# HotfixStatusChecker Jenkins Pipeline
This is a Jenkins pipeline to check the status of the EPICS repositories on instrument machines.
It fails when there are uncommitted changes or an instrument is unreachable either via branch or hotfix.
Example usage is either setting up the repo as a pipleine on Jenkins or running with a .env.local file for env var re,eber to do a pip install -r requirments.txt if running locally ansd ont he machien that is running the jebnkisn check.
tempoary workspace is for the git files when running locallt however this should be an argument passed in