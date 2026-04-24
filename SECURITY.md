# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (main) | ✅ |
| older branches | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability in RAGenix, **please do not open a public GitHub issue**.

Instead, report it privately:

1. **Email**: Send details to the repository maintainer via the contact listed in the GitHub profile, or open a [GitHub Security Advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability).
2. **Include**: A description of the vulnerability, steps to reproduce, potential impact, and any suggested fix.
3. **Response time**: We aim to acknowledge reports within **72 hours** and provide a fix or mitigation within **14 days** for critical issues.

## Credential Security

RAGenix uses environment variables for all credentials. Please follow these practices:

- **Never hardcode** API keys, connection strings, or file paths in source code.
- **Use `.env` files** locally (already in `.gitignore`) and platform secret managers in production.
- **Rotate keys immediately** if you accidentally commit them, then remove the history with `git filter-repo` or contact your provider.
- **Scan before pushing**: Use [truffleHog](https://github.com/trufflesecurity/trufflehog) or [gitleaks](https://github.com/gitleaks/gitleaks) in your CI pipeline.

## Dependency Security

- Pin dependencies in `requirements.txt` to known-good versions.
- Run `pip audit` or [Safety](https://pypi.org/project/safety/) regularly to check for known CVEs.
- Update dependencies promptly when security patches are released.

## File Upload Security

RAGenix accepts user-uploaded PDFs. The following controls are in place:

- File type is validated to `application/pdf` only.
- Maximum file size is enforced (20 MB per file, up to 3 files).
- Uploaded content is processed in-memory; no files are written to disk by the application.
- PDFs are not executed; only text is extracted via PyPDF2.

## Data Privacy

- No user data, uploaded files, or conversation history is stored persistently by the application.
- All vector store data is held in-memory and destroyed when the session ends.
- Telemetry in `.chainlit/config.toml` can be disabled by setting `enable_telemetry = false`.
