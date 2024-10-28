#!/usr/bin/env groovy
pipeline {
  agent {
      label 'commonagent'
  }
  stages {
    stage('Build docker container') {
      steps {
        sh('make ci/build')
      }
    }
    stage('Publish and tag docker container') {
      steps {
        sh('make ci/release')
        script {
            build_version = readFile ".version"
            currentBuild.description = "Release: v" + build_version
        }
      }
    }
  }
}