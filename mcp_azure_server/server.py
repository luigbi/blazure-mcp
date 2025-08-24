# server.py
import sys
import os
import json
from typing import Dict, List, Optional, Any, Union
import httpx
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create an MCP server
mcp = FastMCP("Azure Billing MCP")

# Environment variables for Azure Billing configuration
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
AZURE_SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID")

# Check if environment variables are set
if not all([AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID]):
    print("Warning: Azure environment variables not fully configured. Set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_SUBSCRIPTION_ID.", file=sys.stderr)

# Base URLs
AZURE_MANAGEMENT_URL = "https://management.azure.com"
AZURE_LOGIN_URL = "https://login.microsoftonline.com"

# Helper function to get Azure access token
async def get_azure_token() -> str:
    """Get Azure AD access token for API authentication."""
    url = f"{AZURE_LOGIN_URL}/{AZURE_TENANT_ID}/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "resource": "https://management.azure.com/"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        if response.status_code != 200:
            print(f"Error getting Azure token: {response.text}", file=sys.stderr)
            return None
        
        return response.json().get("access_token")

# Helper function for API requests
async def make_azure_request(method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
    """
    Make a request to the Azure API.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (without base URL)
        params: URL parameters
        data: Data to send (for POST/PUT)
    
    Returns:
        Response from Azure API as dictionary
    """
    token = await get_azure_token()
    if not token:
        return {"error": True, "message": "Failed to authenticate with Azure"}
    
    url = f"{AZURE_MANAGEMENT_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code >= 400:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text
                }
            
            return response.json()
        except Exception as e:
            return {
                "error": True,
                "message": f"API request failed: {str(e)}"
            }

# === TOOLS ===

