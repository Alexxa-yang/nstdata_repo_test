# Security

Never post API keys, passwords or private page content in public issues. Revoke exposed
credentials in the provider dashboard. Report vulnerabilities through GitHub private
vulnerability reporting if it is enabled. Otherwise, contact the maintainer privately
through an available profile contact method; do not publish exploit details in an issue.

This project uses environment variables or hidden local input for API keys. It does
not log SDK response bodies. Exported content can still contain sensitive information:
restrict access, review before sharing and remove it when no longer needed.

This example is intended for owned or explicitly permitted public targets.
