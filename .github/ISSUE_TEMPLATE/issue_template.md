name: Bug Report
description: Report a bug for uAgents
title: "<title>"
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report a bug in uAgents! We appreciate your contribution to improving the library.
  - type: checkboxes
    id: prerequisites
    attributes:
      label: Prerequisites
      description: Please confirm before submitting any new bug report:
      options:
          required: true
        - label: I checked the [existing issues](https://github.com/fetchai/uAgents/issues) and made sure there are no similar bug report. 
          required: true
  - type: dropdown
    id: category
    attributes:
      label: Category
      description: Select the category that best describes the bug.
      options:
        - label: Bug (unexpected behavior)
        - label: Documentation Issue (error or unclear information in docs)
        - label: Other
      validations:
        required: true
  - type: textarea
    id: description
    attributes:
      label: Describe the Issue
      description: Please provide a clear and concise description of the bug you encountered.
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
      label: Steps to Reproduce (Optional)
      description: If possible, provide detailed steps that consistently reproduce the bug. This will help us pinpoint the problem and fix it as soon as possible.
      validations:
        required: false
  - type: textarea
    id: version
    attributes:
      label: uAgents Version
      description: Which version of uAgents were you using? Please enter the version number here.
      validations:
        required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment Details (Optional)
      description: Provide any relevant information about your environment, such as operating system, Python version, and any other libraries used.
      render: markdown
      validations:
        required: false
  - type: textarea
    id: logs
    attributes:
      label: Failure Logs (Optional)
      description: Include any relevant log snippets or files here. You can paste directly or drag and drop files into this area.
    render: shell
    validations:
        required: false
  - type: textarea
    id: additional_info
    attributes:
      label: Additional Information (Optional)
      description: Include any screenshots, code snippets, or other relevant details that might help us understand the bug.
      render: markdown
      validations:
        required: false
