pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate Repository') {
            steps {
                sh '''
                pwd
                ls -la
                test -d k8s
                test -d app
                test -f docker-compose.yml
                '''
            }
        }

        stage('Validate Kustomize Files') {
            steps {
                sh '''
                find k8s -name "*.yaml" | head
                '''
            }
        }

        stage('Success') {
            steps {
                echo 'DevOps Assignment Pipeline Successful'
            }
        }
    }
}
