# Aider: Git-Aware Coding Assistant

**Master's Project - Agentic Artificial Intelligence**  
**Course:** COSC726 - Agentic Artificial Intelligence  
**Project:** #11 - Aider  
**Reference System:** Aider  
**Project Type:** Level 2 - Applied Agent  
**Current Status:** Phase 1 - Project Setup

---

## 1. What It Does

Aider: Git-Aware Coding Assistant is a bounded academic coding agent inspired by the Aider reference system.

The project focuses on software development and Git-based code review. Its purpose is to help a developer review staged code changes before creating a Git commit.

The agent will read the staged Git diff, identify risky or potentially untested changes, generate candidate tests when necessary, run those tests in an isolated environment, observe the results, and retry within a fixed limit.

The agent does not automatically commit or push code. The final decision remains with the developer.

### Problem

Developers may miss risky or untested code paths when manually reviewing changes, especially when a Git diff contains several files or changes existing program logic.

This project investigates whether a small agentic workflow can help detect those risks before a commit is created.

### Project Goal

Given a staged Git diff, the agent will:

1. Read the staged code changes.
2. Analyze the changed code.
3. Identify risky or potentially untested changes.
4. Generate candidate tests when required.
5. Execute the tests in an isolated environment.
6. Observe the test results.
7. Revise and retry when appropriate.
8. Stop after a maximum of three attempts.
9. Produce a final review summary for a human developer.

### Agentic Loop

The project follows the bounded agent loop:

```text
Sense -> Decide -> Act -> Observe -> Repeat / Stop
```

**Sense**  
Read the staged Git diff and available test information.

**Decide**  
Use an LLM to analyze the changes and determine whether additional tests are required.

**Act**  
Generate candidate tests and execute approved tools.

**Observe**  
Capture test results and update the current execution state.

**Repeat / Stop**  
If the tests fail, the agent may revise its candidate test and retry.

The agent stops when:

- the required tests pass, or
- the maximum retry limit is reached.

If the retry limit is reached, the result is escalated to the human reviewer.

---

## 2. Prerequisites

The project is being developed with:

- Python 3.12
- Git
- Visual Studio Code
- GitHub
- Python virtual environment
- DeepSeek API for the LLM component

Later phases will also use:

- GitPython
- pytest
- python-dotenv
- LangGraph
- Docker or another isolated test environment

To verify Python:

```bash
python --version
```

To verify Git:

```bash
git --version
```

---

## 3. Install

### Clone the Repository

When the repository is available publicly, it can be cloned using:

```bash
git clone https://github.com/SuheilAltraikey01/AgenticAI-project-aider-git-aware-coding-assistant.git
```

Then enter the project directory:

```bash
cd AgenticAI-project-aider-git-aware-coding-assistant
```

### Create a Virtual Environment

On Windows:

```bash
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

The dependency list will be updated as each project phase is implemented.

---

## 4. Configure

The project uses environment variables for configuration and API credentials.

Copy:

```text
.env.example
```

to:

```text
.env
```

The `.env.example` file contains dummy values only.

Example:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your_api_key_here
```

The two configuration variables used to select the model configuration are:

```text
LLM_PROVIDER
LLM_MODEL
```

The real API key must be stored only in:

```text
.env
```

The `.env` file is excluded through `.gitignore` and must never be committed to GitHub.

---

## 5. Run

**Current development status:** the executable agent controller has not yet been implemented.

The final project will provide one command that starts the agent.

Planned command structure:

```bash
python -m aider_agent.main
```

This section will be updated when the controller loop is implemented and tested.

---

## 6. Test

The project uses `pytest`.

Run the test suite with:

```bash
pytest
```

The tests are designed to run:

- without a DeepSeek API key;
- without external network access;
- without modifying a remote Git repository.

During development, external LLM behavior will be replaced by a fake or mock LLM client when running automated tests.

### Current Expected Result

During Phase 1, the initial project setup test should report:

```text
1 passed
```

More tests will be added incrementally as project functionality is implemented.

---

## 7. Worked Example

The complete worked example will be implemented after the Git-diff reader and DeepSeek analysis stages are completed.

The expected workflow will resemble the following.

A developer changes a Python function:

```python
def calculate_discount(price, discount):
    return price - discount
```

The developer stages the change:

```bash
git add .
```

The agent reads the staged diff and analyzes it.

Example future output:

```text
Changed files: 1

File:
src/example.py

Risk:
A new calculation path was introduced.

Test coverage:
Potentially insufficient.

Suggested action:
Generate a candidate test for invalid or boundary values.

Test result:
Passed

Agent status:
Ready for human review.
```

This example is illustrative only during the current project phase. A reproducible real example will replace it after the implementation is complete.

---

## 8. Reproduce the Evaluation

The evaluation harness has not yet been implemented.

The final evaluation will use approximately 5-10 controlled Git diff cases containing a mixture of:

- correctly tested changes;
- deliberately untested changes;
- risky changes;
- safe changes;
- failure and recovery cases.

Planned evaluation metrics include:

- risky-change detection rate;
- false-positive rate;
- generated-test quality;
- number of retry iterations;
- successful completion rate;
- latency;
- LLM usage and cost.

