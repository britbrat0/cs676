#**TinyTroupe Installation and Usage**

## **Introduction**

TinyTroupe is a Python library used for simulating multi-agent, persona-driven interactions using underlying LLMs. It emphasizes detailed persona definitions (age, background, goals, personality traits), environment constraints, and experiment-driven configurations.

Details can be found at https://github.com/microsoft/tinytroupe?tab=readme-ov-file

## **Performance Considerations and System Requirements**

Python 3.1 or higher

Access to Azure OpenAI Service or Open AI GPT-4 APIs


At least 4 GB of available RAM, 8-16 GB is optimal.

Modern multi-core CPU. Fast network, low-latency link to API endpoint is optimal.


## **Installation**
1. **Create a clean Python environment**



```python
conda create -n tinytroupe python=3.10

conda activate tinytroupe
```

2. **Install TinyTroupe**


```python
	pip install git+https://github.com/microsoft/TinyTroupe.git@main
```

Alternatively, clone the repo and install locally.


```python
git clone https://github.com/microsoft/TinyTroupe.git

cd TinyTroupe

pip install -e .
```

	Dependencies are included in pyproject.toml in the repository.

3. **Configure credentials and settings**


```python
# If using OpenAI:

export OPENAI_API_KEY="sk-..."

# Or if using Azure OpenAI:

export AZURE_OPENAI_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://<your-endpoint>.openai.azure.com/"
```

Default API type, model name, caching, etc. are set in config.ini.
Copy or adapt the file into your working directory.
Gpt-4o-mini is the default model.


```python
# Example

[api]
type = openai
model = gpt-4o-mini
temperature = 0.7

[caching]
CACHE_API_CALLS = True

[logging]
level = INFO
```

4. **Verify installation**



```python
import os
import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
```

If these import without error, the install is sane.

Example scripts or notebooks in the examples/ folder of the GitHub repo can be run to check installation. These include customer interviews, brainstorming sessions, ad evaluation, etc.

5. **Run example simulations**


```python
from tinytroupe.extraction.results_extractor import ResultsExtractor

# Create two agents
alice = TinyPerson("Alice")
alice.define("age", 30)
alice.define("occupation", "Engineer")

bob = TinyPerson("Bob")
bob.define("age", 35)
bob.define("occupation", "Designer")

# Create a simple world
world = TinyWorld("ChatRoom", [alice, bob])
world.make_everyone_accessible()

alice.listen("Hi Bob! How are you today?")
world.run(3)

# Extract summarized results
extractor = ResultsExtractor()
summary = extractor.extract_results_from_world(
    world,
    extraction_objective="Summarize the conversation from each person's point of view",
    verbose=False
)

print(summary)
```

If this runs and emits output (dialogue, summary), the setup worked.

Because TinyTroupe is early-stage, occasional breaking changes or quirks can be expected; always refer to the upstream repo for updates.

##**Common Installation Issues and Troubleshooting Guidance**

**Missing build dependencies (macOS / Linux):**

If any dependency (e.g. `wheel`, `setuptools`, or C extensions) fails to compile, install system dev tools (`build-essential`, `libssl-dev`, etc.) or update `pip`, `setuptools`, `wheel`:


```python
pip install --upgrade pip setuptools wheel
```

**Python version mismatch (macOS / Linux):**

Ensure you are using the environment Python (not a system Python). Use `which python` or `which pip` to verify.

**Concurrency limits / file descriptors (macOS / Linux):**

If running many agents in parallel, you may hit OS limits. Increase `ulimit -n` etc.

**Conda path issues (Windows):**

Sometimes `conda` is not found in PATH when opening new cmd / PowerShell windows. You may need to run `conda init` and reopen terminal.

**Environment variable persistence (Windows):**

Use `setx OPENAI_API_KEY <key>` or set via “System Properties → Environment Variables” so it persists across sessions.

**Line endings/path separators (Windows):**

Be careful when copying config paths or repository paths, especially in `config.ini`.

**401/“unauthorized” error:**

Verify your API key has sufficient permissions and is spelled right.

**Endpoint URL incorrect (Azure):**

Make sure `AZURE_OPENAI_ENDPOINT` is the full URL (including `https://` and trailing slash).

**Network/proxy issues:**

If behind a corporate proxy or firewall, ensure Python HTTP requests can reach the OpenAI endpoint (set `HTTPS_PROXY`, `HTTP_PROXY` if needed).

**Rate limiting:**

If you hit “429 Too Many Requests,” reduce simulation parallelism or add retry/backoff logic.

**Version mismatch/stale cache**

If after updating the TinyTroupe repo your old installation persists, you may inadvertently be using a cached version. Try:


```python
pip uninstall tinytroupe
pip install --no-cache-dir git+https://github.com/microsoft/TinyTroupe.git@main
```

**Debugging logging**

Enable more verbose logging in `config.ini`:


```python
[logging]
level = DEBUG
```

or programmatically:


```python
import logging
logging.getLogger("tinytroupe").setLevel(logging.DEBUG)
```

Inspect logs of API requests, prompt contents, errors, etc.

##**Configuration Options**

**Persona/Agent configuration**

Use `TinyPerson.define(...)` to annotate attributes (name, age, occupation, traits, goals, routines, etc.). The more detailed your persona, the more consistent the agent behavior is likely to be.

Define personas via JSON specification files and load them programmatically (e.g. via `tinytroupe.examples` or custom loader).

Use `TinyPersonFactory` to generate personas automatically from short prompts or demographic distributions.

**World/Environment settings**

`TinyWorld` objects are containers for agents.

Call `make_everyone_accessible()` to make any agent able to converse with any other.

Use `world.run(n_steps)` to execute the simulation for a fixed number of “rounds” or turns.

Agents take turns listening, thinking, and acting depending on stimuli and environmental cues. Call agent methods like `listen(...)` or `listen_and_act(...)` to inject external stimuli (e.g. from a human user).

**Prompt/LLM settings & caching**

The `config.ini` can set default model, temperature, API type, and caching.

If the simulation repeatedly sends identical sub-prompts, enabling caching (or using TinyTroupe’s built-in caching) can drastically cut down redundant API calls.

Parameters can be overriden on a per-agent or per-call basis (if the API allows) to fine-tune prompt behavior.

For large simulations, consider prompt template optimization: avoid extremely long context, reuse prompt fragments, and structure them efficiently to reduce token usage.

**Extraction, metrics, and reporting**

Use `default_extractor` to extract structured summaries or analysis from the simulation world.

Define "extraction objectives" (e.g. “summarize each agent’s internal view”, or “compare opinions”) and get output in machine-readable form.

Use `ResultsReducer` (if available) or create custom reducers to aggregate metrics across many simulation runs.

Logging and checkpointing: periodically persist the simulation state or partial dialogues for debugging, inspection, or recovery.

##**References**

https://github.com/microsoft/TinyTroupe

https://arxiv.org/abs/2507.09788v1

https://www.piwheels.org/project/tinytroupe/


```python

```
