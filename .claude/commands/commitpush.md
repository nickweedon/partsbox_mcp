# Commit and Push Changes

Create a git commit following the project's commit guidelines and push to the remote repository.

## Git Commit Guidelines

- Do NOT include "Generated with Claude Code" or similar AI attribution in commit messages
- Do NOT include "Co-Authored-By: Claude" or similar co-author tags
- When doing a git commit, if there are untracked files then stop and ask if I would like them included also
- Always do a 'git commit -a' and include all modified files
- Always include descriptive commit comments that succinctly describe the changes made in the summary and a separate line with an asterisk bullet point that describes each feature or notable change in more detail
- Write commit messages as if authored solely by the developer

## Steps

1. Run `git status` to see all changes (both tracked and untracked files)
2. Run `git diff` to see the actual changes
3. If there are untracked files, ask the user if they should be included in the commit
4. If user wants untracked files included, add them with `git add <files>`
5. Create a commit with 'git commit -a' using a descriptive message that:
   - Has a clear summary line
   - Includes bullet points for each notable change
   - Does NOT include AI attribution or co-author tags
6. Push the commit to the remote repository with `git push`
7. Report the results

Execute these steps and handle any errors appropriately.
