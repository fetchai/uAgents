# Contributing

Contributions to this library are welcome.

- If you want to report a bug or ask for features, you can check the [Issues page](https://github.com/fetchai/uAgents/issues) and raise an issue.

- If you would like to contribute a bug fix or feature then [submit a Pull request](https://github.com/fetchai/uAgents/pulls).

## A few simple rules

- Before working on a feature, reach out to one of the core developers or discuss the feature in an issue. The framework caters a diverse audience and new features require upfront coordination.

- Include unit tests when you contribute new features, as they help to a) prove that your code works correctly, and b) guard against future breaking changes to lower the maintenance cost.

- Bug fixes also generally require unit tests, because the presence of bugs usually indicates insufficient test coverage.

- Keep API compatibility in mind when you change code in `uAgents`. Above version `1.0.0`, breaking changes can happen across versions with different left digit. Below version `1.0.0`, they can happen across versions with different middle digit. Reviewers of your pull request will comment on any API compatibility issues.
  
- When you contribute a new feature to `uAgents`, the maintenance burden is transferred to the core team. This means that the benefit of the contribution must be compared against the cost of maintaining the feature.

- Where possible, extend existing features instead of replacing one.

- Before committing and opening a PR, run all tests locally. This saves CI hours and ensures you only commit clean code.

## Contributing code

If you have improvements, send us your pull requests!

A team member will be assigned to review your pull requests. All tests are run as part of CI as well as various other checks (linters, static type checkers, etc). If there are any problems, feedback is provided via GitHub. Once the pull requests is approved and passes continuous integration checks, you or a team member can merge it.

If you want to contribute, start working through the codebase, navigate to the Github [Issues page](https://github.com/fetchai/uAgents/issues) tab and start looking through interesting issues. If you decide to start on an issue, leave a comment so that other people know that you're working on it. If you want to help out, but not alone, use the issue comment thread to coordinate.

## Commits and PRs

This project uses Conventional Commits to generate release notes and to determine versioning. Commit messages should adhere to this standard and be of the form:

```bash
git commit -m "feat: add new feature x"
git commit -m "fix: fix bug in feature x"
git commit -m "docs: add documentation for feature x"
git commit -m "test: add test suite for feature x"
```

Further details on `conventional commits` can be found here: <https://www.conventionalcommits.org/en/v1.0.0/>

When merging a branch, PRs should be squashed into one conventional commit by selecting the `Squash and merge` option. This ensures Release notes are useful and readable when releases are created.

<!-- ![alt text](https://docs.github.com/assets/images/help/pull_requests/select-squash-and-merge-from-drop-down-menu.png) -->
<img src="https://docs.github.com/assets/images/help/pull_requests/select-squash-and-merge-from-drop-down-menu.png" alt="drawing" style="width:600px;"/>