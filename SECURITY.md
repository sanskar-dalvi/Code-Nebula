# Security Policy

## Overview

The C# → Neo4j Code Graph Extractor project takes security seriously. This document outlines our security policy, supported versions, and procedures for reporting security vulnerabilities.

Given that this project processes potentially sensitive source code and uses local LLM processing, security is paramount to maintaining trust and protecting user data.

## Security Features

This project implements several security-by-design features:

### 🔒 Local Processing
- **No External Data Transfer**: All code analysis happens locally
- **Air-Gapped Operation**: Can operate without internet connectivity
- **Data Sovereignty**: Complete control over sensitive source code

### 🛡️ Access Controls
- **Environment Variable Security**: Sensitive credentials stored in .env files
- **Database Authentication**: Neo4j connection requires authentication
- **API Authentication**: FastAPI endpoints can be secured (configurable)

### 🔐 Data Protection
- **Input Validation**: All user inputs are validated and sanitized
- **SQL Injection Prevention**: Parameterized queries for database operations
- **Path Traversal Protection**: File operations are restricted to designated directories

### 🏗️ Secure Architecture
- **Principle of Least Privilege**: Components operate with minimal necessary permissions
- **Separation of Concerns**: Clear boundaries between parsing, enrichment, and storage
- **Error Handling**: Secure error messages that don't leak sensitive information

## Threat Model

### Assets Protected
1. **Source Code**: C# files being analyzed
2. **Parsed Data**: AST and enriched metadata
3. **Graph Database**: Neo4j relationship data
4. **Credentials**: Database passwords and API keys
5. **LLM Responses**: Analysis results from local models

### Potential Threats
1. **Code Injection**: Malicious C# code affecting the parser
2. **Path Traversal**: Unauthorized file system access
3. **Data Exfiltration**: Sensitive code leaking through logs or errors
4. **Credential Exposure**: Database passwords or API keys in logs
5. **LLM Prompt Injection**: Malicious prompts affecting model responses
6. **Denial of Service**: Resource exhaustion through large files

### Mitigations
- Input validation and sanitization
- Secure file handling with restricted paths
- Credential management through environment variables
- Rate limiting and resource management
- Prompt sanitization and validation
- Error handling that doesn't expose sensitive data

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

### 🚨 Critical Vulnerabilities
For critical vulnerabilities that could lead to:
- Remote code execution
- Data exfiltration
- Credential exposure
- Privilege escalation

**Contact immediately**:
1. **Create a private GitHub Security Advisory**
2. **Email**: sanskardineshdalvi@gmail.com
3. **Include**: Detailed description, reproduction steps, and potential impact

### ⚠️ Non-Critical Vulnerabilities
For less critical issues like:
- Information disclosure
- Cross-site scripting (XSS) in API responses
- Denial of service (DoS)
- Configuration issues

**Report via**:
1. **GitHub Issues** with the label "security"
2. **Include**: Clear description and reproduction steps

### Response Process

1. **Acknowledgment**: We'll confirm receipt of your report
2. **Validation**: We'll reproduce and validate the vulnerability
3. **Assessment**: We'll assess the severity and impact
4. **Fix Development**: We'll develop and test a fix
5. **Release**: We'll release a security update
6. **Disclosure**: We'll coordinate public disclosure

## Security Considerations by Component

### ANTLR Parser Security
- **Input Validation**: Validates C# syntax before processing
- **Memory Limits**: Prevents DoS through large files
- **Error Handling**: Secure error messages without exposing file paths

### LLM Integration Security
- **Local Processing**: No data sent to external services
- **Prompt Sanitization**: Prevents prompt injection attacks
- **Response Validation**: Validates LLM responses before processing
- **Resource Limits**: Prevents resource exhaustion

### Neo4j Integration Security
- **Parameterized Queries**: Prevents injection attacks
- **Connection Security**: Encrypted connections when configured
- **Access Control**: Role-based database permissions
- **Data Validation**: Validates data before database insertion

