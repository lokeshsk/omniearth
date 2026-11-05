# Security Policy

OmniEarth takes the security, integrity, and privacy of its users, software artifacts, and geospatial data workflows seriously. This document outlines our security policies, supported versions, and the process for responsibly reporting potential vulnerabilities.

---

## Supported Versions

Only the latest active minor release receives proactive security updates and vulnerability patches. Users are encouraged to stay up to date with the latest release.

| Version | Supported          | Security Maintenance Status      |
| :------ | :----------------- | :------------------------------- |
| 1.3.x   | :white_check_mark: | Currently Supported (Active)     |
| 1.2.x   | :x:                | Deprecated (Upgrade to >= 1.3.0) |
| < 1.2.0 | :x:                | End of Life                      |

---

## Reporting a Vulnerability

If you discover a security vulnerability or suspect a potential security weakness in OmniEarth, please report it responsibly. **Do not create public GitHub issues or public discussions for security concerns.**

### Preferred Method: GitHub Private Vulnerability Reporting
OmniEarth uses GitHub's built-in Private Vulnerability Reporting system:
1. Navigate to the [OmniEarth Security Advisories](https://github.com/lokeshsk/omniearth/security/advisories) tab.
2. Click **"Report a vulnerability"**.
3. Fill in the advisory form with a detailed description, reproduction steps, proof of concept (PoC), and impact assessment.

### Alternative Method: Direct Security Contact
If you cannot use GitHub's advisory tool, you may reach out directly via encrypted or direct email:
- **Primary Security Contact**: Lokesh Kumar
- **Email**: [lokesh.skshukla@gmail.com](mailto:lokesh.skshukla@gmail.com)
- **Subject Line**: `[SECURITY VULNERABILITY] OmniEarth - <Brief Summary>`

### Response SLA & Disclosure Timeline
We are committed to rapid response and coordinated disclosure:
- **Initial Acknowledgement**: Within **24 to 48 hours** of report receipt.
- **Triage & Validation**: Within **72 hours** to confirm severity (CVSS score) and affected components.
- **Remediation & Patch Release**: Security fixes are prioritized and released as a hotfix or minor update within **7 to 14 days** of confirmation.
- **Coordinated Public Disclosure**: A CVE will be requested and a GitHub Security Advisory published alongside the release notes once the patch is live.

---

## Security Architecture & Threat Model

OmniEarth is designed with privacy-first and defense-in-depth principles:

### 1. Zero Telemetry & Local Execution
- OmniEarth contains **zero telemetry**, tracking pixels, analytics, or background call-homes.
- All requests are initiated directly from the user's client machine to official, public, or authenticated Earth Observation endpoints (Copernicus CDSE, NASA Earthdata, DLR EnMAP, USGS, Open-Meteo, SoilGrids).

### 2. Credential Security
- Credentials (e.g., `NASA_EARTHDATA_TOKEN`, `COPERNICUS_CLIENT_ID`, `COPERNICUS_CLIENT_SECRET`) are read strictly from local environment variables or local `.env` files via `python-dotenv` / `dotenv`.
- Credentials are never logged, echoed to standard output, cached on external servers, or transmitted to any third party.
- Bearer tokens are dispatched strictly to authenticated HTTPS endpoints matching verified domain whitelists.

### 3. File System & Path Traversal Protections
- Asset downloads are validated against safe local directory targets. File names derived from remote STAC asset URLs are sanitized to prevent directory traversal (`../`) attacks.
- Range requests and chunked streaming downloads verify total length and enforce boundary integrity.

### 4. Supply Chain Integrity & Provenance
- **PyPI Provenance (PEP 740)**: Built using GitHub Actions with OpenID Connect (OIDC) Trusted Publishing, accompanied by cryptographic build attestations signed via Sigstore.
- **npm Provenance (SLSA)**: Published with `--provenance`, generating an in-toto SLSA attestation on npm and Rekor public transparency log.
- **Automated Dependency Audits**: Continuous scanning via GitHub Advanced Security CodeQL and Dependabot to guard against vulnerable or compromised upstream dependencies.

