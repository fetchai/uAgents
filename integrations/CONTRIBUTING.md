# Contributing

Contributions to integrations are welcome 😊 the integrations repo is the place where you can share how you've integrated uAgents with other technology.

## A few simple rules

- Search the repo for the integration you're submitting, just in case.

- run [black](https://pypi.org/project/black/) on your code before submitting.

- Include a `project.json` file, example of:

```js
{
    "title": "Bert Base Uncased",
    "description": "BERT base model (uncased) Pretrained model on English language using a masked language modeling (MLM) objective.",
    "categories":    ["Text Classification", "Hugging Face", "Text Generation"]
}
```

## Commits and PRs

This project uses Conventional Commits to generate release notes and to determine versioning. Commit messages should adhere to this standard and be of the form:

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