@mcp.tool()
async def get_cost_analysis(timeframe: str = "MonthToDate", granularity: str = "Daily", 
                           group_by: str = None, start_date: str = None, end_date: str = None) -> str:
    """
    Get cost analysis for the subscription.
    
    Args:
        timeframe: The time period for the query (MonthToDate, BillingMonthToDate, TheLastMonth, Custom)
        granularity: The granularity of data (Daily, Monthly, None)
        group_by: Optional property to group the results by (ResourceGroup, ResourceId, etc.)
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.CostManagement/query"
    
    # Prepare the query
    query_data = {
        "type": "ActualCost",
        "timeframe": timeframe,
        "dataSet": {
            "granularity": granularity,
            "aggregation": {
                "totalCost": {
                    "name": "Cost",
                    "function": "Sum"
                }
            }
        }
    }
    
    # Only add timePeriod for Custom timeframe
    if timeframe == "Custom":
        today = datetime.now()
            
        if not start_date:
            start_date = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")

        if not end_date:
            end_date = today.strftime("%Y-%m-%d")

        time_period = {
            "from": start_date,
            "to": end_date
        }
        query_data["timePeriod"] = time_period
    
    # Add grouping if specified
    if group_by:
        query_data["dataSet"]["grouping"] = [
            {
                "type": "Dimension",
                "name": group_by
            }
        ]
    
    result = await make_azure_request("POST", endpoint, 
                                             params={"api-version": "2023-03-01"}, 
                                             data=query_data)
    
    if "error" in result and result["error"]:
        return f"Error retrieving cost analysis: {result.get('message', 'Unknown error')}"
    
    # Format the result in a readable way
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_budgets() -> str:
    """
    Get all budgets for the subscription.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Consumption/budgets"
    
    # Use a supported API version, e.g., 2023-05-01
    result = await make_azure_request("GET", endpoint, 
                                             params={"api-version": "2023-05-01"})
        
    if "error" in result and result["error"]:
        return f"Error retrieving budgets: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_recommendations() -> str:
    """
    Get top 10 recommendations for the subscription.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Advisor/recommendations"
    
    # Use a supported API version, e.g., 2023-05-01
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2025-05-01-preview",
                                                 "$top": "10"
                                                 })
        
    if "error" in result and result["error"]:
        return f"Error retrieving budgets: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_usage_details(start_date: str = None, end_date: str = None) -> str:
    """
    Get usage details for the subscription.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to beginning of current month)
        end_date: End date in YYYY-MM-DD format (defaults to today)
    """
    today = datetime.now()
    
    if not start_date:
        start_date = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
    
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    
    # Filter is required for usage details
    filter_param = f"properties/usageStart ge '{start_date}' and properties/usageEnd le '{end_date}'"
    
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Consumption/usageDetails"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2024-08-01",
                                                 "$filter": filter_param
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving usage details: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_subscription_details() -> str:
    """
    Get details about the current subscription.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={"api-version": "2022-12-01"})
    
    if "error" in result and result["error"]:
        return f"Error retrieving subscription details: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_price_sheet() -> str:
    """
    Get the price sheet for the subscription.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Consumption/pricesheets/default"
    
      # Use a supported API version, e.g., 2023-05-01
    result = await make_azure_request("GET", endpoint, 
                                             params={"api-version": "2023-05-01"})
    
    if "error" in result and result["error"]:
        return f"Error retrieving price sheet: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_all_resources(query: str = None) -> str:
    """
    Get all Azure resources using Resource Graph API.
    
    Args:
        query: Optional KQL query to filter resources (if not provided, gets all resources)
    """
    endpoint = "/providers/Microsoft.ResourceGraph/resources"
    
    # Default query to get all resources with essential info for diagramming
    default_query = """
    Resources
    | project id, name, type, resourceGroup, location, subscriptionId, tags, properties
    | limit 1000
    """
    
    query_data = {
        "subscriptions": [AZURE_SUBSCRIPTION_ID],
        "query": query or default_query
    }
    
    result = await make_azure_request("POST", endpoint, 
                                             params={"api-version": "2021-03-01"}, 
                                             data=query_data)
    
    if "error" in result and result["error"]:
        return f"Error retrieving resources: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_network_topology() -> str:
    """
    Get network topology including VNets, subnets, peerings, and network security groups.
    """
    query = """
    Resources
    | where type in~ (
        'Microsoft.Network/virtualNetworks',
        'Microsoft.Network/virtualNetworkPeerings', 
        'Microsoft.Network/networkSecurityGroups',
        'Microsoft.Network/networkInterfaces',
        'Microsoft.Network/publicIPAddresses',
        'Microsoft.Network/loadBalancers',
        'Microsoft.Network/applicationGateways',
        'Microsoft.Network/virtualNetworkGateways',
        'Microsoft.Network/routeTables'
    )
    | project id, name, type, resourceGroup, location, properties
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_compute_resources() -> str:
    """
    Get all compute resources including VMs, App Services, Functions, etc.
    """
    query = """
    Resources
    | where type in~ (
        'Microsoft.Compute/virtualMachines',
        'Microsoft.Compute/virtualMachineScaleSets',
        'Microsoft.Web/sites',
        'Microsoft.Web/serverFarms',
        'Microsoft.ContainerInstance/containerGroups',
        'Microsoft.ContainerService/managedClusters',
        'Microsoft.Batch/batchAccounts'
    )
    | project id, name, type, resourceGroup, location, properties
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_storage_resources() -> str:
    """
    Get all storage and database resources.
    """
    query = """
    Resources
    | where type in~ (
        'Microsoft.Storage/storageAccounts',
        'Microsoft.Sql/servers',
        'Microsoft.Sql/servers/databases',
        'Microsoft.DocumentDB/databaseAccounts',
        'Microsoft.Cache/Redis',
        'Microsoft.DBforPostgreSQL/servers',
        'Microsoft.DBforMySQL/servers'
    )
    | project id, name, type, resourceGroup, location, properties
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_resource_dependencies() -> str:
    """
    Get resource dependencies and relationships.
    """
    query = """
    Resources
    | extend dependencies = properties.dependencies
    | project id, name, type, resourceGroup, dependencies, properties
    | where isnotempty(dependencies) or isnotempty(properties.networkProfile) or isnotempty(properties.subnets)
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_resource_hierarchy() -> str:
    """
    Get resource hierarchy organized by resource groups and management structure.
    """
    query = """
    Resources
    | summarize Resources = make_list(pack('name', name, 'type', type, 'id', id, 'location', location, 'tags', tags)) by resourceGroup, subscriptionId
    | project subscriptionId, resourceGroup, ResourceCount = array_length(Resources), Resources
    | order by resourceGroup asc
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_network_connections() -> str:
    """
    Get detailed network connections including VM network interfaces, subnet associations, and peerings.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.Network/networkInterfaces'
    | extend vmId = tostring(properties.virtualMachine.id)
    | extend subnetId = tostring(properties.ipConfigurations[0].properties.subnet.id)
    | extend privateIP = tostring(properties.ipConfigurations[0].properties.privateIPAddress)
    | extend publicIPId = tostring(properties.ipConfigurations[0].properties.publicIPAddress.id)
    | project id, name, vmId, subnetId, privateIP, publicIPId, resourceGroup, location
    | union (
        Resources
        | where type =~ 'Microsoft.Network/virtualNetworks'
        | extend subnets = properties.subnets
        | mvexpand subnets
        | extend subnetName = tostring(subnets.name)
        | extend subnetId = tostring(subnets.id)
        | extend addressPrefix = tostring(subnets.properties.addressPrefix)
        | project vnetId = id, vnetName = name, subnetId, subnetName, addressPrefix, resourceGroup, location, type = 'subnet'
    )
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def export_resources_graphml(include_network: bool = True, include_dependencies: bool = True) -> str:
    """
    Export resources in GraphML format for diagram generation.
    
    Args:
        include_network: Include network topology information
        include_dependencies: Include resource dependencies
    """
    try:
        # Get all resources
        all_resources_result = await get_all_resources()
        all_resources_data = json.loads(all_resources_result)
        
        # Get network topology if requested
        network_data = None
        if include_network:
            network_result = await get_network_topology()
            network_data = json.loads(network_result)
        
        # Get dependencies if requested
        dependencies_data = None
        if include_dependencies:
            dependencies_result = await get_resource_dependencies()
            dependencies_data = json.loads(dependencies_result)
        
        # Create GraphML structure
        graphml_structure = {
            "format": "GraphML",
            "nodes": [],
            "edges": [],
            "metadata": {
                "subscription_id": AZURE_SUBSCRIPTION_ID,
                "generated_at": datetime.now().isoformat(),
                "include_network": include_network,
                "include_dependencies": include_dependencies
            }
        }
        
        # Process nodes (resources)
        if "data" in all_resources_data and "rows" in all_resources_data["data"]:
            for resource in all_resources_data["data"]["rows"]:
                node = {
                    "id": resource[0],  # resource id
                    "name": resource[1],  # resource name
                    "type": resource[2],  # resource type
                    "resourceGroup": resource[3],  # resource group
                    "location": resource[4],  # location
                    "subscriptionId": resource[5],  # subscription id
                    "tags": resource[6] if len(resource) > 6 else {},  # tags
                    "properties": resource[7] if len(resource) > 7 else {}  # properties
                }
                graphml_structure["nodes"].append(node)
        
        # Process edges (relationships) from network topology
        if include_network and network_data and "data" in network_data:
            # Add network relationships logic here
            # This would require additional processing of network connections
            pass
        
        # Process edges from dependencies
        if include_dependencies and dependencies_data and "data" in dependencies_data:
            # Add dependency relationships logic here
            # This would require additional processing of dependency information
            pass
        
        return json.dumps(graphml_structure, indent=2)
        
    except Exception as e:
        return f"Error exporting GraphML: {str(e)}"

@mcp.tool()
async def get_resource_detailed_info(resource_id: str = None) -> str:
    """
    Get detailed information about a specific resource or all resources with their detailed configurations.
    
    Args:
        resource_id: Optional specific resource ID to get details for
    """
    if resource_id:
        # Get specific resource details
        endpoint = f"{resource_id}"
        result = await make_azure_request("GET", endpoint, 
                                                 params={"api-version": "2022-09-01"})
    else:
        # Get all resources with detailed information using ARM API
        endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/resources"
        result = await make_azure_request("GET", endpoint, 
                                                 params={
                                                     "api-version": "2022-09-01",
                                                     "$expand": "createdTime,changedTime,provisioningState"
                                                 })
    
    if "error" in result and result["error"]:
        return f"Error retrieving detailed resource info: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_network_security_groups_detailed() -> str:
    """
    Get detailed Network Security Groups with rules and associations.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.Network/networkSecurityGroups'
    | extend securityRules = properties.securityRules
    | extend defaultSecurityRules = properties.defaultSecurityRules
    | extend networkInterfaces = properties.networkInterfaces
    | extend subnets = properties.subnets
    | project id, name, resourceGroup, location, securityRules, defaultSecurityRules, networkInterfaces, subnets
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_load_balancers_detailed() -> str:
    """
    Get detailed Load Balancers with backend pools, probes, and rules.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.Network/loadBalancers'
    | extend frontendIPConfigurations = properties.frontendIPConfigurations
    | extend backendAddressPools = properties.backendAddressPools
    | extend loadBalancingRules = properties.loadBalancingRules
    | extend probes = properties.probes
    | extend inboundNatRules = properties.inboundNatRules
    | project id, name, resourceGroup, location, frontendIPConfigurations, backendAddressPools, loadBalancingRules, probes, inboundNatRules
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_virtual_machines_detailed() -> str:
    """
    Get detailed Virtual Machine information including network interfaces, disks, and extensions.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.Compute/virtualMachines'
    | extend vmSize = properties.hardwareProfile.vmSize
    | extend osType = properties.storageProfile.osDisk.osType
    | extend networkProfile = properties.networkProfile
    | extend availabilitySet = properties.availabilitySet
    | extend diagnosticsProfile = properties.diagnosticsProfile
    | extend powerState = properties.extended.instanceView.powerState.code
    | project id, name, resourceGroup, location, vmSize, osType, networkProfile, availabilitySet, diagnosticsProfile, powerState, tags
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_app_services_detailed() -> str:
    """
    Get detailed App Service information including configuration, slots, and dependencies.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.Web/sites'
    | extend appKind = kind
    | extend serverFarmId = properties.serverFarmId
    | extend defaultHostName = properties.defaultHostName
    | extend enabledHostNames = properties.enabledHostNames
    | extend httpsOnly = properties.httpsOnly
    | extend siteConfig = properties.siteConfig
    | project id, name, resourceGroup, location, appKind, serverFarmId, defaultHostName, enabledHostNames, httpsOnly, siteConfig, tags
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_databases_detailed() -> str:
    """
    Get detailed database information including SQL databases, Cosmos DB, and other data services.
    """
    query = """
    Resources
    | where type in~ (
        'Microsoft.Sql/servers/databases',
        'Microsoft.DocumentDB/databaseAccounts',
        'Microsoft.DBforPostgreSQL/servers',
        'Microsoft.DBforMySQL/servers',
        'Microsoft.Cache/Redis'
    )
    | extend tier = properties.sku.tier
    | extend capacity = properties.sku.capacity
    | extend family = properties.sku.family
    | extend connectionString = properties.connectionString
    | extend firewallRules = properties.firewallRules
    | project id, name, type, resourceGroup, location, tier, capacity, family, connectionString, firewallRules, tags
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_storage_accounts_detailed() -> str:
    """
    Get detailed storage account information including access tiers, replication, and services.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.Storage/storageAccounts'
    | extend sku = properties.sku
    | extend accessTier = properties.accessTier
    | extend supportsHttpsTrafficOnly = properties.supportsHttpsTrafficOnly
    | extend allowBlobPublicAccess = properties.allowBlobPublicAccess
    | extend minimumTlsVersion = properties.minimumTlsVersion
    | extend primaryEndpoints = properties.primaryEndpoints
    | extend networkAcls = properties.networkAcls
    | project id, name, resourceGroup, location, sku, accessTier, supportsHttpsTrafficOnly, allowBlobPublicAccess, minimumTlsVersion, primaryEndpoints, networkAcls, tags
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_key_vaults_detailed() -> str:
    """
    Get detailed Key Vault information including access policies and network access.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.KeyVault/vaults'
    | extend sku = properties.sku
    | extend accessPolicies = properties.accessPolicies
    | extend networkAcls = properties.networkAcls
    | extend enabledForDeployment = properties.enabledForDeployment
    | extend enabledForTemplateDeployment = properties.enabledForTemplateDeployment
    | extend enabledForDiskEncryption = properties.enabledForDiskEncryption
    | project id, name, resourceGroup, location, sku, accessPolicies, networkAcls, enabledForDeployment, enabledForTemplateDeployment, enabledForDiskEncryption, tags
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_resource_group_details() -> str:
    """
    Get detailed information about all resource groups including tags and policies.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/resourcegroups"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2022-09-01",
                                                 "$expand": "tags"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving resource group details: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_network_watchers_topology() -> str:
    """
    Get actual network topology from Network Watcher (if available).
    """
    # First, find Network Watchers in the subscription
    query = """
    Resources
    | where type =~ 'Microsoft.Network/networkWatchers'
    | project id, name, resourceGroup, location
    """
    
    network_watchers_result = await get_all_resources(query)
    
    try:
        import json
        nw_data = json.loads(network_watchers_result)
        
        if "data" in nw_data and "rows" in nw_data["data"] and len(nw_data["data"]["rows"]) > 0:
            # Use the first Network Watcher found
            nw_info = nw_data["data"]["rows"][0]
            nw_name = nw_info[1]  # name
            nw_rg = nw_info[2]    # resource group
            
            # Get topology from Network Watcher
            endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/resourceGroups/{nw_rg}/providers/Microsoft.Network/networkWatchers/{nw_name}/topology"
            
            # Request body for topology query
            topology_request = {
                "targetResourceGroupName": nw_rg
            }
            
            result = await make_azure_request("POST", endpoint, 
                                                     params={"api-version": "2023-02-01"}, 
                                                     data=topology_request)
            
            if "error" in result and result["error"]:
                return f"Error retrieving network topology: {result.get('message', 'Unknown error')}"
            
            return json.dumps(result, indent=2)
        else:
            return "No Network Watchers found in subscription"
            
    except Exception as e:
        return f"Error processing Network Watcher topology: {str(e)}"

@mcp.tool()
async def get_monitoring_and_diagnostics() -> str:
    """
    Get monitoring and diagnostic settings for resources.
    """
    query = """
    Resources
    | where type =~ 'Microsoft.Insights/diagnosticSettings'
    | extend targetResourceId = properties.targetResourceId
    | extend logs = properties.logs
    | extend metrics = properties.metrics
    | extend workspaceId = properties.workspaceId
    | extend storageAccountId = properties.storageAccountId
    | project id, name, targetResourceId, logs, metrics, workspaceId, storageAccountId
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_resource_locks() -> str:
    """
    Get resource locks to understand governance and protection policies.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Authorization/locks"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={"api-version": "2020-05-01"})
    
    if "error" in result and result["error"]:
        return f"Error retrieving resource locks: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_rbac_assignments() -> str:
    """
    Get RBAC role assignments to understand access patterns and security relationships.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Authorization/roleAssignments"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2022-04-01",
                                                 "$filter": "atScope()"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving RBAC assignments: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_resource_dependencies_advanced() -> str:
    """
    Get advanced resource dependencies including cross-resource group relationships.
    """
    query = """
    Resources
    | extend networkProfile = properties.networkProfile
    | extend storageProfile = properties.storageProfile
    | extend dependsOn = properties.dependsOn
    | extend linkedServices = properties.linkedServices
    | extend serverFarmId = properties.serverFarmId
    | extend subnetId = tostring(properties.ipConfigurations[0].properties.subnet.id)
    | extend loadBalancerId = tostring(properties.loadBalancer.id)
    | extend networkSecurityGroupId = tostring(properties.networkSecurityGroup.id)
    | extend routeTableId = tostring(properties.routeTable.id)
    | where isnotempty(networkProfile) or isnotempty(storageProfile) or isnotempty(dependsOn) or isnotempty(linkedServices) or isnotempty(serverFarmId) or isnotempty(subnetId) or isnotempty(loadBalancerId) or isnotempty(networkSecurityGroupId) or isnotempty(routeTableId)
    | project id, name, type, resourceGroup, location, networkProfile, storageProfile, dependsOn, linkedServices, serverFarmId, subnetId, loadBalancerId, networkSecurityGroupId, routeTableId
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_comprehensive_architecture_data() -> str:
    """
    Get comprehensive architecture data combining multiple resource types and their relationships.
    """
    def safe_json_parse(json_string, fallback_name):
        """Safely parse JSON string, return error info if parsing fails."""
        try:
            if json_string.startswith("Error"):
                return {"error": True, "message": json_string, "source": fallback_name}
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            return {"error": True, "message": f"JSON parsing failed: {str(e)}", "source": fallback_name, "raw_data": json_string[:200]}
        except Exception as e:
            return {"error": True, "message": f"Unexpected error: {str(e)}", "source": fallback_name}
    
    try:
        architecture_data = {
            "metadata": {
                "subscription_id": AZURE_SUBSCRIPTION_ID,
                "generated_at": datetime.now().isoformat(),
                "data_scope": "comprehensive_architecture"
            },
            "resource_groups": {},
            "compute": {},
            "networking": {},
            "storage": {},
            "dependencies": {},
            "errors": []
        }
        
        # Get resource groups
        print("Getting resource groups...", file=sys.stderr)
        rg_result = await get_resource_group_details()
        rg_data = safe_json_parse(rg_result, "resource_groups")
        if "error" in rg_data:
            architecture_data["errors"].append(rg_data)
            architecture_data["resource_groups"] = {"error": "Failed to retrieve resource groups"}
        else:
            architecture_data["resource_groups"] = rg_data
        
        # Get compute resources
        print("Getting compute resources...", file=sys.stderr)
        vm_result = await get_virtual_machines_detailed()
        vm_data = safe_json_parse(vm_result, "virtual_machines")
        
        app_result = await get_app_services_detailed()
        app_data = safe_json_parse(app_result, "app_services")
        
        architecture_data["compute"] = {
            "virtual_machines": vm_data if "error" not in vm_data else {"error": "Failed to retrieve VMs"},
            "app_services": app_data if "error" not in app_data else {"error": "Failed to retrieve App Services"}
        }
        
        if "error" in vm_data:
            architecture_data["errors"].append(vm_data)
        if "error" in app_data:
            architecture_data["errors"].append(app_data)
        
        # Get networking
        print("Getting networking data...", file=sys.stderr)
        network_result = await get_network_topology()
        network_data = safe_json_parse(network_result, "network_topology")
        
        nsg_result = await get_network_security_groups_detailed()
        nsg_data = safe_json_parse(nsg_result, "network_security_groups")
        
        architecture_data["networking"] = {
            "topology": network_data if "error" not in network_data else {"error": "Failed to retrieve network topology"},
            "security_groups": nsg_data if "error" not in nsg_data else {"error": "Failed to retrieve NSGs"}
        }
        
        if "error" in network_data:
            architecture_data["errors"].append(network_data)
        if "error" in nsg_data:
            architecture_data["errors"].append(nsg_data)
        
        # Get storage and databases
        print("Getting storage data...", file=sys.stderr)
        storage_result = await get_storage_accounts_detailed()
        storage_data = safe_json_parse(storage_result, "storage_accounts")
        
        db_result = await get_databases_detailed()
        db_data = safe_json_parse(db_result, "databases")
        
        architecture_data["storage"] = {
            "storage_accounts": storage_data if "error" not in storage_data else {"error": "Failed to retrieve storage accounts"},
            "databases": db_data if "error" not in db_data else {"error": "Failed to retrieve databases"}
        }
        
        if "error" in storage_data:
            architecture_data["errors"].append(storage_data)
        if "error" in db_data:
            architecture_data["errors"].append(db_data)
        
        # Get dependencies
        print("Getting dependencies...", file=sys.stderr)
        deps_result = await get_resource_dependencies_advanced()
        deps_data = safe_json_parse(deps_result, "dependencies")
        
        if "error" in deps_data:
            architecture_data["errors"].append(deps_data)
            architecture_data["dependencies"] = {"error": "Failed to retrieve dependencies"}
        else:
            architecture_data["dependencies"] = deps_data
        
        print(f"Architecture data collection completed with {len(architecture_data['errors'])} errors", file=sys.stderr)
        return json.dumps(architecture_data, indent=2)
        
    except Exception as e:
        error_details = {
            "error": True,
            "message": f"Error getting comprehensive architecture data: {str(e)}",
            "type": type(e).__name__,
            "subscription_id": AZURE_SUBSCRIPTION_ID
        }
        return json.dumps(error_details, indent=2)

@mcp.tool()
async def get_azure_advisor_detailed() -> str:
    """
    Get detailed Azure Advisor recommendations including cost, performance, security, and operational excellence.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Advisor/recommendations"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2020-01-01",
                                                 "$filter": "Category eq 'Cost' or Category eq 'Performance' or Category eq 'HighAvailability' or Category eq 'Security' or Category eq 'OperationalExcellence'"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving detailed advisor recommendations: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_unused_resources() -> str:
    """
    Identify potentially unused or under-utilized resources using Resource Graph queries.
    """
    query = """
    Resources
    | where type in~ (
        'Microsoft.Compute/virtualMachines',
        'Microsoft.Network/publicIPAddresses',
        'Microsoft.Compute/disks',
        'Microsoft.Network/networkInterfaces',
        'Microsoft.Storage/storageAccounts'
    )
    | extend resourceDetails = case(
        type =~ 'Microsoft.Compute/virtualMachines', 
            pack('powerState', properties.extended.instanceView.powerState.displayStatus, 'vmSize', properties.hardwareProfile.vmSize),
        type =~ 'Microsoft.Network/publicIPAddresses', 
            pack('ipConfiguration', properties.ipConfiguration, 'associatedResource', properties.ipConfiguration.id),
        type =~ 'Microsoft.Compute/disks', 
            pack('diskState', properties.diskState, 'managedBy', managedBy, 'diskSize', properties.diskSizeGB),
        type =~ 'Microsoft.Network/networkInterfaces', 
            pack('virtualMachine', properties.virtualMachine, 'ipConfigurations', properties.ipConfigurations),
        type =~ 'Microsoft.Storage/storageAccounts',
            pack('accessTier', properties.accessTier, 'lastAccessTime', properties.lastAccessTime),
        pack('status', 'unknown')
    )
    | extend potentiallyUnused = case(
        type =~ 'Microsoft.Compute/virtualMachines' and resourceDetails.powerState contains 'stopped', true,
        type =~ 'Microsoft.Network/publicIPAddresses' and isnull(resourceDetails.ipConfiguration), true,
        type =~ 'Microsoft.Compute/disks' and resourceDetails.diskState =~ 'Unattached', true,
        type =~ 'Microsoft.Network/networkInterfaces' and isnull(resourceDetails.virtualMachine), true,
        false
    )
    | where potentiallyUnused == true
    | project id, name, type, resourceGroup, location, resourceDetails, tags
    """
    
    return await get_all_resources(query)

