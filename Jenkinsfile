node('docker') {

    stage('Checkout') {
        git 'https://git.ercpe.de/ercpe/docker-hosts.git'
    }

    stage('CI') {
        docker.withRegistry('https://r.ercpe.de', 'docker-registry') {
            docker.image('r.ercpe.de/ercpe/python-build:latest').inside {
                sh "make jenkins"
            }
        }
    }

}
