# Architecture

## Updated design

Milo is not tied to one AI brand. It is a controlled web client for whichever engine the parent selects: ChatGPT or DeepSeek.

The parent blocks the official AI chat website(s) for the child's account. The child uses Milo instead.

```text
Parent blocks the official AI chat website(s)
              │
              ▼
Child browser -> Milo Web App -> Input Safety Check -> Chosen AI Engine
                                              │              │
Child browser <- Safe Final Answer <- Output Safety Check <- Draft Answer
```

## Components

### 1. Milo Web App (`src/app.py`)

A Streamlit web app that gives the child a simple chat interface. The child does not see the API key, system prompt, or parental policy — and Milo never states which underlying engine is answering.

### 2. Parent Controls

A sidebar (on the Parent Dashboard page) lets the parent pick the engine and the child's age band (8-10, 11-13, or 14-16, defaulting to the strictest tier). In a production version this would require parent authentication and would not be editable by the child.

### 3. Input Safety Check (`src/classifier.py`, `src/policy_engine.py`)

Before a message reaches the AI engine, it runs through, in order:

1. **Keyword bypass scan** — instant, no API call, catches obvious jailbreak phrasing.
2. **LLM jailbreak judge** — if the keyword scan finds nothing, a second call to the selected engine judges whether the message is a paraphrased attempt to bypass, disable, or manipulate parental controls. Falls back silently to keyword-only detection if unavailable or unparseable.
3. **Topic keywords + OpenAI moderation scoring** — self-harm, sexual, violent, drug, and weapon content are scored via OpenAI's free `omni-moderation-latest` endpoint, checked against thresholds that get stricter for younger age bands. Keyword hits still guarantee at least a REWRITE floor even when the raw text scores as harmless (e.g. an educational question that happens to mention a sensitive topic).
4. **Keyword-only check** — eating disorders and gambling, which have no equivalent moderation category.

### 4. Model Adapter (`src/model_adapter.py`)

Sends approved messages to the selected engine's API (`call_model`), calls OpenAI's moderation endpoint (`moderate`), and runs the jailbreak-judge prompt (`judge_bypass`). If no API key exists for the selected engine, `call_model` falls back to mock responses for demos; `moderate` and `judge_bypass` return `None` under the same condition, degrading their callers to keyword-only detection.

### 5. Output Safety Check

The draft answer from the AI engine is inspected before the child sees it, using the same moderation-and-keyword scoring as step 3 (the jailbreak judge is not re-run on output — it targets the child's own wording). Unsafe output is blocked or rewritten into age-appropriate language.

### 6. Parent Dashboard (`src/pages/1_Parent_Dashboard.py`)

PIN-gated page showing decision stats, a BLOCK/ESCALATE alert feed, the full safety telemetry log, and the engine/age-band controls.

## Key design decision

The child is not allowed to use the official AI chat websites directly. The system relies on parental website blocking plus a protected replacement interface that hides which engine is underneath it.