@mcp.tool()
async def get_vm_performance_metrics(vm_resource_id: str = None, timespan: str = "PT1H") -> str:
    """
    Get performance metrics for Virtual Machines (CPU, Memory, Disk, Network).
    
    Args:
        vm_resource_id: Specific VM resource ID (if not provided, gets metrics for all VMs)
        timespan: Time span for metrics (PT1H=1 hour, PT24H=24 hours, P7D=7 days)
    """
    if vm_resource_id:
        # Get metrics for specific VM
        endpoint = f"{vm_resource_id}/providers/Microsoft.Insights/metrics"
        
        result = await make_azure_request("GET", endpoint, 
                                                 params={
                                                     "api-version": "2018-01-01",
                                                     "metricnames": "Percentage CPU,Available Memory Bytes,Disk Read Bytes/sec,Disk Write Bytes/sec,Network In Total,Network Out Total",
                                                     "timespan": timespan,
                                                     "interval": "PT1M",
                                                     "aggregation": "Average,Maximum"
                                                 })
    else:
        # Get all VMs first, then aggregate their metrics
        vm_query = """
        Resources
        | where type =~ 'Microsoft.Compute/virtualMachines'
        | where properties.extended.instanceView.powerState.code =~ 'PowerState/running'
        | project id, name, resourceGroup, location, vmSize = properties.hardwareProfile.vmSize
        | limit 10
        """
        
        vms_result = await get_all_resources(vm_query)
        
        try:
            vms_data = json.loads(vms_result)
            metrics_summary = {
                "timespan": timespan,
                "vm_metrics": [],
                "summary": {
                    "total_vms": 0,
                    "high_cpu_vms": 0,
                    "low_utilization_vms": 0
                }
            }
            
            if "data" in vms_data and "rows" in vms_data["data"]:
                for vm in vms_data["data"]["rows"]:
                    vm_id = vm[0]
                    vm_name = vm[1]
                    
                    # Get metrics for each VM
                    endpoint = f"{vm_id}/providers/Microsoft.Insights/metrics"
                    
                    vm_metrics = await make_azure_request("GET", endpoint, 
                                                                 params={
                                                                     "api-version": "2018-01-01",
                                                                     "metricnames": "Percentage CPU",
                                                                     "timespan": timespan,
                                                                     "interval": "PT5M",
                                                                     "aggregation": "Average,Maximum"
                                                                 })
                    
                    if "error" not in vm_metrics:
                        metrics_summary["vm_metrics"].append({
                            "vm_id": vm_id,
                            "vm_name": vm_name,
                            "metrics": vm_metrics
                        })
                        metrics_summary["summary"]["total_vms"] += 1
            
            return json.dumps(metrics_summary, indent=2)
            
        except Exception as e:
            return f"Error processing VM metrics: {str(e)}"
    
    if "error" in result and result["error"]:
        return f"Error retrieving VM metrics: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_storage_performance_metrics(storage_account_id: str = None, timespan: str = "PT24H") -> str:
    """
    Get performance metrics for Storage Accounts (transactions, capacity, availability).
    
    Args:
        storage_account_id: Specific storage account resource ID
        timespan: Time span for metrics
    """
    if storage_account_id:
        endpoint = f"{storage_account_id}/providers/Microsoft.Insights/metrics"
    else:
        # Get all storage accounts and their metrics
        storage_query = """
        Resources
        | where type =~ 'Microsoft.Storage/storageAccounts'
        | project id, name, resourceGroup, location, sku = properties.sku.name
        | limit 10
        """
        
        storage_result = await get_all_resources(storage_query)
        
        try:
            storage_data = json.loads(storage_result)
            metrics_summary = {
                "timespan": timespan,
                "storage_metrics": [],
                "summary": {
                    "total_accounts": 0,
                    "low_usage_accounts": 0
                }
            }
            
            if "data" in storage_data and "rows" in storage_data["data"]:
                for storage in storage_data["data"]["rows"]:
                    storage_id = storage[0]
                    storage_name = storage[1]
                    
                    endpoint = f"{storage_id}/providers/Microsoft.Insights/metrics"
                    
                    storage_metrics = await make_azure_request("GET", endpoint, 
                                                                      params={
                                                                          "api-version": "2018-01-01",
                                                                          "metricnames": "Transactions,UsedCapacity,Availability",
                                                                          "timespan": timespan,
                                                                          "interval": "PT1H",
                                                                          "aggregation": "Total,Average"
                                                                      })
                    
                    if "error" not in storage_metrics:
                        metrics_summary["storage_metrics"].append({
                            "storage_id": storage_id,
                            "storage_name": storage_name,
                            "metrics": storage_metrics
                        })
                        metrics_summary["summary"]["total_accounts"] += 1
            
            return json.dumps(metrics_summary, indent=2)
            
        except Exception as e:
            return f"Error processing storage metrics: {str(e)}"
    
    # Single storage account metrics
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2018-01-01",
                                                 "metricnames": "Transactions,UsedCapacity,Availability,SuccessServerLatency,SuccessE2ELatency",
                                                 "timespan": timespan,
                                                 "interval": "PT1H",
                                                 "aggregation": "Total,Average,Maximum"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving storage metrics: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_database_performance_metrics(database_id: str = None, timespan: str = "PT24H") -> str:
    """
    Get performance metrics for databases (DTU, CPU, connections, storage).
    
    Args:
        database_id: Specific database resource ID
        timespan: Time span for metrics
    """
    if not database_id:
        # Get all SQL databases
        db_query = """
        Resources
        | where type in~ ('Microsoft.Sql/servers/databases', 'Microsoft.DocumentDB/databaseAccounts')
        | project id, name, type, resourceGroup, location
        | limit 10
        """
        
        db_result = await get_all_resources(db_query)
        
        try:
            db_data = json.loads(db_result)
            metrics_summary = {
                "timespan": timespan,
                "database_metrics": [],
                "summary": {
                    "total_databases": 0,
                    "high_utilization_dbs": 0
                }
            }
            
            if "data" in db_data and "rows" in db_data["data"]:
                for db in db_data["data"]["rows"]:
                    db_id = db[0]
                    db_name = db[1]
                    db_type = db[2]
                    
                    endpoint = f"{db_id}/providers/Microsoft.Insights/metrics"
                    
                    # Different metrics for different database types
                    if "Microsoft.Sql" in db_type:
                        metric_names = "cpu_percent,dtu_consumption_percent,connection_successful,storage_percent"
                    else:  # Cosmos DB
                        metric_names = "TotalRequestUnits,ProvisionedThroughput,DocumentCount,DataUsage"
                    
                    db_metrics = await make_azure_request("GET", endpoint, 
                                                                 params={
                                                                     "api-version": "2018-01-01",
                                                                     "metricnames": metric_names,
                                                                     "timespan": timespan,
                                                                     "interval": "PT1H",
                                                                     "aggregation": "Average,Maximum"
                                                                 })
                    
                    if "error" not in db_metrics:
                        metrics_summary["database_metrics"].append({
                            "database_id": db_id,
                            "database_name": db_name,
                            "database_type": db_type,
                            "metrics": db_metrics
                        })
                        metrics_summary["summary"]["total_databases"] += 1
            
            return json.dumps(metrics_summary, indent=2)
            
        except Exception as e:
            return f"Error processing database metrics: {str(e)}"
    
    # Single database metrics
    endpoint = f"{database_id}/providers/Microsoft.Insights/metrics"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2018-01-01",
                                                 "metricnames": "cpu_percent,dtu_consumption_percent,connection_successful,storage_percent,blocked_by_firewall",
                                                 "timespan": timespan,
                                                 "interval": "PT1H",
                                                 "aggregation": "Average,Maximum,Total"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving database metrics: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_activity_log_analysis(hours_back: int = 168) -> str:
    """
    Get activity log analysis to identify resource usage patterns and rarely accessed resources.
    
    Args:
        hours_back: Number of hours to look back (default: 168 = 7 days)
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Insights/eventtypes/management/values"
    
    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    
    filter_query = f"eventTimestamp ge '{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}' and eventTimestamp le '{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}'"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2015-04-01",
                                                 "$filter": filter_query,
                                                 "$select": "eventTimestamp,operationName,resourceId,resourceGroupName,resourceProviderName,status,subStatus,caller"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving activity log: {result.get('message', 'Unknown error')}"
    
    # Process activity log to identify usage patterns
    try:
        if "value" in result:
            activity_analysis = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours_analyzed": hours_back
                },
                "resource_activity": {},
                "summary": {
                    "total_events": len(result["value"]),
                    "unique_resources": 0,
                    "inactive_resources": []
                }
            }
            
            # Analyze resource activity
            for event in result["value"]:
                resource_id = event.get("resourceId", "")
                if resource_id:
                    if resource_id not in activity_analysis["resource_activity"]:
                        activity_analysis["resource_activity"][resource_id] = {
                            "event_count": 0,
                            "last_activity": "",
                            "operations": []
                        }
                    
                    activity_analysis["resource_activity"][resource_id]["event_count"] += 1
                    activity_analysis["resource_activity"][resource_id]["last_activity"] = event.get("eventTimestamp", "")
                    activity_analysis["resource_activity"][resource_id]["operations"].append(event.get("operationName", ""))
            
            activity_analysis["summary"]["unique_resources"] = len(activity_analysis["resource_activity"])
            
            # Identify resources with no recent activity
            for resource_id, activity in activity_analysis["resource_activity"].items():
                if activity["event_count"] < 5:  # Very low activity
                    activity_analysis["summary"]["inactive_resources"].append({
                        "resource_id": resource_id,
                        "event_count": activity["event_count"],
                        "last_activity": activity["last_activity"]
                    })
            
            return json.dumps(activity_analysis, indent=2)
        else:
            return json.dumps({"message": "No activity log data found", "result": result}, indent=2)
            
    except Exception as e:
        return f"Error processing activity log: {str(e)}"

@mcp.tool()
async def get_resource_utilization_summary() -> str:
    """
    Get a comprehensive summary of resource utilization across the subscription.
    """
    try:
        utilization_summary = {
            "metadata": {
                "subscription_id": AZURE_SUBSCRIPTION_ID,
                "generated_at": datetime.now().isoformat(),
                "analysis_scope": "resource_utilization"
            },
            "unused_resources": {},
            "performance_issues": {},
            "advisor_recommendations": {},
            "activity_patterns": {},
            "summary": {
                "total_potentially_unused": 0,
                "cost_optimization_opportunities": 0,
                "performance_alerts": 0
            }
        }
        
        print("Getting unused resources...", file=sys.stderr)
        unused_result = await get_unused_resources()
        utilization_summary["unused_resources"] = json.loads(unused_result)
        
        print("Getting advisor recommendations...", file=sys.stderr)
        advisor_result = await get_azure_advisor_detailed()
        utilization_summary["advisor_recommendations"] = json.loads(advisor_result)
        
        print("Getting activity patterns...", file=sys.stderr)
        activity_result = await get_activity_log_analysis(168)  # 7 days
        utilization_summary["activity_patterns"] = json.loads(activity_result)
        
        print("Getting VM performance metrics...", file=sys.stderr)
        vm_metrics_result = await get_vm_performance_metrics(None, "PT24H")
        utilization_summary["performance_issues"]["vm_metrics"] = json.loads(vm_metrics_result)
        
        # Calculate summary statistics
        if "data" in utilization_summary["unused_resources"] and "rows" in utilization_summary["unused_resources"]["data"]:
            utilization_summary["summary"]["total_potentially_unused"] = len(utilization_summary["unused_resources"]["data"]["rows"])
        
        if "value" in utilization_summary["advisor_recommendations"]:
            utilization_summary["summary"]["cost_optimization_opportunities"] = len([
                rec for rec in utilization_summary["advisor_recommendations"]["value"] 
                if rec.get("properties", {}).get("category") == "Cost"
            ])
        
        return json.dumps(utilization_summary, indent=2)
        
    except Exception as e:
        error_details = {
            "error": True,
            "message": f"Error getting resource utilization summary: {str(e)}",
            "type": type(e).__name__
        }
        return json.dumps(error_details, indent=2)

@mcp.tool()
async def get_alerts_overview() -> str:
    """
    Get active alerts from Azure Alerts Management across all subscriptions.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.AlertsManagement/alerts"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2019-05-05-preview",
                                                 "alertState": "New,Acknowledged"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving alerts overview: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_alert_rules() -> str:
    """
    Get metric alert rules and their configurations.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Insights/metricAlerts"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={"api-version": "2018-03-01"})
    
    if "error" in result and result["error"]:
        return f"Error retrieving alert rules: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_alert_details(alert_id: str) -> str:
    """
    Get detailed alert information including remediation steps.
    
    Args:
        alert_id: The alert ID to get details for
    """
    # Try Security Center alert first
    sec_endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Security/alerts/{alert_id}"
    sec_result = await make_azure_request("GET", sec_endpoint, 
                                                  params={"api-version": "2022-01-01"})
    
    if not (isinstance(sec_result, dict) and sec_result.get("error")):
        # Extract remediation steps
        remediation = sec_result.get("properties", {}).get("remediationSteps", [])
        return json.dumps({
            "alert": sec_result,
            "remediation_steps": remediation,
            "alert_type": "security"
        }, indent=2)
    
    # Fallback to AlertsManagement
    am_endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.AlertsManagement/alerts/{alert_id}"
    am_result = await make_azure_request("GET", am_endpoint, 
                                                 params={"api-version": "2019-05-05-preview"})
    
    if "error" in am_result and am_result["error"]:
        return f"Error retrieving alert details: {am_result.get('message', 'Unknown error')}"
    
    return json.dumps({
        "alert": am_result,
        "alert_type": "metric"
    }, indent=2)

@mcp.tool()
async def get_application_insights_data(app_insights_id: str = None, timespan: str = "PT24H") -> str:
    """
    Get Application Insights telemetry and performance data.
    
    Args:
        app_insights_id: Application Insights resource ID
        timespan: Time span for data retrieval
    """
    if not app_insights_id:
        # Get all Application Insights resources
        ai_query = """
        Resources
        | where type =~ 'Microsoft.Insights/components'
        | project id, name, resourceGroup, location, instrumentationKey = properties.InstrumentationKey
        | limit 10
        """
        
        ai_result = await get_all_resources(ai_query)
        
        try:
            ai_data = json.loads(ai_result)
            
            if "data" in ai_data and "rows" in ai_data["data"] and len(ai_data["data"]["rows"]) > 0:
                # Use first Application Insights resource
                app_insights_id = ai_data["data"]["rows"][0][0]
            else:
                return json.dumps({"error": "No Application Insights resources found"}, indent=2)
                
        except Exception as e:
            return f"Error processing Application Insights resources: {str(e)}"
    
    # Query Application Insights for performance data
    endpoint = f"{app_insights_id}/providers/Microsoft.Insights/metrics"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2018-01-01",
                                                 "metricnames": "requests/count,requests/duration,requests/failed,exceptions/count,pageViews/count",
                                                 "timespan": timespan,
                                                 "interval": "PT1H",
                                                 "aggregation": "Count,Average,Total"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving Application Insights data: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_resource_health_status() -> str:
    """
    Get resource health status across the subscription.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.ResourceHealth/availabilityStatuses"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2020-05-01",
                                                 "$filter": "Properties/AvailabilityState ne 'Available'"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving resource health status: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_log_analytics_data(workspace_id: str = None, query: str = None, timespan: str = "PT24H") -> str:
    """
    Query Log Analytics workspace for performance and diagnostic data.
    
    Args:
        workspace_id: Log Analytics workspace resource ID
        query: KQL query to execute
        timespan: Time span for the query
    """
    if not workspace_id:
        # Find Log Analytics workspaces
        la_query = """
        Resources
        | where type =~ 'Microsoft.OperationalInsights/workspaces'
        | project id, name, resourceGroup, location, customerId = properties.customerId
        | limit 5
        """
        
        la_result = await get_all_resources(la_query)
        
        try:
            la_data = json.loads(la_result)
            
            if "data" in la_data and "rows" in la_data["data"] and len(la_data["data"]["rows"]) > 0:
                workspace_id = la_data["data"]["rows"][0][0]
            else:
                return json.dumps({"error": "No Log Analytics workspaces found"}, indent=2)
                
        except Exception as e:
            return f"Error processing Log Analytics workspaces: {str(e)}"
    
    # Default query for performance data
    if not query:
        query = """
        Perf
        | where TimeGenerated > ago(24h)
        | where CounterName in ("% Processor Time", "Available MBytes", "Disk Reads/sec", "Disk Writes/sec")
        | summarize avg(CounterValue) by Computer, CounterName, bin(TimeGenerated, 1h)
        | order by TimeGenerated desc
        """
    
    endpoint = f"{workspace_id}/query"
    
    query_data = {
        "query": query,
        "timespan": timespan
    }
    
    result = await make_azure_request("POST", endpoint, 
                                             params={"api-version": "2020-08-01"}, 
                                             data=query_data)
    
    if "error" in result and result["error"]:
        return f"Error querying Log Analytics: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_secure_score_and_compliance() -> str:
    """
    Get Microsoft Defender secure score and regulatory compliance summary.
    """
    secure_score_endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Security/secureScores"
    compliance_endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Security/regulatoryComplianceStandards"
    
    # Get secure score
    secure_score_result = await make_azure_request("GET", secure_score_endpoint, 
                                                           params={"api-version": "2020-01-01"})
    
    # Get compliance standards
    compliance_result = await make_azure_request("GET", compliance_endpoint, 
                                                         params={"api-version": "2019-01-01-preview"})
    
    return json.dumps({
        "secure_score": secure_score_result,
        "regulatory_compliance": compliance_result
    }, indent=2)

