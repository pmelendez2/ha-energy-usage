#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [[ -n "$(git status --porcelain)" ]]; then
  echo 'ERROR: commit or discard local changes before publishing.' >&2
  exit 1
fi

echo 'Checking documentation policy...'
python3 scripts/check_documentation.py
python3 -m unittest discover -s tests -p 'test_doc_policy.py'

# Exclude explicitly private artifacts even if a developer force-added them.
if git ls-files | grep -Ei \
  '(^|/)(secrets|private|scratch|tmp)/|(^|/)\.env($|\.[^.]*$)|\.(age|pem|key|p12|pfx|sqlite|db|zip)$' \
  | grep -Ev '\.env\.[^.]+\.example$'; then
  echo 'ERROR: prohibited tracked paths (inspect above).' >&2
  exit 1
fi

if ! command -v docker >/dev/null; then
  echo 'ERROR: Docker is required to scan Git history.' >&2
  exit 1
fi

# Linked worktrees have an absolute gitdir reference in their .git file.
# Keep the host paths unchanged when mounting the shared Git metadata.
REPO_ROOT="$(git rev-parse --show-toplevel)"
COMMON_GIT_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"
GIT_DIR="$(git rev-parse --absolute-git-dir)"

if [[ ! -d "$COMMON_GIT_DIR" || ! -d "$GIT_DIR" ]]; then
  echo 'ERROR: cannot locate Git metadata for history scanning.' >&2
  exit 1
fi

# Match the host file owner to avoid Git's dubious-ownership rejection.
DOCKER_GIT=(docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$REPO_ROOT:$REPO_ROOT:ro" \
  -v "$COMMON_GIT_DIR:$COMMON_GIT_DIR:ro" \
  -w "$REPO_ROOT")

if ! "${DOCKER_GIT[@]}" --entrypoint git \
    ghcr.io/gitleaks/gitleaks:v8.30.1 \
    rev-parse --verify HEAD >/dev/null; then
  echo 'ERROR: Gitleaks container cannot read Git history.' >&2
  exit 1
fi

echo 'Scanning local Git history for secrets...'
SCAN_LOG="$(mktemp)"
trap 'rm -f -- "$SCAN_LOG"' EXIT
if ! "${DOCKER_GIT[@]}" \
    ghcr.io/gitleaks/gitleaks:v8.30.1 \
    git --redact=100 . >"$SCAN_LOG" 2>&1; then
  cat "$SCAN_LOG"
  echo 'ERROR: Gitleaks history scan failed.' >&2
  exit 1
fi
cat "$SCAN_LOG"
if grep -Eq '0 commits scanned|fatal: not a git repository|skipping finding links' \
    "$SCAN_LOG"; then
  echo 'ERROR: Gitleaks did not scan usable Git history.' >&2
  exit 1
fi

echo 'Checking whitespace...'
git diff HEAD --check

echo 'Publication checks passed. Review commits before pushing.'
