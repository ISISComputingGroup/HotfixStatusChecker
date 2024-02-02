#!groovy

pipeline {
    // using same agnert as ConfigCheck job
    agent {
        label {
            label 'ConfigCheck'
        }
    }

    triggers {
        cron('0 8 * * *')
    }

    environment {
        EPICS_DIR = 'C:/HotfixStatusChecker/EPICS'
        SSH_CREDENTIALS = credentials('SSH')
        TEST_INSTRUMENT_LIST = $(TEST_INSTRUMENT_LIST)
        USE_TEST_INSTRUMENT_LIST = $(USE_TEST_INSTRUMENT_LIST)
    }

    stages {
        stage('Checkout') {
            steps {
                timeout(time: 2, unit: 'HOURS') {
                    retry(5) {
                        checkout scm
                    }
                }
            }
        }

        stage('Check Instrument has any Hotfixes and then any uncommitteed changes') {
            steps {
                echo 'Check Instrument has any Hotfixes and then any uncommitteed changes'
                timeout(time: 1, unit: 'HOURS') {
                    bat '''
                        call hotfix_checker.bat
                    '''
                }
            }
        }
    }

    post {
        always {
            logParser([
                projectRulePath: 'parse_rules',
                parsingRulesPath: '',
                showGraphs: true,
                unstableOnWarning: true,
                useProjectRule: true,
            ])
        }
    }
}
