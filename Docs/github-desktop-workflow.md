# Ken's GitHub Desktop Workflow

Use this routine for every NameTagBuilder change. It keeps unfinished work out
of `main` and gives you a chance to test it before it becomes the shared version.

## 1. Start a feature branch

1. Open **NameTagBuilder** in GitHub Desktop.
2. Click **Fetch origin** (or **Pull origin**) to get the latest shared work.
3. Confirm **Current Branch** is `main`.
4. Click **Current Branch** → **New Branch**.
5. Give it a descriptive name such as `feature/engraved-text` or
   `fix/hole-position`, then click **Create Branch**.

Do not make normal project changes directly on `main`.

## 2. Make and test the change

1. Edit the model in CQ-editor and run it to inspect the shape.
2. Save the Python file.
3. In GitHub Desktop, look through the changed-file list and diff.
4. Test the tag before committing: run it in CQ-editor and, when the geometry
   changes, generate and inspect an STL in the reference Conda environment.

## 3. Commit and publish the branch

1. In GitHub Desktop's **Changes** tab, select only the files that belong to
   this feature.
2. Write a short commit summary, for example `Add engraved text option`.
3. Click **Commit to feature/engraved-text**.
4. Click **Publish branch** (the first time) or **Push origin** (later commits).

The branch is now safely stored on GitHub, but `main` has not changed.

## 4. Request review and merge

1. Click **Preview Pull Request**, then **Create Pull Request**.
2. On GitHub, state what changed and how it was tested. The pull-request
   template provides a checklist.
3. Ask Don to review it, or review it yourself if it is a small solo change.
4. After approval and testing, click **Merge pull request** on GitHub.

GitHub updates remote `main` when the pull request is merged. There is no need
to separately push `main` afterward.

## 5. Get ready for the next feature

1. Return to GitHub Desktop and switch to `main`.
2. Click **Pull origin** so your computer has the merged version.
3. Delete the completed local feature branch if GitHub Desktop offers to do so.

Then begin the next feature from this updated `main` branch.

## If something looks wrong

Do not merge. Leave the pull request open, write down what happened, and ask for
help. The feature branch preserves the work without affecting `main`.
