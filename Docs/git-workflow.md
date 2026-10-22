# NameTagBuilder Git Workflow

## Goal

Every change to the model is developed on a feature branch, tested by its author
and reviewed by the other collaborator before it is merged into `main`.
`main` should always contain a version that can generate a printable name tag.

## Start a feature

Begin from the latest `main` branch and give the branch a short, descriptive
name. Use `feature/` for new capabilities and `fix/` for corrections.

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/engraved-text
```

Make small, focused changes. Do not combine unrelated improvements in one branch.

## Test before sharing

Before opening a pull request, verify the change in the tools relevant to it:

- In CQ-editor, run `nametag_builder.py` and visually inspect the result.
- In the reference Conda environment, generate an STL using the command-line
  workflow.
- Open the resulting STL in a slicer and confirm the intended geometry,
  lettering, and hole are present.
- Record the exact command, parameter values, and CadQuery version in the pull
  request when they differ from the documented defaults.

Not every branch needs both people to repeat every test, but a change should be
checked in CQ-editor and in the reference environment before it is merged.

## Share and review

Commit the finished change and publish its branch:

```bash
git add <changed-files>
git commit -m "Add engraved-text option"
git push -u origin feature/engraved-text
```

On GitHub, open a pull request from the feature branch into `main`. The author
should summarize the design change and testing performed. The other collaborator
reviews the code and, when practical, tests the branch locally before approving
it. Merge only after approval and successful testing.

## After merging

Bring the local `main` branch up to date, then remove the completed local branch:

```bash
git switch main
git pull --ff-only origin main
git branch -d feature/engraved-text
```

Delete the remote branch from GitHub after merging, or use GitHub's **Delete
branch** button on the merged pull request.

## GitHub setting to enable

In the repository's GitHub settings, add a branch-protection rule for `main`.
Require pull requests before merging and require one approval. This prevents an
accidental direct push to `main` while keeping the workflow simple for two people.
