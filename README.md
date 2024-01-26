# HotfixStatusChecker Jenkins Pipeline
This is a Jenkins pipeline to check the status of a hotfix branch in the EPICS repositories on instrument machines.
It checks their branches for commits and also SSH into the instrument machines to check for uncommitted changes.
It fails when there are uncommitted changes or an instrument is unreachable either via branch or hotfix.

need to make sure git status command is done on the correct branch and throw error if not
need to think about other problems and edge cases
Need to make sure that a class couldn't be used ro easier simple functions and vice versa
Need to make sure of any other jenkins things i could apply and that is all setup correctly