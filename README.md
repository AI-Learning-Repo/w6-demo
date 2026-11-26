# Agent-to-Agent interoperability in Colab

Two independent local seller services demonstrate A2A 1.0 with Python SDK 1.3.1. Burger uses CrewAI (11001); pizza uses LangGraph (11000). Both use fictional menus and simulated orders. Hosted Gemini or Groq inference requires an API key and may incur quota limits.

## Layout

- `remote_seller_agents/`: current services; Python 3.12 environments per seller.
- `remote_seller_agents_v0/`: historical A2A 0.2.6 servers; not used in the lab.
- `clients/`: existing A2A client module and smoke tests.
- `lab_utils.py`: notebook infrastructure helpers.

## Colab quick start

Clone repo, install `uv`, `google-genai`, `groq`, and `clients/requirements.txt` in the notebook environment. Add `GEMINI_API_KEY` and/or `GROQ_API_KEY` to Colab Secrets and grant notebook access. Never commit keys. In Python:

```python
import os, sys
from pathlib import Path
from google.colab import userdata
REPO = Path('/content/w6-demo')
sys.path.insert(0, str(REPO))
import lab_utils as lab
lab.configure(REPO, delay=20)
lab.create_environments()
for config in lab.AGENTS.values():
    lab.install_requirements(config['directory'])
os.environ['GROQ_API_KEY'] = userdata.get('GROQ_API_KEY')
cards = lab.switch_provider('groq', 'openai/gpt-oss-120b')
```

For Gemini, set `GEMINI_API_KEY` from Secrets and call `lab.switch_provider('gemini', 'gemini-3.5-flash')`. List models with the provider SDK before selecting; availability and quotas vary. GPT-OSS and Gemini passed seller tests in the instructor notebook; Qwen `qwen/qwen3.8-27b` passed direct connectivity only. Changing provider restarts both processes and clears in-memory state.

```bash
python clients/test_discovery.py
python clients/test_all.py --delay 20 --json
```
Run from the repository root. Discovery uses no LLM inference. Tests are sequential; delays reduce bursts but cannot guarantee quota compliance. Inspect logs on timeout. `lab.stop_all()` stops the services. The client needs no model key itself.


## Attribution

Adapted from the Google purchasing concierge A2A codelab starter:

- https://codelabs.developers.google.com/intro-a2a-purchasing-concierge
- https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter
- https://github.com/sajacaros/purchasing-concierge-a2a


Changes include local Colab deployment, Developer API/Groq support, modern A2A interfaces, and notebook helpers. 
