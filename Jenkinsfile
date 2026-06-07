pipeline {

```
agent { label 'k3s' }

stages {

    stage('Checkout') {
        steps {
            checkout scm
        }
    }

    stage('Build API Image') {
        steps {
            sh '''
            docker build \
            -t devops-assignment/api:latest \
            ./app/api
            '''
        }
    }

    stage('Build Web Image') {
        steps {
            sh '''
            docker build \
            -t devops-assignment/web:latest \
            ./app/web
            '''
        }
    }

    stage('Import Images Into K3s') {
        steps {
            sh '''
            docker save devops-assignment/api:latest -o api.tar
            docker save devops-assignment/web:latest -o web.tar

            sudo k3s ctr images import api.tar
            sudo k3s ctr images import web.tar
            '''
        }
    }

    stage('Deploy DEV') {
        steps {
            sh '''
            kubectl apply -k k8s/overlays/dev
            '''
        }
    }

    stage('Validate DEV') {
        steps {
            sh '''
            kubectl rollout status deployment/api -n dev --timeout=120s
            kubectl rollout status deployment/web -n dev --timeout=120s
            '''
        }
    }

    stage('Deploy QAT') {
        steps {
            sh '''
            kubectl apply -k k8s/overlays/qat
            '''
        }
    }

    stage('Validate QAT') {
        steps {
            sh '''
            kubectl rollout status deployment/api -n qat --timeout=120s
            kubectl rollout status deployment/web -n qat --timeout=120s
            '''
        }
    }

    stage('Cluster Status') {
        steps {
            sh '''
            kubectl get pods -n dev
            kubectl get pods -n qat
            '''
        }
    }
}

post {
    success {
        echo 'Deployment successful'
    }

    failure {
        echo 'Deployment failed'
    }

    always {
        cleanWs()
    }
}
```

}
