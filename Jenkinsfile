pipeline {
    agent any

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
        COMPOSE_PROJECT = 'futurekawa-ci'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                echo "Code récupéré — branche : ${env.GIT_BRANCH}"
            }
        }

        stage('Build images Docker') {
            steps {
                sh '''
                    docker compose -p ${COMPOSE_PROJECT} build \
                        --no-cache \
                        backend-pays \
                        backend-central \
                        subscriber \
                        simulator \
                        frontend
                '''
            }
        }

        stage('Tests unitaires + app (isolés)') {
            steps {
                sh '''
                    docker run --rm \
                        -v $(pwd)/tests:/tests \
                        -v $(pwd)/backend-pays:/backend-pays \
                        -v $(pwd)/subscriber:/subscriber \
                        python:3.12-slim \
                        bash -c "
                            pip install -q pytest pytest-asyncio httpx fastapi 'sqlalchemy[asyncio]' \
                                aiosqlite pydantic-settings aiosmtplib apscheduler aiomqtt &&
                            cd /tests &&
                            python -m pytest test_unit_severity.py test_app_backend_pays.py \
                                test_alerting_logic.py test_subscriber_logic.py \
                                -v --tb=short --junit-xml=/tests/results/unit.xml
                        "
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'tests/results/*.xml'
                    echo 'Tests unitaires + app terminés'
                }
            }
        }

        stage('Démarrage stack de test') {
            steps {
                sh '''
                    docker compose -p ${COMPOSE_PROJECT} up -d \
                        postgres-br postgres-ec postgres-co \
                        mosquitto-br mosquitto-ec mosquitto-co \
                        mailhog
                    sleep 10
                    docker compose -p ${COMPOSE_PROJECT} up -d \
                        api-br api-ec api-co
                    echo "Attente démarrage APIs..."
                    sleep 25
                    docker compose -p ${COMPOSE_PROJECT} up -d \
                        subscriber-br subscriber-ec subscriber-co \
                        simulator-br simulator-ec simulator-co \
                        backend-central
                    sleep 10
                '''
            }
        }

        stage('Tests d intégration API') {
            steps {
                sh '''
                    docker run --rm \
                        --network futurekawa-ci_central-net \
                        --network futurekawa-ci_br-net \
                        --network futurekawa-ci_ec-net \
                        --network futurekawa-ci_co-net \
                        -v $(pwd)/tests:/tests \
                        -e BASE_BR=http://api-br:8000 \
                        -e BASE_EC=http://api-ec:8000 \
                        -e BASE_CO=http://api-co:8000 \
                        -e BASE_CENTRAL=http://backend-central:8000 \
                        python:3.12-slim \
                        bash -c "
                            pip install -q pytest httpx &&
                            cd /tests &&
                            python -m pytest test_api_lots.py test_api_central.py \
                                -v --tb=short \
                                --junit-xml=/tests/results/integration.xml
                        "
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'tests/results/*.xml'
                }
            }
        }

        stage('Vérification qualité (linting)') {
            steps {
                sh '''
                    docker run --rm \
                        -v $(pwd):/app \
                        python:3.12-slim \
                        bash -c "
                            pip install -q ruff &&
                            ruff check /app/backend-pays /app/subscriber /app/simulator /app/backend-central \
                                --select E,W,F \
                                --ignore E501 \
                                --output-format=text || true
                        "
                '''
            }
        }

        stage('Build Frontend') {
            steps {
                sh '''
                    docker run --rm \
                        -v $(pwd)/frontend:/app \
                        node:20-alpine \
                        sh -c "cd /app && npm ci && npm run build"
                '''
                echo 'Frontend buildé avec succès'
            }
        }

        stage('Packaging artefacts') {
            steps {
                sh '''
                    docker compose -p ${COMPOSE_PROJECT} images
                    echo "=== Images disponibles pour déploiement ==="
                    docker images | grep futurekawa-ci
                '''
                archiveArtifacts artifacts: 'frontend/dist/**/*', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            sh '''
                docker compose -p ${COMPOSE_PROJECT} down -v --remove-orphans || true
            '''
            echo 'Stack de test nettoyée'
        }
        success {
            echo 'Pipeline réussi — FutureKawa prêt pour déploiement'
        }
        failure {
            echo 'Pipeline échoué — vérifier les logs ci-dessus'
        }
    }
}
