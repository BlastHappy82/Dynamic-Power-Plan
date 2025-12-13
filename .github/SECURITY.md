# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Dynamic Power Plan seriously. If you discover a security vulnerability, please follow the steps below:

### How to Report

1. **Do NOT** open a public issue for security vulnerabilities
2. Contact the maintainers directly via GitHub private message
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its severity
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 7 days

### Security Considerations

This application:
- Runs with user-level permissions by default
- Modifies Windows power plans (requires appropriate Windows permissions)
- Copies files to L-Connect settings directory (requires write access)
- Can be configured to start with Windows (modifies registry)

### Best Practices for Users

1. Download only from official sources (GitHub releases)
2. Verify file integrity when possible
3. Review configuration before running
4. Run with minimum necessary permissions
5. Keep the application updated

## Scope

This security policy applies to:
- The Dynamic Power Plan application source code
- Official releases and builds
- Configuration file handling

Out of scope:
- Third-party dependencies (report to their maintainers)
- User system configuration issues
- L-Connect software issues (report to Lian Li)

## Acknowledgments

We appreciate security researchers who help keep this project secure. Contributors who report valid security issues will be acknowledged (with permission) in our release notes.