@mcp.tool()
async def get_security_incidents() -> str:
    """
    Get Azure Sentinel security incidents and their details.
    """
    # First find Sentinel workspaces
    sentinel_query = """
    Resources
    | where type =~ 'Microsoft.OperationalInsights/workspaces'
    | where properties.features.enableLogAccessUsingOnlyResourcePermissions == true
    | project id, name, resourceGroup, location
    """
    
    sentinel_result = await get_all_resources(sentinel_query)
    
    try:
        sentinel_data = json.loads(sentinel_result)
        
        incidents_summary = {
            "total_incidents": 0,
            "workspaces": [],
            "incidents_by_severity": {},
            "recent_incidents": []
        }
        
        if "data" in sentinel_data and "rows" in sentinel_data["data"]:
            for workspace in sentinel_data["data"]["rows"]:
                workspace_id = workspace[0]
                workspace_name = workspace[1]
                
                # Get incidents for this workspace
                incidents_endpoint = f"{workspace_id}/providers/Microsoft.SecurityInsights/incidents"
                incidents_result = await make_azure_request("GET", incidents_endpoint, 
                                                                   params={"api-version": "2021-10-01"})
                
                if not (isinstance(incidents_result, dict) and incidents_result.get("error")):
                    incidents = incidents_result.get("value", [])
                    
                    workspace_info = {
                        "workspace_name": workspace_name,
                        "workspace_id": workspace_id,
                        "incident_count": len(incidents),
                        "incidents": incidents
                    }
                    
                    incidents_summary["workspaces"].append(workspace_info)
                    incidents_summary["total_incidents"] += len(incidents)
                    
                    # Categorize by severity
                    for incident in incidents:
                        severity = incident.get("properties", {}).get("severity", "Unknown")
                        incidents_summary["incidents_by_severity"][severity] = incidents_summary["incidents_by_severity"].get(severity, 0) + 1
        
        return json.dumps(incidents_summary, indent=2)
        
    except Exception as e:
        return f"Error retrieving security incidents: {str(e)}"

