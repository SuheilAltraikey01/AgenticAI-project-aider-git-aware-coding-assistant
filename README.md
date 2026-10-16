# Aider: Git-Aware Coding Assistant

A bounded agentic AI project for reviewing staged Git changes before commit.

The agent reads the staged Git diff, looks for risky changes and missing tests,
generates candidate pytest tests, runs them in an isolated temporary workspace,
and can replan when tests fail.

Passing candidate tests are not written to the developer's repository until a
human explicitly approves them.

The agent never performs `git commit` or `git push`.

---

## What the Project Does

The workflow is:

```text
Staged Git changes
        |
        v
Read staged diff
        |
        v
Risk and test-gap analysis
        |
        v
Generate candidate tests
        |
        v
Run pytest in temporary workspace
        |
        +-------------------+
        |                   |
      PASS                FAIL
        |                   |
        v                   v
 Human approval         Observe result
        |                   |
   +----+----+              v
   |         |            Replan
Approve    Reject            |
   |         |               v
   v         v          Run again
Apply       Stop              |
test                     max retries
   |
   v
Stop
```

This is a **single-agent bounded workflow** built with LangGraph.

The LLM provides reasoning and candidate generation, while the Python
application controls Git access, validation, test execution, retry limits,
approval, and stopping conditions.

---

## Agentic AI Design

This project treats the complete system as the agent, not only the LLM.

The agent follows a simple loop:

```text
Sense
  ↓
Decide
  ↓
Act
  ↓
Observe
  ↓
Update state
  ↓
Replan when needed
  ↓
Stop or escalate
```

Examples in this project:

- **Sense:** read the staged Git diff.
- **Decide:** identify risky files and missing tests.
- **Act:** generate and execute candidate tests.
- **Observe:** inspect pytest results and timeouts.
- **Replan:** revise a failed candidate test.
- **Stop:** finish when no work is needed or the retry limit is reached.
- **Escalate:** require human approval before writing generated tests.

The workflow uses a maximum of three retries by default, which prevents an
unbounded autonomous loop.

---

## Technology

- Python 3.12
- LangGraph
- GitPython
- pytest
- DeepSeek API
- python-dotenv

The original project proposal referenced Claude as the LLM provider.
During implementation, the provider was changed to DeepSeek while keeping
the same bounded workflow and safety design.

The current configured model is defined through the environment:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-flash
```

---

## Installation

Clone the repository:

```powershell
git clone https://github.com/SuheilAltraikey01/AgenticAI-project-aider-git-aware-coding-assistant.git

cd AgenticAI-project-aider-git-aware-coding-assistant
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

Example:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-flash
DEEPSEEK_API_KEY=your_real_api_key_here
```

The real `.env` file is excluded from Git.

Never place a real API key inside `.env.example`.

---

## Testing

Run the complete automated test suite:

```powershell
python -m pytest -v
```

The automated tests use fake LLM responses where possible and do not require
the DeepSeek API or network access.

This keeps the test suite deterministic and repeatable.

---

## Main Workflow Components

### Git Reader

`GitDiffReader` reads only staged changes:

```text
git diff --cached
```

It does not commit, push, or modify repository history.

### Risk Analysis

The staged diff is sent to the LLM for structured analysis.

The result contains:

```text
risk level
risky files
test gaps
summary
```

The Git diff is treated as untrusted input. Instructions found inside source
code, comments, strings, or documentation are not treated as agent commands.

### Candidate Test Generation

When a test gap is found, the LLM may propose pytest tests.

Generated file paths are validated and must remain inside:

```text
tests/
```

Unsafe paths such as:

```text
tests/../../danger.py
```

are rejected.

### Isolated Test Execution

Candidate tests are not initially written to the real working repository.

The runner:

1. creates a temporary directory
2. exports the staged Git snapshot
3. writes candidate tests inside the temporary directory
4. runs pytest with a timeout
5. captures the result
6. deletes the temporary directory

Known LLM API keys are removed from the pytest subprocess environment.

This provides filesystem and process separation, but it is not a complete
OS-level security sandbox and does not guarantee network isolation.

### Replanning

If a candidate test fails or times out, the result is returned to the
replanning component.

The replanner receives:

```text
previous candidate test
pytest stdout
pytest stderr
timeout state
original staged diff
identified test gaps
```

It can then produce a revised test.

The default retry limit is:

```text
3 retries
```

If the tests still fail, the workflow stops and requires human review.

---

## Human Approval Gate

A passing generated test is still not automatically written to the real
repository.

The reviewer sees:

```text
[A] Approve
[R] Reject
[V] View Diff
```

`V` shows the proposed unified diff.

If the reviewer chooses `R`, nothing is applied.

If the reviewer chooses `A`, the approved candidate test can be written to
the working repository.

Even after approval, the agent does not perform:

```text
git add
git commit
git push
```

Those actions remain under developer control.

---

## JSON Execution Traces

Completed workflows create a local JSON trace inside:

```text
traces/
```

The trace records important events such as:

- staged file inspection
- risk analysis
- candidate generation
- test execution
- replanning
- retry count
- approval decision
- final status

The raw staged diff is not copied into the trace. A SHA-256 digest and basic
metadata are stored instead.

Trace files are excluded from Git.

---

## Offline Evaluation

The project includes a deterministic evaluation harness using controlled Git
scenarios.

Run:

```powershell
$env:PYTHONPATH="src"
python -m aider_agent.evaluation.run_evaluation
```

Current controlled evaluation result:

```text
Tasks: 6
Test-gap detection rate: 100.0%
False-positive rate: 0.0%
Candidate quality proxy: 100.0%
Convergence rate: 75.0%
Final-status accuracy: 100.0%
Average retry count: 0.75
Average retries to convergence: 0.33
Retry-limit cases: 1
```

These numbers measure the deterministic workflow using predefined fake LLM
responses.

They should **not** be interpreted as DeepSeek accuracy.

The 75% convergence rate is intentional because one evaluation scenario is
designed to continue failing until the retry limit is reached.

---

## Failure and Recovery Evaluation

A second evaluation suite focuses on failure handling.

Run:

```powershell
$env:PYTHONPATH="src"
python -m aider_agent.evaluation.run_failure_scenarios
```

Current result:

```text
Scenarios: 6
Expected outcomes matched: 6/6

