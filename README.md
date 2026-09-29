# Aider: Git-Aware Coding Assistant

Master's Project - Agentic AI  
Project #11 - Aider  
Status: Phase 0 - Project Setup

## Project Overview

This project is a bounded academic coding agent inspired by Aider.

The agent reviews staged Git changes before a developer commits them. It
identifies risky or untested changes, proposes candidate tests, runs the
tests, observes the results, and produces a final review summary.

The system does not automatically commit or push code. The final decision
always remains with the developer.

## Problem

Developers can miss risky or untested code paths when reviewing code
changes manually, especially when a diff contains several files.

The project investigates whether a small agentic workflow can help review
those changes before commit.

## Project Goal

Given a staged Git diff, the agent will:

1. Read the changed code.
2. Identify risky or potentially untested changes.
3. Generate candidate tests when needed.
4. Run the tests.
5. Observe the result.
6. Revise and retry when a test fails.
7. Stop after a maximum of three attempts.
8. Produce a final commit-ready review summary.

## Agent Loop

Sense -> Decide -> Act -> Observe -> Repeat / Stop

### Sense

Read the staged Git diff and current test information.

### Decide

Use DeepSeek to classify the changed code and decide whether new tests
are required.

### Act

Generate candidate tests and execute them in an isolated environment.

### Observe

Capture the test result and update the current run state.

### Repeat / Stop

If the tests fail, the agent may revise them and retry.

The agent stops when:

- the proposed tests pass, or
- the retry limit is reached.

When the retry limit is reached, the result is passed to a human reviewer.

## Planned Technology

- Python
- Visual Studio Code
- Git
- GitPython
- pytest
- DeepSeek API
- JSON execution traces
- Isolated test environment / Docker

## Safety Boundaries

- No automatic Git push.
- No automatic Git commit.
- Git inspection is read-only.
- API keys are never stored in source code.
- Generated tests are executed only in an isolated environment.
- Maximum retry count is three.
- A human makes the final commit/push decision.

## Project Roadmap

- [x] Phase 0 - Repository and README
- [ ] Phase 1 - Python project structure
- [ ] Phase 2 - Git staged-diff reader
- [ ] Phase 3 - DeepSeek integration
- [ ] Phase 4 - Risk and test analysis
- [ ] Phase 5 - Candidate test generation
- [ ] Phase 6 - Test execution
- [ ] Phase 7 - Agent retry loop
- [ ] Phase 8 - JSON execution trace
- [ ] Phase 9 - Sandbox and safety controls
- [ ] Phase 10 - Evaluation dataset
- [ ] Phase 11 - Final documentation and demo

## Reference System

Aider - AI pair programming and Git-aware coding assistant.

This project does not attempt to reproduce the complete Aider system.
It implements a smaller academic agent focused on staged-diff review,
test generation, test feedback, and human approval.

## Current Progress

Repository initialized and initial project scope documented.