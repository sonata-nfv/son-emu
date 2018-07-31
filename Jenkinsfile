#!groovy

pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                echo 'Checkout...'
                checkout scm
            }
        }
        stage('Build') {
            steps {
                echo 'Building...'
                sh "docker build --no-cache -t sonatanfv/son-emu:v4.0 ."
            }
        }
        stage('Style check') {
            steps {
                echo 'Style check...'
                sh "docker run --name son-emu --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock sonatanfv/son-emu:v4.0 'flake8 --exclude=.eggs,devops --ignore=E501 .'"
                echo "done."
            }
        }
        stage('Test') {
            steps {
                echo 'Testing...'
                sh "docker run --name son-emu --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock sonatanfv/son-emu:v4.0 'pytest -v'"
            }
        }
        stage('Package') {
            steps {
                echo 'Packaging (Docker-image)...'
                // push to public Docker registry
                sh "docker push sonatanfv/son-emu:v4.0"
                // push to internal Docker registry
                sh "docker tag sonatanfv/son-emu:v4.0 registry.sonata-nfv.eu:5000/son-emu:v4.0"
                sh "docker push registry.sonata-nfv.eu:5000/son-emu:v4.0"        
            }
        }
    }
    post {
         success {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "SUCCESS: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
         failure {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "FAILURE: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
    }
}