The final repository will provide one command to reproduce the evaluation.

Planned structure:

```bash
python evaluation/run_evaluation.py
```

The numbers produced by the evaluation command will match the numbers reported in the final project report.

---

## 9. Approval Gate

The system uses human oversight for changes that affect the developer's real working repository.

The agent may automatically:

- read staged Git changes;
- analyze code;
- generate candidate tests;
- execute tests inside the isolated environment;
- produce recommendations.

However, a generated candidate test must not be copied into the developer's real working repository without explicit human approval.

The planned approval screen will show information similar to:

```text
Candidate Test Ready

File:
tests/test_example.py

Reason:
A changed code path does not appear to have test coverage.

Sandbox Result:
8 tests passed.

Choose an action:

[A] Approve
[R] Reject
[V] View Diff
```

If the developer approves, the proposed candidate test may be copied from the isolated environment into the working repository.

If the developer rejects it, the real repository is not changed.

The agent is never permitted to automatically execute:

```bash
git commit
```

or:

```bash
git push
```

The developer remains responsible for the final Git decision.

---

## 10. Repository Map

Current repository structure:

```text
aider-git-aware-coding-assistant/
|
|-- README.md
|   Project description, setup instructions, usage, evaluation,
|   approval gate, and limitations.
|
|-- requirements.txt
|   Python dependencies with pinned versions.
|
|-- .env.example
|   Example environment configuration with dummy values.
|
|-- .gitignore
|   Files that must not be committed, including .env and
|   the local virtual environment.
|
|-- src/
|   Main source code.
|   |
|   `-- aider_agent/
|       Python package containing the agent implementation.
|
`-- tests/
    Automated project tests that run without an API key
    or external network access.
```

Planned later structure:

```text
src/aider_agent/
|
|-- agent/
|   Agent state, workflow, and controller.
|
|-- git/
|   Git staged-diff reading tools.
|
|-- llm/
|   DeepSeek and offline fake LLM clients.
|
|-- testing/
|   Candidate test generation and execution.
|
|-- sandbox/
|   Isolated execution environment.
|
|-- approval/
|   Human approval gate.
|
`-- trace/
    Execution-trace persistence.

evaluation/
|
|-- cases/
|   Reproducible evaluation cases.
|
`-- run_evaluation.py
    Evaluation harness.
```

The repository map will be updated when these directories are introduced.

---

## 11. Limitations

The current project scope is deliberately bounded.

Planned limitations include:

- The agent is intended primarily for small-to-medium Git diffs.
- The first implementation focuses mainly on Python projects using pytest.
- Complex risks involving many interacting files may not always be detected.
- LLM-generated analysis may be incomplete or incorrect.
- Generated tests are candidate suggestions and require human oversight.
- The agent does not automatically commit code.
- The agent does not automatically push code.
- The agent does not operate on production repositories autonomously.
- Generated code is executed only in an isolated environment.
- A maximum retry limit prevents uncontrolled agent loops.

The project is an academic prototype inspired by Aider and does not attempt to reproduce the complete Aider product.

---

## Project Roadmap

- [x] Phase 0 - GitHub repository and initial README
- [x] Phase 1 - Python project structure and environment
- [x] Phase 2 - Staged Git diff reader
- [x] Phase 3 - Offline Git reader tests
- [x] Phase 4 - Agent state and LangGraph workflow
- [ ] Phase 5 - DeepSeek integration
- [ ] Phase 6 - Offline fake LLM provider
- [ ] Phase 7 - Risk and test-gap analysis
- [ ] Phase 8 - Candidate test generation
- [ ] Phase 9 - Isolated pytest execution
- [ ] Phase 10 - Bounded retry and replanning loop
- [ ] Phase 11 - Human approval gate
- [ ] Phase 12 - JSON execution traces
- [ ] Phase 13 - Evaluation harness and task set
- [ ] Phase 14 - Failure and recovery scenarios
- [ ] Phase 15 - Cost and latency evaluation
- [ ] Phase 16 - Final documentation and demonstration

---

## Reference System

The reference system for this project is:

**Aider - Git-aware AI coding assistant**

This project studies selected agentic ideas demonstrated by Aider, particularly the interaction between an AI coding assistant and a Git repository.

The project does not attempt to clone all Aider functionality.

Instead, it implements a smaller and auditable academic agent focused on:

```text
Git Diff
   |
   v
Code Analysis
   |
   v
Risk / Test Gap Detection
   |
   v
Candidate Test Generation
   |
   v
Sandbox Execution
   |
   v
Observe Result
   |
   v
Retry / Stop
   |
   v
Human Approval
```

---

## Safety Boundaries

The project follows the following safety boundaries:

- Git inspection starts as read-only.
- No automatic Git commit.
- No automatic Git push.
- API keys are never stored in source code.
- The real `.env` file is never committed.
- Candidate code is tested in isolation before human approval.
- Tests must also support offline execution.
- The agent has a fixed maximum retry count.
- Human approval is required before applying generated changes to the working repository.
- Execution traces are retained for audit and evaluation.

