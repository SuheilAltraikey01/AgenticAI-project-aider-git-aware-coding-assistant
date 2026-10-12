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

AgenticAI-project-aider-git-aware-coding-assistant/
|
|-- README.md
|   Main project documentation including setup, architecture,
|   workflow, safety controls, evaluation plan, repository map,
|   limitations, and development roadmap.
|
|-- requirements.txt
|   Pinned Python dependencies required to run and test the project.
|
|-- .env.example
|   Example environment configuration using dummy values only.
|   Documents the required LLM provider, model, and API key variables.
|
|-- .gitignore
|   Prevents secrets, virtual environments, caches, IDE files,
|   generated traces, and other local files from being committed.
|
|-- pytest.ini
|   Pytest configuration including the src/ Python path and tests/
|   discovery directory.
|
|-- src/
|   `-- aider_agent/
|       |
|       |-- __init__.py
|       |   Marks aider_agent as a Python package.
|       |
|       |-- config.py
|       |   Loads environment settings and validates the configured
|       |   DeepSeek API key and model configuration.
|       |
|       |-- git/
|       |   Git inspection components.
|       |   |
|       |   |-- __init__.py
|       |   |
|       |   `-- diff_reader.py
|       |       Reads staged Git files and staged diffs in read-only
|       |       mode without committing or pushing changes.
|       |
|       |-- agent/
|       |   LangGraph workflow and shared agent state.
|       |   |
|       |   |-- __init__.py
|       |   |
|       |   |-- state.py
|       |   |   Defines the shared AgentState used across workflow
|       |   |   nodes, including Git context, analysis results,
|       |   |   candidate tests, execution results, retry state,
|       |   |   approval state, and applied files.
|       |   |
|       |   `-- graph.py
|       |       Builds the bounded LangGraph workflow.
|       |
|       |       Current workflow:
|       |
|       |       staged Git changes
|       |              |
|       |              v
|       |       risk/test-gap analysis
|       |              |
|       |              v
|       |       candidate test generation
|       |              |
|       |              v
|       |       isolated pytest execution
|       |              |
|       |        +-----+-----+
|       |        |           |
|       |       PASS        FAIL
|       |        |           |
|       |        |           v
|       |        |       replanning
|       |        |           |
|       |        |           v
|       |        |       retry test
|       |        |           |
|       |        |     max 3 retries
|       |        |           |
|       |        v           v
|       |   human approval  stop/escalate
|       |        |
|       |   +----+----+
|       |   |         |
|       | approve    reject
|       |   |         |
|       |   v         v
|       | apply      END
|       | candidate
|       | tests
|       |   |
|       |   v
|       |  END
|       |
|       |-- llm/
|       |   LLM provider abstraction and implementations.
|       |   |
|       |   |-- __init__.py
|       |   |
|       |   |-- base.py
|       |   |   Defines the common LlmClient protocol used by the
|       |   |   agent instead of coupling workflow code directly
|       |   |   to one provider.
|       |   |
|       |   |-- deepseek_client.py
|       |   |   Real DeepSeek API client used for live risk analysis,
|       |   |   candidate test generation, and replanning.
|       |   |
|       |   `-- fake_client.py
|       |       Deterministic offline LLM implementation used by tests
|       |       so the automated test suite requires no API or network.
|       |
|       |-- analysis/
|       |   LLM-assisted reasoning and candidate-generation components.
|       |   |
|       |   |-- __init__.py
|       |   |
|       |   |-- risk_analyzer.py
|       |   |   Analyzes the staged Git diff for risk, risky files,
|       |   |   missing test coverage, and a structured summary.
|       |   |   Treats staged code and comments as untrusted input.
|       |   |
|       |   |-- candidate_test_generator.py
|       |   |   Generates structured pytest candidate tests from
|       |   |   identified test gaps and validates generated paths
|       |   |   before they are accepted by the workflow.
|       |   |
|       |   `-- test_replanner.py
|       |       Uses previous candidate tests together with pytest
|       |       stdout, stderr, timeout status, and Git context to
|       |       generate revised tests after a failed execution.
|       |
|       |-- execution/
|       |   Candidate-test execution components.
|       |   |
|       |   |-- __init__.py
|       |   |
|       |   |-- base.py
|       |   |   Defines the TestRunner protocol and structured
|       |   |   TestExecutionResult returned to the workflow.
|       |   |
|       |   `-- pytest_runner.py
|       |       Exports the staged Git snapshot into a disposable
|       |       temporary directory, writes candidate tests only
|       |       inside that environment, runs pytest with a fixed
|       |       timeout, captures stdout/stderr/exit status, removes
|       |       known LLM API secrets from the subprocess environment,
|       |       and deletes the temporary directory afterwards.
|       |
|       `-- approval/
|           Human oversight and controlled candidate application.
|           |
|           |
|           |-- __init__.py
|           |
|           |-- base.py
|           |   Defines the ApprovalGate and CandidateApplier
|           |   protocols used by the workflow.
|           |
|           |-- console_gate.py
|           |   Presents generated candidate tests to the human
|           |   reviewer and supports:
|           |
|           |       A - Approve
|           |       R - Reject
|           |       V - View unified diff
|           |
|           |   The workflow cannot write a passing generated test
|           |   into the real working repository without explicit
|           |   approval.
|           |
|           `-- candidate_applier.py
|               Validates approved test paths and writes approved
|               candidate tests into the real working repository.
|               It never performs git add, git commit, or git push.
            |-- tracing/
