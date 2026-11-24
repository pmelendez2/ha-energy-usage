#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Canonical, non-publishing release verification for Energy Usage.
set -Eeuo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT"

scope=full
if (($# > 0)); then
  if (($# != 2)) || [[ "$1" != "--scope" ]]; then
    echo 'Usage: bash scripts/verify-release.sh [--scope full|docs|workflow]' >&2
    exit 2
  fi
  scope="$2"
fi
case "$scope" in
  full|docs|workflow) ;;
  *) echo "ERROR: unsupported verification scope: $scope" >&2; exit 2 ;;
esac

step='initialization'
trap 'printf "ERROR: %s failed (exit %s)\n" "$step" "$?" >&2' ERR

run_check() {
  step="$1"
  shift
  printf '\n=== %s ===\n' "$step"
  "$@"
}

# This runner may be called on an uncommitted feature branch. The separate
# check-publication.sh requires a clean tree and checks Git history secrets.
run_check 'CI workflow contracts' python3 scripts/check_ci_workflows.py
run_check 'Documentation version metadata' \
  python3 scripts/manage_doc_versions.py --check
run_check 'Documentation policy' python3 scripts/check_doc_policy.py
run_check 'Documentation consistency and links' \
  python3 scripts/check_documentation.py

if [[ "$scope" == full ]]; then
  run_check 'Integration metadata and JSON' \
    python3 scripts/check_integration.py
  run_check 'Compile Python source and tests' \
    python3 -m compileall -q custom_components/energy_usage tests
  run_check 'Python regression tests' \
    python3 -m unittest discover -s tests -p 'test_*.py'
  run_check 'Explorer JavaScript syntax' \
    node --check custom_components/energy_usage/www/energy-usage-explorer.js
  run_check 'Explorer JavaScript regression tests' \
    node tests/test-energy-usage-explorer.cjs
  step='Build and verify release ZIP'
  mkdir -p build
  run_check 'Build component-only release ZIP' \
    python3 scripts/package_release.py --output build/ha-energy-usage.zip
  run_check 'Validate release ZIP integrity and version' \
    python3 scripts/check_release_package.py build/ha-energy-usage.zip
fi

# GitHub Actions supplies the change base for PR/push validation. Local runs
# validate unstaged, staged and most recent committed changes without writing.
step='Git whitespace verification'
printf '\n=== %s ===\n' "$step"
if [[ -n "${VERIFY_RELEASE_CHANGE_BASE:-}" ]]; then
  git diff --check "$VERIFY_RELEASE_CHANGE_BASE" "${GITHUB_SHA:-HEAD}"
else
  git diff --check HEAD
  git diff --cached --check
  if git rev-parse -q --verify HEAD^ >/dev/null 2>&1; then
    git diff --check HEAD^ HEAD
  else
    git show --format= --check HEAD
  fi
fi

printf '\nRelease verification: PASS (%s scope)\n' "$scope"
