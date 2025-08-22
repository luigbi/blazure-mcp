# Azure MCP Server - Security Features

## Overview
The Azure MCP server has been enhanced with comprehensive security monitoring and threat detection capabilities to identify security issues, threats, and incidents across your Azure environment.

## New Security Tools Added

### 1. Security Center & Alerts

#### `get_security_center_alerts`
- **Purpose**: Retrieve Azure Security Center alerts and security incidents
- **Data Sources**: Microsoft.Security/alerts API
- **Capabilities**:
  - Active security alerts across all subscriptions
  - Alert categorization by severity (Critical, High, Medium, Low)
  - Alert status tracking (Active, Dismissed, Resolved)
  - Recent alerts (last 7 days)
  - Compromised entity identification
  - Remediation steps and guidance
  - Extended alert properties and context

#### `get_security_assessments`
- **Purpose**: Get Azure Security Center security assessments and recommendations
- **Data Sources**: Microsoft.Security/assessments API
- **Features**:
  - Security assessment results across all resources
  - Assessment categorization by severity and status
  - Failed and critical security findings
  - Resource-specific security recommendations
  - Assessment metadata and descriptions
  - Compliance status indicators

### 2. Microsoft Defender for Cloud

#### `get_defender_for_cloud_status`
- **Purpose**: Analyze Microsoft Defender for Cloud enablement and coverage
- **Data Sources**: Microsoft.Security/pricings API
- **Coverage Analysis**:
  - Service enablement status per subscription
  - Resource type coverage (VMs, SQL, Storage, Kubernetes, etc.)
  - Free trial status and remaining days
  - Defender plan extensions and sub-plans
  - Coverage gaps identification
  - Cost optimization recommendations

### 3. Key Vault Security

#### `get_key_vault_security_status`
- **Purpose**: Audit Azure Key Vault security configurations
- **Data Sources**: Azure Resource Graph + Key Vault properties
- **Security Checks**:
  - Soft delete enablement status
  - Purge protection configuration
  - Public network access restrictions
  - Soft delete retention period validation
  - Network ACLs and private endpoint usage
  - Security scoring (0-100) per vault
  - Configuration compliance recommendations

### 4. Network Security

#### `get_network_security_analysis`
- **Purpose**: Comprehensive network security configuration analysis
- **Data Sources**: Azure Resource Graph (NSGs, Firewalls, Public IPs)
- **Security Analysis**:
  - **Network Security Groups (NSGs)**:
    - Overly permissive rules detection
    - High-risk port exposure (22, 3389, 1433, etc.)
    - Source address wildcard usage
    - Inbound rule security scoring
  - **Azure Firewalls**:
    - Threat intelligence mode configuration
    - Firewall policy implementation
    - SKU and configuration analysis
  - **Public IP Exposure**:
    - Unassociated public IP identification
    - Resource exposure analysis
    - Public endpoint security recommendations

## Security Risk Scoring System

### Key Vault Security Scores
- **100 points**: Fully secure configuration
- **-25 points**: Soft delete not enabled
- **-20 points**: Purge protection disabled
- **-20 points**: Public network access enabled
- **-10 points**: Short retention period (<30 days)

### NSG Security Scores
- **100 points**: Secure rule configuration
- **-20 points per high-risk rule**: Internet exposure of sensitive ports
- **-10 points per medium-risk rule**: Overly permissive configurations

### Threat Categories Detected

1. **High-Risk Network Exposures**:
   - SSH (port 22) exposed to internet
   - RDP (port 3389) exposed to internet
   - Database ports (1433, 3306, 5432) exposed publicly
   - Any port with source address "*"

2. **Key Vault Misconfigurations**:
   - Missing data protection (soft delete)
   - Insufficient retention policies
   - Unrestricted network access
   - Missing purge protection

3. **Defender Coverage Gaps**:
   - Critical services without Defender protection
   - Inconsistent coverage across subscriptions
   - Missing threat intelligence integration

## New Resources Available