@mcp.tool()
async def get_threat_intelligence_indicators() -> str:
    """
    Get threat intelligence indicators from Azure Sentinel.
    """
    # Find Sentinel workspaces first
    sentinel_query = """
    Resources
    | where type =~ 'Microsoft.OperationalInsights/workspaces'
    | project id, name, resourceGroup, location
    | limit 5
    """
    
    sentinel_result = await get_all_resources(sentinel_query)
    
    try:
        sentinel_data = json.loads(sentinel_result)
        
        threat_intel_summary = {
            "total_indicators": 0,
            "workspaces": [],
            "indicators_by_type": {}
        }
        
        if "data" in sentinel_data and "rows" in sentinel_data["data"]:
            for workspace in sentinel_data["data"]["rows"]:
                workspace_id = workspace[0]
                workspace_name = workspace[1]
                
                # Get threat intelligence indicators
                ti_endpoint = f"{workspace_id}/providers/Microsoft.SecurityInsights/threatIntelligence/main/indicators"
                ti_result = await make_azure_request("GET", ti_endpoint, 
                                                            params={"api-version": "2021-10-01"})
                
                if not (isinstance(ti_result, dict) and ti_result.get("error")):
                    indicators = ti_result.get("value", [])
                    
                    workspace_info = {
                        "workspace_name": workspace_name,
                        "workspace_id": workspace_id,
                        "indicators_count": len(indicators),
                        "indicators": indicators[:10]  # Limit to first 10 for performance
                    }
                    
                    threat_intel_summary["workspaces"].append(workspace_info)
                    threat_intel_summary["total_indicators"] += len(indicators)
        
        return json.dumps(threat_intel_summary, indent=2)
        
    except Exception as e:
        return f"Error retrieving threat intelligence indicators: {str(e)}"

@mcp.tool()
async def get_security_recommendations_detailed() -> str:
    """
    Get detailed security recommendations with remediation steps and impact assessment.
    """
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Security/assessments"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={
                                                 "api-version": "2020-01-01",
                                                 "$expand": "links,metadata"
                                             })
    
    if "error" in result and result["error"]:
        return f"Error retrieving detailed security recommendations: {result.get('message', 'Unknown error')}"
    
    # Process recommendations to add remediation guidance
    try:
        if "value" in result:
            processed_recommendations = []
            
            for recommendation in result["value"]:
                props = recommendation.get("properties", {})
                metadata = props.get("metadata", {})
                
                processed_rec = {
                    "id": recommendation.get("id", ""),
                    "name": recommendation.get("name", ""),
                    "display_name": metadata.get("displayName", ""),
                    "description": metadata.get("description", ""),
                    "severity": metadata.get("severity", ""),
                    "category": metadata.get("categories", []),
                    "status": props.get("status", {}),
                    "remediation_description": metadata.get("remediationDescription", ""),
                    "implementation_effort": metadata.get("implementationEffort", ""),
                    "user_impact": metadata.get("userImpact", ""),
                    "threats": metadata.get("threats", []),
                    "resource_details": props.get("resourceDetails", {}),
                    "additional_data": props.get("additionalData", {})
                }
                
                processed_recommendations.append(processed_rec)
            
            # Sort by severity and status
            severity_order = {"High": 3, "Medium": 2, "Low": 1}
            processed_recommendations.sort(
                key=lambda x: (
                    severity_order.get(x.get("severity", ""), 0),
                    1 if x.get("status", {}).get("code") == "Unhealthy" else 0
                ),
                reverse=True
            )
            
            summary = {
                "total_recommendations": len(processed_recommendations),
                "critical_recommendations": [r for r in processed_recommendations if r.get("severity") == "High" and r.get("status", {}).get("code") == "Unhealthy"],
                "all_recommendations": processed_recommendations
            }
            
            return json.dumps(summary, indent=2)
            
    except Exception as e:
        return f"Error processing security recommendations: {str(e)}"
    
    return json.dumps(result, indent=2)

# === RESOURCES ===

@mcp.resource("https://azure-billing/subscription")
async def get_subscription_resource() -> str:
    """Get details about the current subscription."""
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={"api-version": "2022-12-01"})
    
    if "error" in result and result["error"]:
        return f"Error retrieving subscription details: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.resource("https://azure-billing/billing-summary")
async def get_azure_summary_resource() -> str:
    """Get a summary of current billing for the subscription."""
    # We'll use cost management API to get a quick summary
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.CostManagement/query"
    
    query_data = {
        "type": "ActualCost",
        "timeframe": "MonthToDate",
        "dataSet": {
            "granularity": "None",
            "aggregation": {
                "totalCost": {
                    "name": "Cost",
                    "function": "Sum"
                }
            }
        }
    }
    
    result = await make_azure_request("POST", endpoint, 
                                             params={"api-version": "2023-03-01"}, 
                                             data=query_data)
    
    if "error" in result and result["error"]:
        return f"Error retrieving billing summary: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.resource("https://azure-billing/budgets")
async def get_budgets_resource() -> str:
    """Get all budgets for the subscription."""
    endpoint = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Consumption/budgets"
    
    result = await make_azure_request("GET", endpoint, 
                                             params={"api-version": "2023-04-01"})
    
    if "error" in result and result["error"]:
        return f"Error retrieving budgets: {result.get('message', 'Unknown error')}"
    
    return json.dumps(result, indent=2)

@mcp.resource("https://azure-resources/all")
async def get_all_resources_resource() -> str:
    """Get all Azure resources in the subscription."""
    return await get_all_resources()

@mcp.resource("https://azure-resources/network-topology")
async def get_network_topology_resource() -> str:
    """Get network topology for the subscription."""
    return await get_network_topology()

@mcp.resource("https://azure-resources/hierarchy")
async def get_resource_hierarchy_resource() -> str:
    """Get resource hierarchy organized by resource groups."""
    return await get_resource_hierarchy()

@mcp.resource("https://azure-resources/dependencies")
async def get_resource_dependencies_resource() -> str:
    """Get resource dependencies and relationships."""
    return await get_resource_dependencies()

@mcp.resource("https://azure-optimization/unused-resources")
async def get_unused_resources_resource() -> str:
    """Get potentially unused or under-utilized resources."""
    return await get_unused_resources()

@mcp.resource("https://azure-optimization/utilization-summary")
async def get_utilization_summary_resource() -> str:
    """Get comprehensive resource utilization summary."""
    return await get_resource_utilization_summary()

@mcp.resource("https://azure-performance/vm-metrics")
async def get_vm_performance_resource() -> str:
    """Get VM performance metrics."""
    return await get_vm_performance_metrics()

@mcp.resource("https://azure-performance/storage-metrics")
async def get_storage_performance_resource() -> str:
    """Get storage performance metrics."""
    return await get_storage_performance_metrics()

@mcp.resource("https://azure-optimization/advisor-recommendations")
async def get_advisor_recommendations_resource() -> str:
    """Get detailed Azure Advisor recommendations."""
    return await get_azure_advisor_detailed()

@mcp.resource("https://azure-security/alerts")
async def get_security_alerts_resource() -> str:
    """Get Azure Security Center alerts and incidents."""
    return await get_security_center_alerts()

@mcp.resource("https://azure-security/assessments")
async def get_security_assessments_resource() -> str:
    """Get Azure Security Center security assessments."""
    return await get_security_assessments()

@mcp.resource("https://azure-security/defender-status")
async def get_defender_status_resource() -> str:
    """Get Microsoft Defender for Cloud status."""
    return await get_defender_for_cloud_status()

@mcp.resource("https://azure-security/keyvault-security")
async def get_keyvault_security_resource() -> str:
    """Get Key Vault security configuration analysis."""
    return await get_key_vault_security_status()

@mcp.resource("https://azure-security/network-security")
async def get_network_security_resource() -> str:
    """Get network security analysis including NSGs and firewalls."""
    return await get_network_security_analysis()

@mcp.resource("https://azure-alerts/overview")
async def get_alerts_overview_resource() -> str:
    """Get active alerts overview across the subscription."""
    return await get_alerts_overview()

@mcp.resource("https://azure-alerts/rules")
async def get_alert_rules_resource() -> str:
    """Get metric alert rules and configurations."""
    return await get_alert_rules()

@mcp.resource("https://azure-performance/application-insights")
async def get_application_insights_resource() -> str:
    """Get Application Insights performance data."""
    return await get_application_insights_data()

@mcp.resource("https://azure-performance/resource-health")
async def get_resource_health_resource() -> str:
    """Get resource health status across the subscription."""
    return await get_resource_health_status()

@mcp.resource("https://azure-performance/log-analytics")
async def get_log_analytics_resource() -> str:
    """Get Log Analytics performance data."""
    return await get_log_analytics_data()

@mcp.resource("https://azure-security/secure-score")
async def get_secure_score_resource() -> str:
    """Get Microsoft Defender secure score and compliance."""
    return await get_secure_score_and_compliance()

