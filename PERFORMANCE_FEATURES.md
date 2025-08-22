# Azure MCP Server - Performance & Optimization Features

## Overview
The Azure MCP server has been enhanced with comprehensive performance monitoring and resource optimization capabilities to help identify unused resources and performance issues.

## New Tools Added

### 1. Resource Optimization Tools

#### `get_unused_resources`
- **Purpose**: Identify potentially unused or under-utilized resources
- **Capabilities**:
  - Stopped/deallocated VMs older than 30 days
  - Unattached managed disks
  - Unused network interfaces
  - Empty network security groups
  - Unassociated public IP addresses

#### `get_resource_utilization_summary`
- **Purpose**: Comprehensive utilization analysis and recommendations
- **Features**:
  - Aggregates data from all optimization tools
  - Provides actionable cleanup recommendations
  - Estimates potential cost savings
  - Prioritizes recommendations by impact

### 2. Performance Monitoring Tools

#### `get_vm_performance_metrics`
- **Purpose**: Monitor VM performance metrics
- **Metrics Collected**:
  - CPU utilization percentage
  - Memory usage percentage
  - Disk read/write operations per second
  - Network bytes in/out
  - Available memory bytes

#### `get_storage_performance_metrics`
- **Purpose**: Analyze storage account performance
- **Metrics Monitored**:
  - Transaction count
  - Used capacity
  - Ingress/egress data
  - Success rate percentage
  - Availability metrics

#### `get_database_performance_metrics`
- **Purpose**: Monitor database performance
- **Database Types Supported**:
  - Azure SQL Database (DTU/vCore)
  - Azure Database for MySQL
  - Azure Database for PostgreSQL
- **Metrics Tracked**:
  - DTU consumption percentage
  - CPU utilization
  - Memory percentage
  - Connection count

### 3. Analysis Tools

#### `get_activity_log_analysis`
- **Purpose**: Analyze resource usage patterns
- **Features**:
  - Last 30 days of activity
  - Resource access patterns
  - Administrative operations
  - Usage frequency analysis

#### `get_azure_advisor_detailed`
- **Purpose**: Enhanced Azure Advisor recommendations
- **Categories**:
  - Cost optimization
  - Performance improvements
  - Security recommendations
  - Reliability enhancements

## New Resources Available

- `https://azure-optimization/unused-resources`
- `https://azure-optimization/utilization-summary`
- `https://azure-performance/vm-metrics`
- `https://azure-performance/storage-metrics`
- `https://azure-optimization/advisor-recommendations`

## New Prompts for Guided Analysis

### `performance_analysis`
- Analyzes resource performance across VMs, storage, and databases
- Can focus on specific resource types
- Identifies bottlenecks and optimization opportunities

### `unused_resources_cleanup`
- Guides identification of resources for cleanup
- Considers business requirements and data retention
- Provides specific deletion recommendations

### `utilization_summary`
- Comprehensive utilization analysis
- Actionable insights for efficiency improvements
- Cost and performance optimization focus

### `advisor_insights`
- Azure Advisor recommendation analysis
- Can filter by category (Cost, Performance, Security, Reliability)
- Provides prioritized action plans

## Usage Examples

### Identify Unused Resources
```python
# Use the MCP tool
result = await get_unused_resources()
# This will return JSON with categorized unused resources
```

### Monitor VM Performance
```python
# Get VM performance metrics
metrics = await get_vm_performance_metrics()
# Returns CPU, memory, disk, and network metrics for all VMs
```

### Get Comprehensive Optimization Summary
```python
# Get full utilization analysis
summary = await get_resource_utilization_summary()
# Returns aggregated recommendations and cost savings opportunities
```

## API Requirements

### Azure Monitor Metrics API
- Endpoint: `https://management.azure.com/subscriptions/{subscription}/resourceGroups/{resourceGroup}/providers/{resourceProvider}/providers/microsoft.insights/metrics`
- Required permissions: `Monitoring Reader` role
- API Version: `2018-01-01`

### Azure Activity Log API
- Endpoint: `https://management.azure.com/subscriptions/{subscription}/providers/microsoft.insights/eventtypes/management/values`
- Required permissions: `Reader` role
- API Version: `2015-04-01`

## Performance Thresholds

### High Utilization Alerts
- **CPU**: >80% average over 7 days
- **Memory**: >85% average over 7 days
- **Disk I/O**: >90% utilization
- **DTU**: >80% for SQL databases

### Low Utilization Thresholds
- **CPU**: <5% average over 30 days
- **Storage**: <10% capacity used
- **Network**: <1% of provisioned bandwidth

## Error Handling

All new tools include comprehensive error handling:
- JSON parsing safety with `safe_json_parse()`
- Graceful fallback when metrics are unavailable
- Detailed error reporting in JSON format
- Resource existence validation

## Integration Notes

- All existing functionality preserved
- New tools follow same authentication pattern
- Compatible with existing resource and prompt structure
- Maintains async/await patterns throughout
- Uses httpx for HTTP requests with proper error handling

## Testing

The server has been validated for:
- ✅ Syntax compilation
- ✅ Module import
- ✅ Tool registration
- ✅ Resource availability
- ✅ Prompt functionality

## Next Steps

1. Test with actual Azure environment
2. Validate Azure Monitor API permissions
3. Fine-tune performance thresholds based on usage
4. Add additional metrics as needed
5. Consider adding alerting capabilities
