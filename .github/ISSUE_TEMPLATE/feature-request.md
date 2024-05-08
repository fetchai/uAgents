name: Feature request
description: Suggest a new feature for uAgents
title: "[Feature request]: <title>"
labels: ["enhancement", "unconfirmed"]
body:
  - type: markdown
    attributes:
      value: |
        Thank you for suggesting a new feature for uAgents. Please provide the following details to ensure we have all the details to get things started.
  - type: checkboxes
    id: prerequisites
    attributes:
      label: Prerequisites
      description: Please confirm before submitting any new feature request.
      options:
        - label: I checked the [documentation](https://fetch.ai/docs) and made sure this feature does not already exist.
          required: true
        - label: I checked the [existing issues](https://github.com/fetchai/uAgents/issues) to make sure this feature has not already been requested.
          required: true
  - type: textarea
    id: problem
    attributes:
      label: Problem identification
      description: |
        Clearly describe the problem or limitation you are facing that this feature would address.
    validations:
      required: false
  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: |
        Describe the feature or solution you would like to see implemented.
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: |
        Have you considered any alternative approaches or solutions? If so, please describe them here.
    validations:
      required: false
  - type: textarea
    id: info
    attributes:
      label: Additional Information
      description: |
        Add any other context, screenshots, or information that could be helpful for understanding your feature request.
    validations:
      required: false