@mcp.resource("https://azure-security/incidents")
async def get_security_incidents_resource() -> str:
    """Get Azure Sentinel security incidents."""
    return await get_security_incidents()

@mcp.resource("https://azure-security/threat-intelligence")
async def get_threat_intelligence_resource() -> str:
    """Get threat intelligence indicators."""
    return await get_threat_intelligence_indicators()

@mcp.resource("https://azure-security/recommendations-detailed")
async def get_security_recommendations_detailed_resource() -> str:
    """Get detailed security recommendations with remediation steps."""
    return await get_security_recommendations_detailed()

# === PROMPTS ===

@mcp.prompt("analyze_costs")
def analyze_costs_prompt(timeframe: str = None, group_by: str = None) -> str:
    """
    A prompt template for analyzing Azure costs.
    
    Args:
        timeframe: The time period for analysis (MonthToDate, TheLastMonth, etc.)
        group_by: Property to group the analysis by (ResourceGroup, ResourceId, etc.)
    """
    if timeframe and group_by:
        return f"Please analyze my Azure costs for the timeframe '{timeframe}', grouped by '{group_by}'. What insights can you provide about my spending patterns, and are there any anomalies or areas where I could optimize costs?"
    elif timeframe:
        return f"Please analyze my Azure costs for the timeframe '{timeframe}'. What insights can you provide about my spending patterns, and are there any anomalies or areas where I could optimize costs?"
    else:
        return "Please analyze my Azure costs. What insights can you provide about my spending patterns, and are there any anomalies or areas where I could optimize costs?"

@mcp.prompt("budget_recommendations")
def budget_recommendations_prompt() -> str:
    """
    A prompt template for getting budget recommendations.
    """
    return "Based on my Azure usage and spending patterns, what budget recommendations would you suggest? Please analyze my current spending and provide realistic budget thresholds for different resource categories."

@mcp.prompt("cost_reduction")
def cost_reduction_prompt() -> str:
    """
    A prompt template for getting cost reduction suggestions.
    """
    return "Please analyze my Azure billing data and suggest specific ways I could reduce costs. Identify resources that might be underutilized, oversized, or could benefit from reserved instances or savings plans."

@mcp.prompt("analyze_architecture")
def analyze_architecture_prompt(focus: str = None) -> str:
    """
    A prompt template for analyzing Azure architecture.
    
    Args:
        focus: The focus area for analysis (network, compute, storage, security, etc.)
    """
    if focus:
        return f"Please analyze my Azure architecture with a focus on '{focus}'. Examine the resources, their relationships, and provide insights about the current setup. Identify any potential improvements for reliability, security, performance, and cost optimization."
    else:
        return "Please analyze my Azure architecture. Examine all resources, their relationships, and provide insights about the current setup. Identify any potential improvements for reliability, security, performance, and cost optimization."

@mcp.prompt("network_topology_analysis")
def network_topology_analysis_prompt() -> str:
    """
    A prompt template for analyzing network topology.
    """
    return "Please analyze my Azure network topology. Examine the virtual networks, subnets, network security groups, and connectivity patterns. Identify any security gaps, performance bottlenecks, or architectural improvements that could be made."

@mcp.prompt("resource_optimization")
def resource_optimization_prompt() -> str:
    """
    A prompt template for resource optimization recommendations.
    """
    return "Please analyze my Azure resources and provide optimization recommendations. Look for unused resources, oversized instances, missing best practices, and opportunities for consolidation or rightsizing."

@mcp.prompt("performance_analysis")
def performance_analysis_prompt(resource_type: str = None) -> str:
    """
    A prompt template for Azure performance analysis.
    
    Args:
        resource_type: The type of resource to focus on (vm, storage, database, etc.)
    """
    if resource_type:
        return f"Please analyze the performance of my Azure {resource_type} resources. Identify any performance bottlenecks, high utilization issues, or optimization opportunities. Focus on CPU, memory, disk I/O, and network metrics."
    else:
        return "Please analyze the performance of my Azure resources. Identify any performance bottlenecks, high utilization issues, or optimization opportunities across VMs, storage accounts, and databases."

@mcp.prompt("unused_resources_cleanup")
def unused_resources_cleanup_prompt() -> str:
    """
    A prompt template for identifying unused resources that can be cleaned up.
    """
    return "Please identify unused or under-utilized Azure resources that could potentially be deleted to reduce costs. Look for stopped VMs, unattached disks, unused network interfaces, and resources with minimal activity. Provide specific recommendations for cleanup while considering data retention and business requirements."

@mcp.prompt("utilization_summary")
def utilization_summary_prompt() -> str:
    """
    A prompt template for comprehensive resource utilization analysis.
    """
    return "Please provide a comprehensive summary of my Azure resource utilization. Include performance metrics, usage patterns, cost optimization opportunities, and specific recommendations for improving efficiency. Focus on actionable insights that can reduce costs and improve performance."

@mcp.prompt("advisor_insights")
def advisor_insights_prompt(category: str = None) -> str:
    """
    A prompt template for Azure Advisor recommendations.
    
    Args:
        category: The category to focus on (Cost, Performance, Security, Reliability, etc.)
    """
    if category:
        return f"Please analyze Azure Advisor recommendations specifically for '{category}'. Provide detailed insights and prioritized action items based on the recommendations."
    else:
        return "Please analyze all Azure Advisor recommendations. Categorize them by impact and effort, and provide a prioritized action plan for implementing these improvements."

@mcp.prompt("security_assessment")
def security_assessment_prompt(focus_area: str = None) -> str:
    """
    A prompt template for comprehensive Azure security assessment.
    
    Args:
        focus_area: The security area to focus on (alerts, assessments, network, etc.)
    """
    if focus_area:
        return f"Please conduct a comprehensive security assessment of my Azure environment with focus on '{focus_area}'. Identify security alerts, failed assessments, misconfigurations, and provide prioritized remediation steps."
    else:
        return "Please conduct a comprehensive security assessment of my Azure environment. Analyze security alerts, assessments, Defender for Cloud status, Key Vault configurations, and network security. Provide prioritized recommendations for improving security posture."

@mcp.prompt("security_alerts_analysis")
def security_alerts_analysis_prompt() -> str:
    """
    A prompt template for analyzing security alerts and incidents.
    """
    return "Please analyze my Azure Security Center alerts and security incidents. Focus on critical and high-severity alerts, recent security events, and provide detailed remediation guidance for each type of security issue identified."

@mcp.prompt("defender_coverage_analysis")
def defender_coverage_analysis_prompt() -> str:
    """
    A prompt template for analyzing Microsoft Defender for Cloud coverage.
    """
    return "Please analyze my Microsoft Defender for Cloud coverage across all subscriptions and resource types. Identify gaps in protection, recommend enabling Defender for critical services, and provide cost-benefit analysis for security coverage improvements."

@mcp.prompt("network_security_review")
def network_security_review_prompt() -> str:
    """
    A prompt template for network security configuration review.
    """
    return "Please review my Azure network security configurations including Network Security Groups, Azure Firewalls, and public IP exposure. Identify overly permissive rules, security gaps, and provide specific recommendations to improve network security posture."

@mcp.prompt("keyvault_security_audit")
def keyvault_security_audit_prompt() -> str:
    """
    A prompt template for Key Vault security audit.
    """
    return "Please audit my Azure Key Vault security configurations. Check for proper soft delete, purge protection, network access restrictions, and provide recommendations to improve secret management security across all Key Vaults."

@mcp.prompt("security_compliance_review")
def security_compliance_review_prompt(standard: str = None) -> str:
    """
    A prompt template for security compliance review.
    
    Args:
        standard: The compliance standard to focus on (ISO 27001, SOC 2, PCI DSS, etc.)
    """
    if standard:
        return f"Please review my Azure security posture against '{standard}' compliance requirements. Analyze current assessments, identify compliance gaps, and provide a roadmap for achieving and maintaining '{standard}' compliance."
    else:
        return "Please review my Azure security compliance status across all applicable standards. Identify failed controls, compliance gaps, and provide prioritized recommendations for improving overall compliance posture."

@mcp.prompt("alerts_analysis")
def alerts_analysis_prompt(severity: str = None) -> str:
    """
    A prompt template for analyzing Azure alerts and their remediation.
    
    Args:
        severity: Filter by alert severity (Critical, High, Medium, Low)
    """
    if severity:
        return f"Please analyze my Azure alerts filtered by {severity} severity. Focus on active alerts, their root causes, and provide step-by-step remediation guidance. Include impact assessment and prevention strategies."
    else:
        return "Please analyze all my Azure alerts across the subscription. Categorize by severity and type, identify patterns, and provide comprehensive remediation guidance for critical issues. Include recommendations for alert optimization."

@mcp.prompt("performance_troubleshooting")
def performance_troubleshooting_prompt(resource_type: str = None) -> str:
    """
    A prompt template for performance troubleshooting using monitoring data.
    
    Args:
        resource_type: Focus on specific resource type (vm, app-service, database, etc.)
    """
    if resource_type:
        return f"Please troubleshoot performance issues in my Azure {resource_type} resources. Analyze metrics, logs, and health status to identify bottlenecks, resource constraints, and optimization opportunities. Provide specific remediation steps."
    else:
        return "Please perform comprehensive performance troubleshooting across my Azure environment. Analyze Application Insights, Log Analytics, and resource health data to identify performance issues, bottlenecks, and provide actionable remediation steps."

@mcp.prompt("security_incident_response")
def security_incident_response_prompt() -> str:
    """
    A prompt template for security incident response and remediation.
    """
    return "Please analyze my Azure security incidents and alerts. Prioritize by severity and impact, provide detailed incident response procedures, remediation steps, and preventive measures. Include threat intelligence context where available."

@mcp.prompt("threat_hunting")
def threat_hunting_prompt() -> str:
    """
    A prompt template for proactive threat hunting using Azure security data.
    """
    return "Please conduct proactive threat hunting across my Azure environment. Analyze security incidents, threat intelligence indicators, and security assessments to identify potential threats, IOCs, and attack patterns. Provide hunting queries and remediation strategies."

@mcp.prompt("compliance_remediation")
def compliance_remediation_prompt(standard: str = None) -> str:
    """
    A prompt template for compliance remediation based on security assessments.
    
    Args:
        standard: Focus on specific compliance standard
    """
    if standard:
        return f"Please analyze my Azure security posture for {standard} compliance. Review security assessments, identify compliance gaps, and provide detailed remediation roadmap with prioritized actions and timelines."
    else:
        return "Please analyze my Azure security compliance across all standards. Review secure score, regulatory compliance assessments, and provide comprehensive remediation plan to improve security posture and compliance ratings."

@mcp.prompt("alert_optimization")
def alert_optimization_prompt() -> str:
    """
    A prompt template for optimizing alert rules and reducing noise.
    """
    return "Please analyze my Azure alert rules and configurations. Identify noisy alerts, gaps in monitoring coverage, and opportunities for optimization. Provide recommendations for improving alert quality, reducing false positives, and ensuring critical issues are properly monitored."

