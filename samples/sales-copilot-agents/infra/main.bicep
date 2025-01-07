targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param aiProjectName string = ''
param aiHubName string = ''
param searchServiceName string = ''
param containerAppsEnvironmentName string = ''
param containerRegistryName string = ''
param staticWebAppName string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Resource names
var aiProjectNameFinal = !empty(aiProjectName) ? aiProjectName : '${abbrs.aiProject}${resourceToken}'
var aiHubNameFinal = !empty(aiHubName) ? aiHubName : '${abbrs.aiHub}${resourceToken}'
var searchServiceNameFinal = !empty(searchServiceName) ? searchServiceName : '${abbrs.searchServices}${resourceToken}'
var containerAppsEnvironmentNameFinal = !empty(containerAppsEnvironmentName) ? containerAppsEnvironmentName : '${abbrs.appContainerAppsEnvironments}${resourceToken}'
var containerRegistryNameFinal = !empty(containerRegistryName) ? containerRegistryName : '${abbrs.containerRegistryRegistries}${resourceToken}'
var staticWebAppNameFinal = !empty(staticWebAppName) ? staticWebAppName : '${abbrs.webStaticSites}${resourceToken}'

// Create resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// AI Hub and Project
module aiHub './core/ai/hub.bicep' = {
  name: 'ai-hub'
  scope: rg
  params: {
    name: aiHubNameFinal
    location: location
    tags: tags
  }
}

module aiProject './core/ai/project.bicep' = {
  name: 'ai-project'
  scope: rg
  params: {
    name: aiProjectNameFinal
    location: location
    tags: tags
    hubName: aiHub.outputs.name
  }
}

// OpenAI Service
module openai './core/ai/cognitiveservices.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    name: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'S0'
    }
    deployments: [
      {
        name: 'gpt-4o'
        model: {
          format: 'OpenAI'
          name: 'gpt-4'
          version: '0613'
        }
        sku: {
          name: 'Standard'
          capacity: 1
        }
      }
      {
        name: 'text-embedding-ada-002'
        model: {
          format: 'OpenAI'
          name: 'text-embedding-ada-002'
          version: '2'
        }
        sku: {
          name: 'Standard'
          capacity: 1
        }
      }
    ]
  }
}

// Azure AI Search
module search './core/search/search-services.bicep' = {
  name: 'search'
  scope: rg
  params: {
    name: searchServiceNameFinal
    location: location
    tags: tags
    sku: {
      name: 'standard'
    }
  }
}

// Container Apps host (Backend API)
module containerApps './core/host/container-apps.bicep' = {
  name: 'container-apps'
  scope: rg
  params: {
    name: containerAppsEnvironmentNameFinal
    location: location
    tags: tags
    containerRegistryName: containerRegistryNameFinal
    logAnalyticsWorkspaceName: monitoring.outputs.logAnalyticsWorkspaceName
    applicationInsightsName: monitoring.outputs.applicationInsightsName
  }
}

// Monitoring
module monitoring './core/monitor/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
    applicationInsightsDashboardName: '${abbrs.portalDashboards}${resourceToken}'
  }
}

// Static Web App (Frontend)
module staticWebApp './core/host/staticwebapp.bicep' = {
  name: 'static-webapp'
  scope: rg
  params: {
    name: staticWebAppNameFinal
    location: location
    tags: tags
    sku: {
      name: 'Standard'
      tier: 'Standard'
    }
  }
}


// Container registry
module registry './core/host/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: containerRegistryNameFinal
    location: location
    tags: tags
    sku: {
      name: 'Basic'
    }
  }
}

// App outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

// AI Service outputs
output AZURE_AIPROJECT_NAME string = aiProject.outputs.name
output AZURE_AIHUB_NAME string = aiHub.outputs.name
output AZURE_OPENAI_SERVICE_NAME string = openai.outputs.name
output AZURE_SEARCH_SERVICE_NAME string = search.outputs.name

// Container Apps outputs
output AZURE_CONTAINER_REGISTRY_NAME string = registry.outputs.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.loginServer
output AZURE_CONTAINER_APPS_ENVIRONMENT_NAME string = containerApps.outputs.name

// Static Web App outputs
output AZURE_STATIC_WEB_APP_NAME string = staticWebApp.outputs.name
