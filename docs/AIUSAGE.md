<!-- SPDX-License-Identifier: MIT -->
# AI Usage

> **Audience:** Developers and maintainers
> **Purpose:** AI Usage reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

## Purpose

This document records how AI-assisted tools were used during the design,
implementation, testing, documentation, and maintenance of this project.

The goal is transparency for maintainers, contributors, and users.

## General policy

AI-generated or AI-assisted output is not considered authoritative solely
because it was produced by an AI system.

Architectural decisions, source-code changes, documentation, tests, and
external technical claims must be reviewed and verified before acceptance.

Accepted ADRs are project decisions made by maintainers, regardless of whether
AI assisted in their discussion or drafting.

## Release history

| Release | AI Tool | Model | Date Range |
|---|---|---|---|
| 0.1.0 (pre-release) | ChatGPT | GPT-5.6 Sol, GPT-6 | 2026-09-28 - 2026-10-23 |

### 0.1.0 (pre-release)

* AI Tool: ChatGPT
* Models: GPT-5.6 Sol, GPT-6
* Date Range: 2026-09-28 - 2026-10-23
* Maintainer Review: Required

#### Areas of AI assistance

AI assistance has been used for:

- initial project architecture;
- Green Button / ESPI research;
- evaluation of existing open-source projects;
- provider and OAuth architecture;
- canonical data-model discussions;
- ADR planning and drafting;
- repository structure;
- test strategy and CI/CD planning;
- documentation planning;
- integration source development and Recorder import tests;
- Explorer UI, tests, HACS registration and packaging;
- installation and release-documentation review.

#### Verification

AI-assisted conclusions should be verified against authoritative sources where
appropriate, including:

- NAESB ESPI XML schemas;
- Green Button Alliance documentation;
- provider documentation;
- upstream source repositories;
- actual test results;
- sanitized or synthetic regression fixtures.

#### Maintenance

Update this document for every project release.

Each release entry should record:

- project release/version;
- AI product/tool;
- AI model/version;
- date or date range;
- areas of AI assistance;
- relevant human review and verification.