[PASS] timeout_then_recover
  Status: approved_tests_applied
  Retries: 1

[PASS] retry_limit_reached
  Status: retry_limit_reached
  Retries: 2

[PASS] no_candidate_generated
  Status: no_candidate_tests
  Retries: 0

[PASS] human_rejection
  Status: approval_rejected
  Retries: 0

[PASS] malformed_analysis_json
  Exception: ValueError

[PASS] unsafe_candidate_path
  Exception: ValueError

All expected outcomes matched: True
```

The important behaviors demonstrated here are:

- recovery after timeout
- replanning after failure
- bounded retry termination
- safe stopping when no candidate can be produced
- human rejection
- rejection of malformed LLM output
- rejection of unsafe file paths

Malformed or unsafe structured output currently fails closed with
`ValueError`. It is rejected before test execution or file application.

---

## Repository Structure

```text
AgenticAI-project-aider-git-aware-coding-assistant/
|
|-- README.md
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- pytest.ini
|
|-- evaluation/
|   |-- tasks.json
|   |-- failure_scenarios.json
|   `-- results/
|       Generated evaluation reports (ignored by Git)
|
|-- src/
|   `-- aider_agent/
|       |-- config.py
|       |
|       |-- git/
|       |   `-- diff_reader.py
|       |
|       |-- agent/
|       |   |-- state.py
|       |   `-- graph.py
|       |
|       |-- llm/
|       |   |-- base.py
|       |   |-- deepseek_client.py
|       |   `-- fake_client.py
|       |
|       |-- analysis/
|       |   |-- risk_analyzer.py
|       |   |-- candidate_test_generator.py
|       |   `-- test_replanner.py
|       |
|       |-- execution/
|       |   |-- base.py
|       |   `-- pytest_runner.py
|       |
|       |-- approval/
|       |   |-- base.py
|       |   |-- console_gate.py
|       |   `-- candidate_applier.py
|       |
|       |-- tracing/
|       |   |-- base.py
|       |   `-- json_trace_writer.py
|       |
|       `-- evaluation/
|           |-- harness.py
|           |-- run_evaluation.py
|           `-- run_failure_scenarios.py
|
`-- tests/
    |-- test_diff_reader.py
    |-- test_agent_graph.py
    |-- test_config.py
    |-- test_deepseek_client.py
    |-- test_fake_llm_client.py
    |-- test_risk_analyzer.py
    |-- test_candidate_test_generator.py
    |-- test_pytest_runner.py
    |-- test_test_replanner.py
    |-- test_replanning_loop.py
    |-- test_console_approval_gate.py
    |-- test_candidate_applier.py
    |-- test_json_trace_writer.py
    |-- test_execution_trace.py
    |-- test_evaluation_harness.py
    `-- test_failure_recovery_scenarios.py
```

---

## Safety Boundaries

The current system is intentionally bounded.

It can:

```text
read staged Git changes
analyze risk
generate candidate tests
execute candidate tests temporarily
observe failures
replan
request human approval
write approved tests
```

It cannot autonomously:

```text
git add
git commit
git push
```

Important limitations:

- temporary-directory execution is not a complete OS sandbox
- network isolation is not currently guaranteed
- evaluation scenarios are small and controlled
- complex multi-file changes may require stronger reasoning
- generated tests still require human judgment
- malformed structured LLM output currently stops the workflow rather than
  automatically repairing the response

---

## Development Roadmap

```text
[x] Phase 0  - GitHub repository and initial README
[x] Phase 1  - Python project structure and environment
[x] Phase 2  - Staged Git diff reader
[x] Phase 3  - Offline Git reader tests
[x] Phase 4  - Agent state and LangGraph workflow
[x] Phase 5  - DeepSeek integration
[x] Phase 6  - Offline fake LLM provider
[x] Phase 7  - Risk and test-gap analysis
[x] Phase 8  - Candidate test generation
[x] Phase 9  - Isolated pytest execution
[x] Phase 10 - Bounded retry and replanning
[x] Phase 11 - Human approval gate
[x] Phase 12 - JSON execution traces
[x] Phase 13 - Evaluation harness and task set
[x] Phase 14 - Failure and recovery scenarios
[ ] Phase 15 - Cost and latency evaluation
[ ] Phase 16 - Final documentation and demonstration
```

---

## Current Status

The project currently demonstrates a complete bounded agent loop:

```text
Sense
Decide
Act
Observe
Replan
Human oversight
Safe stopping
Traceability
Evaluation
```

The next phase will measure API cost and latency using the real DeepSeek
provider while keeping those live results separate from the deterministic
offline evaluation.