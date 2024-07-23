# Security Policy

Security is very important for Fetch.ai and its community. This document outlines security procedures and general policies for this repository.

## How to Report

Please follow the steps listed below to report your bug:

- In an email, describe the issue clearly with reference to the underlying source code and indicate whether the bug is **Critical** or **Non-critical**.
- Attach all relevant information that is required to reproduce the bug in a test environment.
- Include the relevant version information associated with the faulty software of the components along with any other relevant system information such as OS versions.
- Include suggested solutions and/or mitigations (if known).
- Send this email to [security@fetch.ai](mailto:security@fetch.ai) and start the subject with your classification **Critical** or **Non-critical** followed by a short title of the bug.

The Fetch team will review your information and your classification of the bug.

For non-critical bugs, the Fetch team will create an issue or a pull request allowing you to follow the progress on the bug fix.

For critical bugs that can result in loss of funds, it is important that the Fetch team has an opportunity to deploy a patched version before the exploit is acknowledged publicly. Hence, critical bugs and their fixes will be shared after the code is patched to prevent the targeting of such exploits.

## Disclosure Policy

When the security team receives a security bug report, they will assign it to a primary handler. This person will coordinate the fix and release process, involving the following steps:

- Confirm the problem and determine the affected versions.
- Audit code to find any potential similar problems.
- Prepare fixes for all releases still under maintenance. These fixes will be released as fast as possible to PyPI.

## Comments on this Policy

If you have suggestions on how this process could be improved please submit a pull request.

## Public Discussions

Please restrain from publicly discussing a potential security vulnerability. 🙊

It's better to discuss privately and try to find a solution first, to limit the potential impact as much as possible.

---

Thanks for your help!
