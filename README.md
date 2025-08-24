# Azure Billing MCP Server

A comprehensive Model Context Protocol (MCP) server that provides deep insights into your Azure environment. This server enables AI assistants to analyze Azure costs, resources, security, and performance through a unified interface.

## What is this for?

This MCP server allows AI assistants like Claude to:

- **Analyze Azure costs and billing** - Get detailed cost breakdowns, budget tracking, and optimization recommendations
- **Map your Azure architecture** - Discover resources, analyze dependencies, and visualize network topology
- **Assess security posture** - Review security alerts, compliance status, and configuration risks
- **Monitor performance** - Track resource utilization, identify bottlenecks, and optimize efficiency
- **Provide actionable insights** - Generate recommendations for cost savings, security improvements, and performance optimization

## Key Features

### Cost & Billing Analysis
- Multi-dimensional cost analysis with custom timeframes
- Budget management and spend tracking
- Usage details and cost attribution
- Azure Advisor cost recommendations

### Resource Architecture Discovery
- Comprehensive resource inventory across all Azure services
- Network topology mapping (VNets, subnets, NSGs, load balancers)
- Resource dependency analysis and relationship mapping
- GraphML export for architecture visualization

### Security & Compliance Monitoring
- Azure Security Center alerts and incident analysis
- Microsoft Defender for Cloud coverage assessment
- Network security configuration review
- Key Vault security analysis
- RBAC assignments and access management

### Performance & Optimization
- VM, storage, and database performance metrics
- Unused and underutilized resource identification
- Activity log analysis for usage patterns
- Comprehensive utilization reporting

## Installation

### Prerequisites
- Python 3.8 or higher
- Azure subscription with appropriate permissions

### Install Dependencies

```bash
pip install fastmcp httpx
```

Or install from the project directory:

```bash
pip install -e .
```

## Configuration

### 1. Create Azure Service Principal

You'll need an Azure service principal with the following permissions:

```bash
# Create service principal
az ad sp create-for-rbac --name "AzureBillingMCP" --role "Reader" --scopes /subscriptions/{SUBSCRIPTION_ID}

# Add required roles
az role assignment create --assignee {CLIENT_ID} --role "Cost Management Reader" --scope /subscriptions/{SUBSCRIPTION_ID}
az role assignment create --assignee {CLIENT_ID} --role "Security Reader" --scope /subscriptions/{SUBSCRIPTION_ID}
az role assignment create --assignee {CLIENT_ID} --role "Monitoring Reader" --scope /subscriptions/{SUBSCRIPTION_ID}
```
# This outputs your credentials. Set them as environment variables.

  ## Windows (Command Prompt):
  set AZURE_TENANT_ID=your_tenant_id
  set AZURE_CLIENT_ID=your_client_id
  set AZURE_CLIENT_SECRET=your_client_secret
  set AZURE_SUBSCRIPTION_ID=your_subscription_id

  ## Windows (PowerShell):
  $env:AZURE_TENANT_ID="your_tenant_id"
  $env:AZURE_CLIENT_ID="your_client_id"
  $env:AZURE_CLIENT_SECRET="your_client_secret"
  $env:AZURE_SUBSCRIPTION_ID="your_subscription_id"

  ## Linux/Mac:
  export AZURE_TENANT_ID="your_tenant_id"
  export AZURE_CLIENT_ID="your_client_id"
  export AZURE_CLIENT_SECRET="your_client_secret"
  export AZURE_SUBSCRIPTION_ID="your_subscription_id"

### 2. Set Environment Variables

Create a `.env` file or set these environment variables:

```bash
export AZURE_TENANT_ID="your_tenant_id"
export AZURE_CLIENT_ID="your_client_id"
export AZURE_CLIENT_SECRET="your_client_secret"
export AZURE_SUBSCRIPTION_ID="your_subscription_id"
```

### 3. Update Configuration

Edit the `server.py` file to use your credentials:

```python
AZURE_TENANT_ID = "your_tenant_id"
AZURE_CLIENT_ID = "your_client_id"
AZURE_CLIENT_SECRET = "your_client_secret"
AZURE_SUBSCRIPTION_ID = "your_subscription_id"
```

## Usage

### Start the MCP Server

```bash
python -m mcp_azure_server.server

### Using with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "azure-billing": {
      "command": "python",
      "args": ["-m", "mcp_azure_server.server"],
      "cwd": "/path/to/mcp_azure_server",
      "env": {
        "AZURE_TENANT_ID": "your_tenant_id",
        "AZURE_CLIENT_ID": "your_client_id",
        "AZURE_CLIENT_SECRET": "your_client_secret",
        "AZURE_SUBSCRIPTION_ID": "your_subscription_id"
      }
    }
  }
}
```

## Example Queries

Once connected, you can ask Claude questions like:

- "What are my top Azure costs this month?"
- "Show me all my virtual machines and their performance metrics"
- "Analyze my network security configuration"
- "What unused resources can I clean up to save money?"
- "Generate a GraphML diagram of my Azure architecture"
- "Review my Azure security alerts and provide remediation steps"

## Available Tools

The server provides 40+ tools organized in these categories:

- **Billing & Cost Management** (6 tools) - Cost analysis, budgets, usage details, recommendations
- **Resource Discovery** (8 tools) - Resource inventory, network topology, dependencies
- **Detailed Resource Analysis** (8 tools) - VMs, databases, storage, app services, Key Vaults
- **Performance Monitoring** (6 tools) - Metrics for VMs, storage, databases, activity logs
- **Security Analysis** (5 tools) - Security alerts, assessments, Defender status, RBAC
- **Advanced Analytics** (8 tools) - GraphML export, monitoring settings, resource locks

## Data Export

The server can export comprehensive data to JSON files for further analysis:

- `export/billing/` - Cost analysis, budgets, usage details
- `export/resources/` - Resource inventory, topology, dependencies
- `export/detailed/` - Detailed resource configurations
- `export/performance/` - Performance metrics and monitoring data
- `export/security/` - Security alerts, assessments, RBAC data
- `export/additional/` - Advanced analytics and specialized reports

## Security Considerations

- Use environment variables for credentials, never hardcode them
- Grant minimum required permissions to the service principal
- Regularly rotate client secrets
- Monitor service principal usage through Azure Activity Logs
- Store credentials securely using Azure Key Vault when possible

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your tenant ID, client ID, and secret are correct
2. **Permission Denied**: Ensure your service principal has the required roles assigned
3. **No Data Returned**: Check that resources exist in the specified subscription
4. **Timeout Errors**: Large environments may require multiple API calls; try filtering queries

### Required Azure Roles

- **Reader** - Basic resource access
- **Cost Management Reader** - Billing and cost data
- **Security Reader** - Security Center data
- **Monitoring Reader** - Performance metrics
- **Resource Graph Reader** - Advanced resource queries

## Version

0.0.1

## License

MIT License - see LICENSE file for details.
