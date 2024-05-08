name: Issue Report
description: Report an issue for uAgents
title: "[ISSUE]: <title>"
labels: ["issue", "unconfirmed"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report an issue in uAgents!
  - type: dropdown
    id: category
    attributes:
      label: Category
      description: Select the category that best describes your issue.
      options:
        - label: Bug (unexpected behavior)
        - label: Feature Request (suggestion for new functionality)
        - label: Documentation Issue (error or unclear information in docs)
        - label: Other (unclear issue type)
      validations:
        required: true
  - type: textarea
    id: description
    attributes:
      label: Describe the issue
      description: Please provide a clear and concise description of the issue you encountered.
      placeholder: What went wrong?
      validations:
        required: true
  - type: textarea
    id: expected_behavior
    attributes:
      label: Expected Behavior
      description: Explain what you expected to happen in this situation.
      validations:
        required: false
  - type: textarea
    id: steps_to_reproduce
    attributes:
      label: Steps to reproduce
      description: If possible, provide detailed steps that consistently reproduce the issue.
      validations:
        required: false
  - type: dropdown
    id: version
    attributes:
      label: uAgents version
      description: Which version of uagents were you using?
      options:
        - v0.11.1
        - v0.11.0
        - v0.10.0
        # Add other versions as needed
      validations:
        required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment details (Optional)
      description: Provide any relevant information about your environment, such as operating system and Python version.
      validations:
        required: false
  - type: textarea
    id: logs
    attributes:
      label: Failure logs
      description: Include any relevant log snippets or files here
    validations:
      required: false
  - type: textarea
    id: additional_info
    attributes:
      label: Additional information (Optional)
      description: Include any screenshots, logs, or code snippets that might help identify the issue.
      validations:
        required: false
  - type: checkboxes
    id: prerequisites
    attributes:
      label: General information
      description: Please confirm the following before submitting your issue report.
      options:
        - label: I have included a clear description of the issue.
          required: true
        - label: I have read the [documentation](https://fetch.ai/docs) and found no answer to the problem.
          required: true
        - label: I have checked the [existing issues](https://github.com/fetchai/uAgents/issues) list to make sure my problem has not already been reported.
          required: true
