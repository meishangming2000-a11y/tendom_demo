# Simulations Repository Agent Instructions

This directory is an independent Git repository and the formal submodule of
the parent tendon project. When embedded under the parent repository, the
canonical policy is `TENDON_GIT_LIFECYCLE_V1` in
`../docs/repository_management.md`; these rules also apply when this repository
is cloned alone.

At task start, record this repository's branch, HEAD, upstream, worktree,
unfinished operations, and current remote branch SHA. Do not treat parent
repository status or a parent fetch as evidence about this repository.

At task end, verify required assets, run the minimum sufficient tests, audit
every task-owned file, and stage only explicit paths. Never use `git add .`,
`git add -A`, automatic stash/reset/rebase/clean/switch, or force push. Do not
automatically commit datasets, checkpoints, videos, caches, image batches, or
runtime dumps.

When parent and submodule both change, the publication order is
`simulations -> root`: commit and push this repository first, verify the exact
remote SHA with `ls-remote`, and only then allow the parent to update its
mode-160000 gitlink. A dirty worktree or unrelated residual files must be
reported and must never be swept into the commit.
