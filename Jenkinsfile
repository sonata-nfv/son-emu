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
                sh "docker build --no-cache -t test-son-emu-img ."
            }
        }
        stage('Test') {
            steps {
                echo 'Testing...'
                sh "docker run --name son-emu --rm --privileged --pid='host' -w '/son-emu' -v /var/run/docker.sock:/var/run/docker.sock test-son-emu-img 'py.test -v src/emuvim/test/unittests'"
            }
        }
        stage('Package') {
            steps {
                echo 'Packaging (Docker-image)...'
            }
        }
    }
}
