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
                sh "docker build -t test-son-emu-img ."
            }
        }
        stage('Test') {
            steps {
                echo 'Testing...'
                sh "docker run --name son-emu --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock test-son-emu-img 'py.test -v src/emuvim/test/unittests'"
            }
        }
        stage('Package') {
            steps {
                echo 'Packaging (Docker-image)...'
                sh "docker tag test-son-emu-img:latest registry.sonata-nfv.eu:5000/son-emu:latest"
                sh "docker push registry.sonata-nfv.eu:5000/son-emu"        
            }
        }
    }
    post {
         success {
                 mail(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "SUCCESS: son-emu-pipeline",
                 body: "Job ${env.BUILD_ID} on ${env.JENKINS_URL}")
         }
         failure {
                  mail(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "FAILURE: son-emu-pipeline",
                 body: "Job ${env.BUILD_ID} on ${env.JENKINS_URL}")
         }
    }
}