- `https://azure-security/alerts` - Security Center alerts and incidents
- `https://azure-security/assessments` - Security assessments and recommendations
- `https://azure-security/defender-status` - Defender for Cloud coverage analysis
- `https://azure-security/keyvault-security` - Key Vault security configuration audit
- `https://azure-security/network-security` - Network security analysis and recommendations

## New Security Prompts

### `security_assessment`
- Comprehensive security posture analysis
- Multi-dimensional security review
- Prioritized remediation roadmap

### `security_alerts_analysis`
- Active threat and incident analysis
- Critical alert prioritization
- Detailed remediation guidance

### `defender_coverage_analysis`
- Protection gap identification
- Service enablement recommendations
- Cost-benefit security analysis

### `network_security_review`
- Network configuration audit
- Firewall and NSG optimization
- Public exposure risk assessment

### `keyvault_security_audit`
- Secret management security review
- Configuration compliance check
- Data protection validation

### `security_compliance_review`
- Regulatory compliance assessment
- Control gap analysis
- Compliance roadmap development

## Usage Examples

### Get Security Alerts
```python
# Retrieve active security alerts
alerts = await get_security_center_alerts()
# Returns categorized alerts with severity, status, and remediation steps
```

### Analyze Defender Coverage
```python
# Check Defender for Cloud protection status
coverage = await get_defender_for_cloud_status()
# Returns enablement status, gaps, and recommendations
```

### Audit Key Vault Security
```python
# Review Key Vault security configurations
security_status = await get_key_vault_security_status()
# Returns security scores, issues, and recommendations
```

### Network Security Analysis
```python
# Analyze network security configurations
network_security = await get_network_security_analysis()
# Returns NSG analysis, firewall status, and risk assessment
```

## Security APIs and Permissions

### Required API Endpoints
- `Microsoft.Security/alerts` (Security Center Alerts)
- `Microsoft.Security/assessments` (Security Assessments)
- `Microsoft.Security/pricings` (Defender for Cloud Status)
- `Microsoft.Security/regulatoryComplianceStandards` (Compliance)
- `Microsoft.ResourceGraph/resources` (Resource Discovery)

### Required Permissions
- **Security Reader**: Access to Security Center data
- **Reader**: Access to resource configurations
- **Resource Graph Reader**: Query across subscriptions

### API Versions
- Security APIs: `2020-01-01` to `2022-03-01`
- Resource Graph: `2021-03-01`
- Subscription Management: `2020-01-01`

## Security Monitoring Capabilities

### Real-time Threat Detection
- Active security alerts monitoring
- Critical incident identification
- Automated risk assessment
- Threat severity classification

### Configuration Compliance
- Azure Security Benchmark compliance
- Industry standard alignment (ISO 27001, SOC 2, PCI DSS)
- Custom security policy validation
- Drift detection and reporting

### Vulnerability Management
- Security assessment tracking
- Remediation progress monitoring
- Risk prioritization
- Vulnerability lifecycle management

## Integration with Existing Tools

- **Performance Monitoring**: Cross-reference security issues with performance impact
- **Cost Optimization**: Balance security investments with cost considerations
- **Resource Management**: Integrate security findings with resource optimization
- **Compliance Reporting**: Automated security compliance documentation

## Error Handling & Reliability

- Graceful API failure handling
- Partial data collection on permission errors
- Detailed error reporting with context
- Fallback mechanisms for incomplete data

## Best Practices Recommendations

1. **Regular Security Assessments**: Run weekly security reviews
2. **Critical Alert Prioritization**: Address high/critical alerts within 24 hours
3. **Defender Coverage**: Enable for all production workloads
4. **Network Segmentation**: Implement least-privilege network access
5. **Key Vault Hardening**: Enable all security features for production vaults

## Future Enhancements

- Azure Sentinel integration for SIEM data
- Microsoft Defender ATP integration
- Custom security rule development
- Automated remediation workflows
- Security metrics dashboard
- Compliance reporting automation
