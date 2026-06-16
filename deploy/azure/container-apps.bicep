@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short environment name, for example dev, staging, or prod.')
param environmentName string

@description('Container image for the FastAPI backend.')
param backendImage string

@description('Container image for the Celery worker.')
param workerImage string = backendImage

@description('Container image for the Celery beat scheduler.')
param beatImage string = backendImage

@description('Container image for the frontend.')
param frontendImage string

@secure()
@description('FastAPI SECRET_KEY.')
param secretKey string

@secure()
@description('PostgreSQL connection URL used by SQLAlchemy.')
param databaseUrl string

@secure()
@description('Redis URL used by Celery and runtime queues.')
param redisUrl string

@description('Public frontend URL.')
param frontendUrl string

@description('MLflow tracking URI reachable from backend containers.')
param mlflowTrackingUri string

@secure()
@description('Optional Slack client secret.')
param slackClientSecret string = ''

@secure()
@description('Optional Groq API key for report/RCA generation.')
param groqApiKey string = ''

@description('Minimum backend replicas.')
param backendMinReplicas int = 1

@description('Maximum backend replicas.')
param backendMaxReplicas int = 3

var namePrefix = 'opssight-${environmentName}'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-apps'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-api'
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        { name: 'secret-key', value: secretKey }
        { name: 'database-url', value: databaseUrl }
        { name: 'redis-url', value: redisUrl }
        { name: 'slack-client-secret', value: slackClientSecret }
        { name: 'groq-api-key', value: groqApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: backendImage
          command: ['uvicorn']
          args: ['app.main:app', '--host', '0.0.0.0', '--port', '8000', '--proxy-headers']
          env: [
            { name: 'APP_ENV', value: environmentName }
            { name: 'SECRET_KEY', secretRef: 'secret-key' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'REDIS_URL', secretRef: 'redis-url' }
            { name: 'FRONTEND_URL', value: frontendUrl }
            { name: 'MLFLOW_TRACKING_URI', value: mlflowTrackingUri }
            { name: 'SLACK_CLIENT_SECRET', secretRef: 'slack-client-secret' }
            { name: 'GROQ_API_KEY', secretRef: 'groq-api-key' }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: backendMinReplicas
        maxReplicas: backendMaxReplicas
      }
    }
  }
}

resource worker 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-worker'
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: [
        { name: 'secret-key', value: secretKey }
        { name: 'database-url', value: databaseUrl }
        { name: 'redis-url', value: redisUrl }
        { name: 'groq-api-key', value: groqApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: workerImage
          command: ['celery']
          args: ['-A', 'app.core.celery_app.celery_app', 'worker', '--loglevel=info', '--queues=ai,scheduler,emails,remediation', '--concurrency=2']
          env: [
            { name: 'APP_ENV', value: environmentName }
            { name: 'SECRET_KEY', secretRef: 'secret-key' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'REDIS_URL', secretRef: 'redis-url' }
            { name: 'MLFLOW_TRACKING_URI', value: mlflowTrackingUri }
            { name: 'GROQ_API_KEY', secretRef: 'groq-api-key' }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

resource beat 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-beat'
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: [
        { name: 'secret-key', value: secretKey }
        { name: 'database-url', value: databaseUrl }
        { name: 'redis-url', value: redisUrl }
      ]
    }
    template: {
      containers: [
        {
          name: 'beat'
          image: beatImage
          command: ['celery']
          args: ['-A', 'app.core.celery_app.celery_app', 'beat', '--loglevel=info']
          env: [
            { name: 'APP_ENV', value: environmentName }
            { name: 'SECRET_KEY', secretRef: 'secret-key' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'REDIS_URL', secretRef: 'redis-url' }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

resource frontend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-frontend'
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output apiUrl string = 'https://${api.properties.configuration.ingress.fqdn}'
output frontendAppUrl string = 'https://${frontend.properties.configuration.ingress.fqdn}'