@mcp.tool("get_security_center_alerts")
async def get_security_center_alerts() -> str:
    """Get Azure Security Center alerts and security incidents."""
    token = await get_azure_token()
    if not token:
        return json.dumps({"error": "Authentication failed"})
    
    try:
        # Get all subscriptions first
        async with httpx.AsyncClient() as client:
            subscription_response = await client.get(
                "https://management.azure.com/subscriptions",
                headers={"Authorization": f"Bearer {token}"},
                params={"api-version": "2020-01-01"}
            )
            subscription_response.raise_for_status()
            subscriptions = subscription_response.json().get("value", [])
            
            all_alerts = []
            
            for subscription in subscriptions:
                subscription_id = subscription["subscriptionId"]
                
                # Get Security Center alerts
                alerts_response = await client.get(
                    f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Security/alerts",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"api-version": "2022-01-01"}
                )
                
                if alerts_response.status_code == 200:
                    alerts_data = alerts_response.json()
                    subscription_alerts = alerts_data.get("value", [])
                    
                    for alert in subscription_alerts:
                        alert_info = {
                            "subscription_id": subscription_id,
                            "subscription_name": subscription.get("displayName", "Unknown"),
                            "alert_id": alert.get("id", ""),
                            "alert_name": alert.get("name", ""),
                            "severity": alert.get("properties", {}).get("severity", ""),
                            "status": alert.get("properties", {}).get("status", ""),
                            "alert_type": alert.get("properties", {}).get("alertType", ""),
                            "description": alert.get("properties", {}).get("description", ""),
                            "start_time": alert.get("properties", {}).get("startTimeUtc", ""),
                            "end_time": alert.get("properties", {}).get("endTimeUtc", ""),
                            "compromised_entity": alert.get("properties", {}).get("compromisedEntity", ""),
                            "remediation_steps": alert.get("properties", {}).get("remediationSteps", []),
                            "extended_properties": alert.get("properties", {}).get("extendedProperties", {})
                        }
                        all_alerts.append(alert_info)
            
            summary = {
                "total_alerts": len(all_alerts),
                "alerts_by_severity": {},
                "alerts_by_status": {},
                "recent_alerts": [],
                "critical_alerts": [],
                "all_alerts": all_alerts
            }
            
            # Categorize alerts
            for alert in all_alerts:
                severity = alert.get("severity", "Unknown")
                status = alert.get("status", "Unknown")
                
                summary["alerts_by_severity"][severity] = summary["alerts_by_severity"].get(severity, 0) + 1
                summary["alerts_by_status"][status] = summary["alerts_by_status"].get(status, 0) + 1
                
                if severity in ["High", "Critical"]:
                    summary["critical_alerts"].append(alert)
            
            # Get recent alerts (last 7 days)
            from datetime import datetime, timedelta
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            
            for alert in all_alerts:
                start_time_str = alert.get("start_time", "")
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_time >= recent_cutoff:
                            summary["recent_alerts"].append(alert)
                    except:
                        pass
            
            return json.dumps(summary, indent=2)
            
    except Exception as e:
        return json.dumps({"error": "Failed to get security alerts", "details": str(e)})

@mcp.tool("get_security_assessments")
async def get_security_assessments() -> str:
    """Get Azure Security Center security assessments and recommendations."""
    token = await get_azure_token()
    if not token:
        return json.dumps({"error": "Authentication failed"})
    
    try:
        async with httpx.AsyncClient() as client:
            # Get all subscriptions
            subscription_response = await client.get(
                "https://management.azure.com/subscriptions",
                headers={"Authorization": f"Bearer {token}"},
                params={"api-version": "2020-01-01"}
            )
            subscription_response.raise_for_status()
            subscriptions = subscription_response.json().get("value", [])
            
            all_assessments = []
            
            for subscription in subscriptions:
                subscription_id = subscription["subscriptionId"]
                
                # Get security assessments
                assessments_response = await client.get(
                    f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Security/assessments",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"api-version": "2020-01-01"}
                )
                
                if assessments_response.status_code == 200:
                    assessments_data = assessments_response.json()
                    subscription_assessments = assessments_data.get("value", [])
                    
                    for assessment in subscription_assessments:
                        props = assessment.get("properties", {})
                        status = props.get("status", {})
                        
                        assessment_info = {
                            "subscription_id": subscription_id,
                            "subscription_name": subscription.get("displayName", "Unknown"),
                            "assessment_id": assessment.get("id", ""),
                            "assessment_name": assessment.get("name", ""),
                            "display_name": props.get("displayName", ""),
                            "description": props.get("description", ""),
                            "severity": props.get("metadata", {}).get("severity", ""),
                            "category": props.get("metadata", {}).get("categories", []),
                            "status_code": status.get("code", ""),
                            "status_cause": status.get("cause", ""),
                            "status_description": status.get("description", ""),
                            "resource_details": props.get("resourceDetails", {}),
                            "additional_data": props.get("additionalData", {})
                        }
                        all_assessments.append(assessment_info)
            
            # Categorize assessments
            summary = {
                "total_assessments": len(all_assessments),
                "assessments_by_severity": {},
                "assessments_by_status": {},
                "failed_assessments": [],
                "critical_findings": [],
                "all_assessments": all_assessments
            }
            
            for assessment in all_assessments:
                severity = assessment.get("severity", "Unknown")
                status_code = assessment.get("status_code", "Unknown")
                
                summary["assessments_by_severity"][severity] = summary["assessments_by_severity"].get(severity, 0) + 1
                summary["assessments_by_status"][status_code] = summary["assessments_by_status"].get(status_code, 0) + 1
                
                if status_code in ["Unhealthy", "Failed"]:
                    summary["failed_assessments"].append(assessment)
                
                if severity in ["High", "Critical"] and status_code in ["Unhealthy", "Failed"]:
                    summary["critical_findings"].append(assessment)
            
            return json.dumps(summary, indent=2)
            
    except Exception as e:
        return json.dumps({"error": "Failed to get security assessments", "details": str(e)})

@mcp.tool("get_defender_for_cloud_status")
async def get_defender_for_cloud_status() -> str:
    """Get Microsoft Defender for Cloud enablement status and coverage."""
    token = await get_azure_token()
    if not token:
        return json.dumps({"error": "Authentication failed"})
    
    try:
        async with httpx.AsyncClient() as client:
            subscription_response = await client.get(
                "https://management.azure.com/subscriptions",
                headers={"Authorization": f"Bearer {token}"},
                params={"api-version": "2020-01-01"}
            )
            subscription_response.raise_for_status()
            subscriptions = subscription_response.json().get("value", [])
            
            all_pricings = []
            
            for subscription in subscriptions:
                subscription_id = subscription["subscriptionId"]
                
                # Get Defender for Cloud pricing/enablement status
                pricing_response = await client.get(
                    f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Security/pricings",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"api-version": "2022-03-01"}
                )
                
                if pricing_response.status_code == 200:
                    pricing_data = pricing_response.json()
                    subscription_pricings = pricing_data.get("value", [])
                    
                    for pricing in subscription_pricings:
                        props = pricing.get("properties", {})
                        pricing_info = {
                            "subscription_id": subscription_id,
                            "subscription_name": subscription.get("displayName", "Unknown"),
                            "resource_type": pricing.get("name", ""),
                            "pricing_tier": props.get("pricingTier", ""),
                            "enabled": props.get("pricingTier", "") == "Standard",
                            "free_trial_remaining_days": props.get("freeTrialRemainingTime", ""),
                            "subplan": props.get("subPlan", ""),
                            "extensions": props.get("extensions", [])
                        }
                        all_pricings.append(pricing_info)
            
            # Analyze coverage
            summary = {
                "total_resource_types": len(all_pricings),
                "enabled_services": len([p for p in all_pricings if p["enabled"]]),
                "disabled_services": len([p for p in all_pricings if not p["enabled"]]),
                "coverage_by_subscription": {},
                "coverage_by_service": {},
                "recommendations": [],
                "all_pricings": all_pricings
            }
            
            # Group by subscription
            for pricing in all_pricings:
                sub_id = pricing["subscription_id"]
                if sub_id not in summary["coverage_by_subscription"]:
                    summary["coverage_by_subscription"][sub_id] = {
                        "subscription_name": pricing["subscription_name"],
                        "enabled": 0,
                        "disabled": 0,
                        "services": []
                    }
                
                if pricing["enabled"]:
                    summary["coverage_by_subscription"][sub_id]["enabled"] += 1
                else:
                    summary["coverage_by_subscription"][sub_id]["disabled"] += 1
                
                summary["coverage_by_subscription"][sub_id]["services"].append({
                    "service": pricing["resource_type"],
                    "enabled": pricing["enabled"]
                })
                
                # Track service coverage across subscriptions
                service = pricing["resource_type"]
                if service not in summary["coverage_by_service"]:
                    summary["coverage_by_service"][service] = {"enabled": 0, "disabled": 0}
                
                if pricing["enabled"]:
                    summary["coverage_by_service"][service]["enabled"] += 1
                else:
                    summary["coverage_by_service"][service]["disabled"] += 1
            
            # Generate recommendations
            critical_services = ["VirtualMachines", "SqlServers", "StorageAccounts", "KubernetesService", "ContainerRegistry"]
            
            for service in critical_services:
                disabled_count = summary["coverage_by_service"].get(service, {}).get("disabled", 0)
                if disabled_count > 0:
                    summary["recommendations"].append(f"Enable Defender for {service} - {disabled_count} subscription(s) not protected")
            
            return json.dumps(summary, indent=2)
            
    except Exception as e:
        return json.dumps({"error": "Failed to get Defender for Cloud status", "details": str(e)})

