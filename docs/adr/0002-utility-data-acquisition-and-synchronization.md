<!-- SPDX-License-Identifier: MIT -->
# 0002. Utility data acquisition and synchronization

**Audience:** Maintainers and contributors

**Purpose:** Record architectural boundaries for manual Green Button upload.

**Status:** Accepted

**Release:** 0.1.3

**Last Updated:** 2026-10-29

* Status: Accepted
* Date: 2026-10-29

## Context

Users need to import later utility downloads and accepted corrections
without utility credentials entering Home Assistant or losing historical
usage already synchronized to Recorder. Energy Ingest is authoritative for
validated usage; Home Assistant Recorder is a derived reporting store.
ADR-0001 already defines Recorder history, gaps, and correction behavior.

## Decision

1. The user authenticates directly with their utility and downloads actual
   Green Button XML. The integration does not collect utility credentials.
2. A Home Assistant authenticated upload endpoint forwards XML to the
   separately authenticated Energy Ingest API. No browser API bearer token.
3. Energy Ingest validates acquisition source identity and XML, commits
   canonical accepted observations, and reports import outcomes.
4. Recorder synchronization occurs only after a successful canonical import.
   A failure in Recorder synchronization is separately reported and retryable;
   it does not roll back an accepted canonical import.
5. The integration preserves missing periods and accepts genuine revisions;
   it never estimates or synthesizes observations. Electricity and natural
   gas usage are in scope; billing and rates are out of scope.
6. A production release requires verified authorization of source IDs,
   bounded upload handling, authenticated access, and runtime tests.

## Consequences and open questions

The UI discovers source names and IDs from the authenticated Energy Ingest
catalog, but users must explicitly select the source for each XML batch.
Provider-specific download links must remain configurable. The appropriate
source-selection and upload authorization contract must be finalized before
acceptance and production deployment. This decision does not supersede
accepted ADR-0001 or establish an already-validated security boundary.
