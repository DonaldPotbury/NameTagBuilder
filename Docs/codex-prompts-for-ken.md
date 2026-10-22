# Codex Prompts for Ken

These prompts are designed for working in a Codex chat that has the local
**NameTagBuilder** repository open. Replace `<short-name>` with a brief feature
name such as `engraved-text` or `hole-position`.

## Understand the current state

Use this first if anything is unclear. It only inspects the repository.

```text
I am new to Git. In the NameTagBuilder repository, inspect the current Git status and explain it in plain English. Do not change anything yet.
```

## Start a feature safely

Use this before changing the model. It creates a separate workspace for the
feature and leaves `main` unchanged.

```text
Create a new feature branch named feature/<short-name> from the latest main branch. Do not modify main. Confirm the new branch name and tell me what to do next in CQ-editor.
```

## Review, commit, and publish work

First save and visually test the model in CQ-editor. Then use this prompt to
review exactly what will be shared.

```text
I changed the model and tested it in CQ-editor. Review the Git changes with me in plain English. If the changes are limited to this feature, commit them with a clear message and push the feature branch. Do not merge into main.
```

## Merge an approved feature

Use this only after the pull request has been reviewed and you are ready to
merge it.

```text
The feature branch is pushed and I have reviewed the pull request. Check that main is not modified locally, then explain the safest way for me to merge the pull request on GitHub Desktop or GitHub.
```

## Standing safety rule

Add this sentence to any prompt where it is relevant:

```text
Never merge or push directly to main unless I explicitly ask.
```

## Before asking Codex to commit or push

- Save the model file in CQ-editor.
- Run it in CQ-editor and inspect the result.
- Make sure GitHub Desktop is signed in to Ken's GitHub account with access to
  this repository.
- Read Codex's plain-language description of the changed files before allowing
  a commit or push.

For the complete GitHub Desktop sequence, see
[Ken's GitHub Desktop workflow](github-desktop-workflow.md).
