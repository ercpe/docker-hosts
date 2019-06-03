node('docker') {

    stage('Checkout') {
        git 'https://git.ercpe.de/ercpe/docker-hosts.git'
    }

    stage('CI') {
        docker.withRegistry('https://r.ercpe.de', 'docker-registry') {
            docker.image('r.ercpe.de/ercpe/ubuntu-build:latest').inside {
                sh "make clean jenkins"
            }
        }
    }

    stage('Package') {
        docker.withRegistry('https://r.ercpe.de', 'docker-registry') {
            docker.image('r.ercpe.de/ercpe/ubuntu-build:latest').inside {
                sh "make clean deb"
            }
        }
    }
}