@mcp.tool("get_key_vault_security_status")
async def get_key_vault_security_status() -> str:
    """Get Azure Key Vault security configuration and potential issues."""
    token = await get_azure_token()
    if not token:
        return json.dumps({"error": "Authentication failed"})
    
    try:
        async with httpx.AsyncClient() as client:
            # Get all Key Vaults using Resource Graph
            query = """
            Resources
            | where type == "microsoft.keyvault/vaults"
            | extend vaultUri = properties.vaultUri,
                     enabledForDeployment = properties.enabledForDeployment,
                     enabledForTemplateDeployment = properties.enabledForTemplateDeployment,
                     enabledForDiskEncryption = properties.enabledForDiskEncryption,
                     enableSoftDelete = properties.enableSoftDelete,
                     softDeleteRetentionInDays = properties.softDeleteRetentionInDays,
                     enablePurgeProtection = properties.enablePurgeProtection,
                     publicNetworkAccess = properties.publicNetworkAccess,
                     networkAcls = properties.networkAcls
            | project id, name, resourceGroup, location, subscriptionId,
                     vaultUri, enabledForDeployment, enabledForTemplateDeployment,
                     enabledForDiskEncryption, enableSoftDelete, softDeleteRetentionInDays,
                     enablePurgeProtection, publicNetworkAccess, networkAcls
            | limit 1000
            """
            
            response = await client.post(
                "https://management.azure.com/providers/Microsoft.ResourceGraph/resources",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query},
                params={"api-version": "2021-03-01"}
            )
            response.raise_for_status()
            data = response.json()
            key_vaults = data.get("data", [])
            
            security_analysis = []
            security_issues = []
            
            for kv in key_vaults:
                vault_analysis = {
                    "vault_name": kv.get("name", ""),
                    "resource_group": kv.get("resourceGroup", ""),
                    "subscription_id": kv.get("subscriptionId", ""),
                    "location": kv.get("location", ""),
                    "vault_uri": kv.get("vaultUri", ""),
                    "security_config": {
                        "soft_delete_enabled": kv.get("enableSoftDelete", False),
                        "purge_protection_enabled": kv.get("enablePurgeProtection", False),
                        "public_network_access": kv.get("publicNetworkAccess", ""),
                        "soft_delete_retention_days": kv.get("softDeleteRetentionInDays", 0)
                    },
                    "security_score": 0,
                    "security_issues": [],
                    "recommendations": []
                }
                
                # Security scoring and issue detection
                score = 100
                
                # Check soft delete
                if not kv.get("enableSoftDelete", False):
                    vault_analysis["security_issues"].append("Soft delete not enabled")
                    vault_analysis["recommendations"].append("Enable soft delete for data protection")
                    score -= 25
                
                # Check purge protection
                if not kv.get("enablePurgeProtection", False):
                    vault_analysis["security_issues"].append("Purge protection not enabled")
                    vault_analysis["recommendations"].append("Enable purge protection for critical vaults")
                    score -= 20
                
                # Check public network access
                if kv.get("publicNetworkAccess", "").lower() == "enabled":
                    vault_analysis["security_issues"].append("Public network access enabled")
                    vault_analysis["recommendations"].append("Restrict network access using private endpoints")
                    score -= 20
                
                # Check retention period
                retention_days = kv.get("softDeleteRetentionInDays", 0)
                if retention_days < 30:
                    vault_analysis["security_issues"].append(f"Short retention period: {retention_days} days")
                    vault_analysis["recommendations"].append("Increase soft delete retention to at least 30 days")
                    score -= 10
                
                vault_analysis["security_score"] = max(0, score)
                security_analysis.append(vault_analysis)
                
                # Collect critical security issues
                if vault_analysis["security_score"] < 70:
                    security_issues.append({
                        "vault_name": vault_analysis["vault_name"],
                        "security_score": vault_analysis["security_score"],
                        "critical_issues": vault_analysis["security_issues"]
                    })
            
            summary = {
                "total_key_vaults": len(key_vaults),
                "average_security_score": round(sum(kv["security_score"] for kv in security_analysis) / len(security_analysis), 2) if security_analysis else 0,
                "vaults_with_issues": len(security_issues),
                "common_issues": {},
                "security_recommendations": [],
                "critical_vaults": security_issues,
                "all_vaults": security_analysis
            }
            
            # Analyze common issues
            all_issues = []
            for vault in security_analysis:
                all_issues.extend(vault["security_issues"])
            
            for issue in set(all_issues):
                summary["common_issues"][issue] = all_issues.count(issue)
            
            # Generate top recommendations
            if summary["common_issues"]:
                top_issues = sorted(summary["common_issues"].items(), key=lambda x: x[1], reverse=True)[:3]
                for issue, count in top_issues:
                    summary["security_recommendations"].append(f"Address '{issue}' affecting {count} vault(s)")
            
            return json.dumps(summary, indent=2)
            
    except Exception as e:
        return json.dumps({"error": "Failed to get Key Vault security status", "details": str(e)})

@mcp.tool("get_network_security_analysis")
async def get_network_security_analysis() -> str:
    """Analyze network security configurations including NSGs, firewalls, and network access."""
    token = await get_azure_token()
    if not token:
        return json.dumps({"error": "Authentication failed"})
    
    try:
        async with httpx.AsyncClient() as client:
            # Get Network Security Groups
            nsg_query = """
            Resources
            | where type == "microsoft.network/networksecuritygroups"
            | extend rules = properties.securityRules
            | project id, name, resourceGroup, location, subscriptionId, rules
            | limit 500
            """
            
            # Get Azure Firewalls
            firewall_query = """
            Resources
            | where type == "microsoft.network/azurefirewalls"
            | extend firewallPolicy = properties.firewallPolicy,
                     threatIntelMode = properties.threatIntelMode,
                     sku = properties.sku
            | project id, name, resourceGroup, location, subscriptionId, firewallPolicy, threatIntelMode, sku
            | limit 100
            """
            
            # Get Public IPs
            pip_query = """
            Resources
            | where type == "microsoft.network/publicipaddresses"
            | extend ipAddress = properties.ipAddress,
                     associatedResource = properties.ipConfiguration.id
            | project id, name, resourceGroup, location, subscriptionId, ipAddress, associatedResource
            | limit 500
            """
            
            # Execute queries
            nsg_response = await client.post(
                "https://management.azure.com/providers/Microsoft.ResourceGraph/resources",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": nsg_query},
                params={"api-version": "2021-03-01"}
            )
            
            firewall_response = await client.post(
                "https://management.azure.com/providers/Microsoft.ResourceGraph/resources",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": firewall_query},
                params={"api-version": "2021-03-01"}
            )
            
            pip_response = await client.post(
                "https://management.azure.com/providers/Microsoft.ResourceGraph/resources",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": pip_query},
                params={"api-version": "2021-03-01"}
            )
            
            # Parse responses
            nsgs = nsg_response.json().get("data", []) if nsg_response.status_code == 200 else []
            firewalls = firewall_response.json().get("data", []) if firewall_response.status_code == 200 else []
            public_ips = pip_response.json().get("data", []) if pip_response.status_code == 200 else []
            
            # Analyze NSG security
            nsg_analysis = []
            security_risks = []
            
            for nsg in nsgs:
                rules = nsg.get("rules", [])
                nsg_info = {
                    "nsg_name": nsg.get("name", ""),
                    "resource_group": nsg.get("resourceGroup", ""),
                    "subscription_id": nsg.get("subscriptionId", ""),
                    "total_rules": len(rules),
                    "risky_rules": [],
                    "security_score": 100,
                    "recommendations": []
                }
                
                # Analyze rules for security risks
                for rule in rules:
                    rule_props = rule.get("properties", {})
                    source_address = rule_props.get("sourceAddressPrefix", "")
                    dest_port = rule_props.get("destinationPortRange", "")
                    protocol = rule_props.get("protocol", "")
                    access = rule_props.get("access", "")
                    direction = rule_props.get("direction", "")
                    
                    risk_level = "Low"
                    risk_reasons = []
                    
                    # Check for overly permissive rules
                    if source_address == "*" and access.lower() == "allow" and direction.lower() == "inbound":
                        risk_level = "High"
                        risk_reasons.append("Allows traffic from any source")
                    
                    if dest_port == "*" and access.lower() == "allow":
                        risk_level = "Medium" if risk_level == "Low" else "High"
                        risk_reasons.append("Allows traffic to any port")
                    
                    # Check for common risky ports
                    risky_ports = ["22", "3389", "1433", "3306", "5432", "27017"]
                    if any(port in dest_port for port in risky_ports) and source_address == "*":
                        risk_level = "High"
                        risk_reasons.append(f"Exposes sensitive port {dest_port} to internet")
                    
                    if risk_level != "Low":
                        nsg_info["risky_rules"].append({
                            "rule_name": rule.get("name", ""),
                            "risk_level": risk_level,
                            "risk_reasons": risk_reasons,
                            "source": source_address,
                            "destination_port": dest_port,
                            "protocol": protocol,
                            "access": access,
                            "direction": direction
                        })
                        
                        # Reduce security score
                        if risk_level == "High":
                            nsg_info["security_score"] -= 20
                        elif risk_level == "Medium":
                            nsg_info["security_score"] -= 10
                
                nsg_info["security_score"] = max(0, nsg_info["security_score"])
                
                # Generate recommendations
                if nsg_info["risky_rules"]:
                    nsg_info["recommendations"].append("Review and restrict overly permissive rules")
                if any(rule["risk_level"] == "High" for rule in nsg_info["risky_rules"]):
                    nsg_info["recommendations"].append("Immediately address high-risk rules exposing sensitive ports")
                
                nsg_analysis.append(nsg_info)
                
                # Collect high-risk NSGs
                if nsg_info["security_score"] < 70:
                    security_risks.append({
                        "resource_type": "NSG",
                        "resource_name": nsg_info["nsg_name"],
                        "security_score": nsg_info["security_score"],
                        "risk_count": len(nsg_info["risky_rules"])
                    })
            
            # Analyze firewalls
            firewall_analysis = []
            for firewall in firewalls:
                firewall_info = {
                    "firewall_name": firewall.get("name", ""),
                    "resource_group": firewall.get("resourceGroup", ""),
                    "subscription_id": firewall.get("subscriptionId", ""),
                    "threat_intel_mode": firewall.get("threatIntelMode", ""),
                    "has_policy": bool(firewall.get("firewallPolicy")),
                    "sku": firewall.get("sku", {}),
                    "security_score": 80,  # Base score
                    "recommendations": []
                }
                
                # Check threat intelligence mode
                if firewall_info["threat_intel_mode"].lower() != "alert":
                    firewall_info["recommendations"].append("Enable threat intelligence alerting")
                    firewall_info["security_score"] -= 10
                
                if not firewall_info["has_policy"]:
                    firewall_info["recommendations"].append("Configure firewall policy for centralized management")
                    firewall_info["security_score"] -= 15
                
                firewall_analysis.append(firewall_info)
            
            # Analyze public IP exposure
            public_ip_analysis = {
                "total_public_ips": len(public_ips),
                "associated_resources": len([pip for pip in public_ips if pip.get("associatedResource")]),
                "unassociated_ips": len([pip for pip in public_ips if not pip.get("associatedResource")]),
                "recommendations": []
            }
            
            if public_ip_analysis["unassociated_ips"] > 0:
                public_ip_analysis["recommendations"].append(f"Remove {public_ip_analysis['unassociated_ips']} unused public IP addresses")
            
            # Overall summary
            summary = {
                "network_security_overview": {
                    "total_nsgs": len(nsgs),
                    "nsgs_with_risks": len([nsg for nsg in nsg_analysis if nsg["security_score"] < 80]),
                    "total_firewalls": len(firewalls),
                    "total_public_ips": len(public_ips)
                },
                "security_risks": security_risks,
                "nsg_analysis": nsg_analysis,
                "firewall_analysis": firewall_analysis,
                "public_ip_analysis": public_ip_analysis,
                "top_recommendations": []
            }
            
            # Generate top recommendations
            all_recommendations = []
            for nsg in nsg_analysis:
                all_recommendations.extend(nsg["recommendations"])
            for fw in firewall_analysis:
                all_recommendations.extend(fw["recommendations"])
            all_recommendations.extend(public_ip_analysis["recommendations"])
            
            # Get unique recommendations with counts
            rec_counts = {}
            for rec in all_recommendations:
                rec_counts[rec] = rec_counts.get(rec, 0) + 1
            
            summary["top_recommendations"] = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return json.dumps(summary, indent=2)
            
    except Exception as e:
        return json.dumps({"error": "Failed to analyze network security", "details": str(e)})
    print("Starting Azure Billing MCP server...", file=sys.stderr)
    mcp.run()
