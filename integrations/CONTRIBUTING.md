# Contributing

Contributions to integrations are welcome 😊 the integrations repo is the place where you can share how you've integrated uAgents with other technology.

## A few simple rules

- Search the repo for the integration you're submitting, just in case.

- run [ruff](https://github.com/astral-sh/ruff) on your code before submitting. (see `DEVELOPING.md`)

- Include a `project.json` file, example of:

```json
{
  "title": "Bert Base Uncased",
  "description": "BERT base model (uncased) Pretrained model on English language using a masked language modeling (MLM) objective.",
  "categories": ["Text Classification", "Hugging Face", "Text Generation"],
  "deltav": false
}
```

Set `deltav` to true if your agent is built using agentverse and is accessible by DeltaV.

## Commits and PRs

This project uses Conventional Commits to generate release notes and to determine versioning.
When opening a PR please adhere to the following naming scheme where the type would be chosen based on the PRs goal and the title its description:

```
<type>(integration): <title>
```

### types

- **chore**: Commits that don't directly add features, fix bugs, or refactor code, but rather maintain the project or its surrounding processes.
- **ci**: Changes to our CI configuration files and scripts
- **docs**: Changes to the documentation
- **feat**: A new feature
- **fix**: A bug fix
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests or correcting existing tests
- **revert**: Reverts a previous commit that introduced an issue or unintended change. This essentially undoes a previous commit.
- **style**: Changes that only affect code formatting or style, without affecting functionality. This ensures consistency and readability of the codebase.
- **perf**: Changes that improve the performance of the project.

You will need to fork uAgents and then clone the repo to make PRs to this project. Please be descriptive in your commits:

```bash
git commit -m "feat: add new feature x"
git commit -m "fix: fix bug in feature x"
git commit -m "docs: add documentation for feature x"
git commit -m "test: add test suite for feature x"
```

Further details on `conventional commits` can be found here: <https://www.conventionalcommits.org/en/v1.0.0/>

## Support and help

Suppport and extra information is available in our [documentation](https://fetch.ai/docs) and on [Discord](https://discord.com/invite/fetchai)