### API Security
- **Input Validation**: Validates all API inputs
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Error Handling**: Secure error responses
- **Authentication**: Configurable authentication mechanisms

## Security Updates and Notifications

### Automatic Updates
We recommend enabling automatic security updates:

```bash
# GitHub Watch settings
# Enable: "Custom" -> "Security alerts"

# Set up dependabot alerts
# .github/dependabot.yml is configured for automatic dependency updates
```

### Security Notifications
Subscribe to security announcements:

1. **GitHub Releases**: Watch the repository for releases
2. **Security Advisories**: Enable GitHub security advisory notifications
3. **RSS Feed**: Subscribe to the project's release RSS feed

### Security Checklist for Releases

Before each release, we verify:

- [ ] All dependencies are up to date
- [ ] No known vulnerabilities in dependencies
- [ ] Security tests pass
- [ ] Input validation is comprehensive
- [ ] Error handling doesn't leak sensitive information
- [ ] Documentation reflects security best practices
- [ ] Example configurations are secure

## Compliance and Standards

This project aims to comply with:

### Industry Standards
- **OWASP Top 10**: Web application security risks
- **NIST Cybersecurity Framework**: Risk management
- **ISO 27001**: Information security management

### Regulatory Compliance
- **GDPR**: Data protection (when processing EU data)
- **SOC 2**: Security controls for service organizations
- **HIPAA**: Healthcare data protection (when applicable)

### Code Security Standards
- **SAST**: Static Application Security Testing
- **DAST**: Dynamic Application Security Testing
- **Dependency Scanning**: Known vulnerability detection
- **Secret Scanning**: Credential detection in code

## Security Testing

### Automated Security Testing

```bash
# Run security tests
pytest tests/security/ -v

# Dependency vulnerability scanning
pip-audit

# Static analysis for security issues
bandit -r pipeline/ api/

# Check for secrets in code
git-secrets --scan
```

### Manual Security Testing

1. **Input Validation Testing**
   - Test with malicious C# code samples
   - Verify path traversal protection
   - Test API input validation

2. **Authentication Testing**
   - Test database connection security
   - Verify API authentication mechanisms
   - Test credential handling

3. **Data Protection Testing**
   - Verify sensitive data is not logged
   - Test error message security
   - Validate data encryption in transit

## Contact Information

### Security Team
- **Primary Contact**: Create GitHub Security Advisory
- **Emergency Contact**: Use GitHub Issues with "security" label
- **PGP Key**: Available upon request for sensitive communications

### Response Commitment
We commit to:
- Acknowledging all security reports within 48 hours
- Providing regular updates on investigation progress
- Releasing security fixes as quickly as possible
- Coordinating responsible disclosure

## Legal Safe Harbor

We support security research and provide legal safe harbor for:

1. **Good Faith Research**: Conducted to identify and report vulnerabilities
2. **Responsible Disclosure**: Following our reporting procedures
3. **No Malicious Intent**: Not intended to harm users or systems
4. **Scope Compliance**: Testing only within the project's scope

**Protected Activities**:
- Security testing of the open-source code
- Reporting vulnerabilities through proper channels
- Providing proof-of-concept demonstrations
- Participating in coordinated disclosure

**Prohibited Activities**:
- Testing against production systems without permission
- Accessing or modifying user data
- Performing denial of service attacks
- Social engineering or phishing attempts

## Attribution

Security researchers who help improve our security will be recognized:

### Hall of Fame
Contributors who responsibly disclose vulnerabilities:

1. Sanskar Dalvi (Owner)
2. Kshitij Landge
3. Utkarsha Mahale
4. Ganesh Muthal
5. Rushikesh Chaudhari

### Recognition Policy
- **Public acknowledgment** in release notes and README
- **CVE credit** for significant vulnerabilities
- **Special thanks** in security documentation
- **Optional recognition** (researchers may remain anonymous)

---


For questions about this security policy, please create a GitHub issue with the "security-policy" label.