|             Execution trace persistence components.
|           |
|           |-- __init__.py
|           |
|           |-- base.py
|           |   Defines the TraceWriter protocol used by the workflow.
|           |
|           `-- json_trace_writer.py
|       Persists a structured JSON trace after each completed
|       workflow. Records analysis, candidate tests, execution
|       results, retries, approval decisions, applied files,
|       timestamps, and final status while avoiding storage of
|       the raw staged Git diff.
|
`-- tests/
    |
    |-- __init__.py
    |   Marks the tests directory as a Python package.
    |
    |-- test_setup.py
    |   Basic project and pytest setup verification.
    |
    |-- test_diff_reader.py
    |   Tests staged-file and staged-diff reading, empty staged
    |   changes, and invalid Git repository handling.
    |
    |-- test_agent_graph.py
    |   Tests the main LangGraph workflow using fake dependencies.
    |   Covers:
    |
    |       - no staged changes
    |       - staged-change analysis
    |       - candidate generation
    |       - passing execution
    |       - human approval
    |       - human rejection
    |       - no-test-gap termination
    |
    |-- test_config.py
    |   Tests configuration loading and required API-key validation.
    |
    |-- test_deepseek_client.py
    |   Tests DeepSeek client behavior without making live API calls.
    |
    |-- test_fake_llm_client.py
    |   Tests deterministic fake LLM responses, call recording,
    |   ordered responses, and exhausted-response handling.
    |
    |-- test_risk_analyzer.py
    |   Tests structured risk/test-gap analysis, prompt construction,
    |   JSON validation, and risk-level validation.
    |
    |-- test_candidate_test_generator.py
    |   Tests candidate-test generation, structured output,
    |   candidate path validation, and unsafe-path rejection.
    |
    |-- test_pytest_runner.py
    |   Tests candidate execution in the temporary environment,
    |   successful and failed pytest execution, filesystem isolation,
    |   timeout handling, and unsafe-path rejection.
    |
    |-- test_test_replanner.py
    |   Tests failure-aware candidate-test revision and verifies that
    |   pytest observations are provided to the replanning component.
    |
    |-- test_replanning_loop.py
    |   Tests the complete bounded recovery loop:
    |
    |       failure
    |          |
    |          v
    |       observe
    |          |
    |          v
    |       replan
    |          |
    |          v
    |       retry
    |
    |   Also verifies:
    |
    |       - recovery after a failed candidate
    |       - approval after successful recovery
    |       - rejection after successful recovery
    |       - maximum retry termination
    |
    |-- test_console_approval_gate.py
    |   Tests human approval, rejection, and View Diff behavior
    |   without requiring real interactive keyboard input.
    |
    `-- test_candidate_applier.py
    |   Tests approved candidate application, path-traversal safety,
    |    file writing, and verifies that applied tests are not
    |    automatically staged or committed by Git.
    |-- test_json_trace_writer.py
    |   Tests structured JSON persistence and verifies that the raw
    |   staged Git diff is not copied into trace files.
    |
    |-- test_execution_trace.py
    |   Tests that a complete LangGraph workflow produces an
    |   inspectable JSON event trace.   
    
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
- [x] Phase 5 - DeepSeek integration
- [x] Phase 6 - Offline fake LLM provider
- [x] Phase 7 - Risk and test-gap analysis
- [x] Phase 8 - Candidate test generation
- [x] Phase 9 - Isolated pytest execution
- [x] Phase 10 - Bounded retry and replanning loop
- [x] Phase 11 - Human approval gate
- [x] Phase 12 - JSON execution traces
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

### LLM Provider

The project currently uses DeepSeek through an OpenAI-compatible API.

The DeepSeek integration is isolated behind an LLM client abstraction.
The agent does not give the model direct access to Git, files, tests,
commit, or push operations.

### LLM Provider Change

The original project proposal named Claude as the planned LLM provider.

During implementation, the provider was changed to DeepSeek.
The agent architecture, Git safety boundaries, evaluation goals,
and human-oversight design remain unchanged.

### Offline LLM Testing

The automated test suite does not require a real LLM API key or
external network access.

A `FakeLlmClient` implements the same `generate()` interface used by
the real DeepSeek client. It returns predefined responses and records
the prompts it receives.

This allows agent behavior to be tested deterministically without
calling an external model provider.

### Generated Test Safety

Candidate tests are generated as structured data only.

During this stage, generated tests are not written into the developer's
working repository and are not executed. Candidate file paths are
validated and must remain inside the `tests/` directory.

Execution of generated tests is handled separately in an isolated
environment in a later phase.

### Candidate Test Execution Safety

Generated tests are never executed directly inside the developer's
working repository.

The runner exports the staged Git snapshot into a disposable temporary
directory, writes candidate tests only inside that directory, executes
pytest with a fixed timeout, captures the result, and deletes the
temporary directory afterwards.

LLM API secrets are removed from the test subprocess environment.

This design provides filesystem and process separation, but it is not a
complete operating-system security sandbox and does not itself guarantee
network isolation. Stronger container-based isolation remains a future
hardening step.

### Bounded Retry and Replanning

When a generated candidate test fails, the agent does not simply run
the same test again.

The pytest observation is returned to the replanning component,
including bounded stdout, stderr, timeout status, the previous candidate
tests, and the original staged Git context.

The LLM then proposes a revised candidate test, which is validated and
executed again in the isolated test environment.

The workflow allows a maximum of three retries after the initial test
execution. If the tests still fail, the workflow stops and requires
human review.

This prevents unbounded autonomous loops while allowing the agent to
recover from test-generation failures.
### Human Approval Gate

Candidate tests are first executed inside the isolated test environment.

A candidate that passes is not automatically written to the developer's
working repository. The workflow pauses at a human approval gate.

The reviewer can:

- `A` - Approve the candidate tests.
- `R` - Reject the candidate tests and stop.
- `V` - View the proposed unified diff before deciding.

Only explicit human approval allows the candidate tests to be written
to the working repository.

Rejecting a candidate leaves the working repository unchanged.

Even after approval, the agent does not stage, commit, or push Git
changes. Those actions remain under direct developer control.

### JSON Execution Traces

Every completed agent workflow produces a structured local JSON trace
inside the `traces/` directory.

The trace records the major observable workflow events, including:

- staged file inspection
- risk and test-gap analysis
- candidate test generation
- pytest execution attempts
- replanning and retry attempts
- human approval or rejection
- applied candidate files
- final workflow status

Each event includes a UTC timestamp and structured details.

The raw staged Git diff is not copied into the trace. Instead, the trace
stores the staged file names, diff character count, and a SHA-256 digest.
This reduces unnecessary duplication of source code or potentially
sensitive content in logs.

Generated candidate tests and bounded pytest output are retained because
they are needed to inspect and explain the agent's decisions.

Trace files are local development artifacts and are excluded from Git by
`.gitignore`.