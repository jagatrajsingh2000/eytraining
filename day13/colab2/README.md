# 🔁 Lab 2 — Prompt Feedback Loop with Automatic Iteration
**Day 13 · Module 5 · FinSight AI Credit Risk Scenario**

This directory contains the automated evaluation pipeline to test, triage, and systematically improve LLM prompt performance for generating credit risk memos. 

---

## 🎯 Learning Objectives
1. **Instrument LLM calls** with structured logging to a persistent SQLite database.
2. **Build an automated quality probe suite** to detect hallucinations, missing sections, and length violations at scale.
3. **Triage failure patterns** using frequency analysis and Matplotlib visualizations.
4. **Implement advanced prompts** using Chain-of-Thought (CoT) and strict compliance guardrails.
5. **Verify improvements** using quantitative A/B testing and Weights & Biases / LangSmith tracing.

---

## 📂 Project Structure
* `colab2.py`: The main execution script running the simulation, probes, triage, and A/B comparison.
* `finsight_logs.db`: SQLite database storing request telemetry and quality flags.
* `failure_analysis.png`: Chart mapping baseline failure categories and length distributions.
* `before_after_comparison.png`: Comparison dashboard showing performance gains.

---

## ⚙️ Configuration & Environment Setup

Copy your API credentials to the `.env` file located in the repository root:

```ini
# Groq API Key (gsk_...) or xAI API Key (xai-...)
XAI_API_KEY=gsk_your_key_here

# OpenAI API Key (Optional)
OPENAI_API_KEY=sk-proj-your_key_here

# LangSmith Tracing (Optional)
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_PROJECT=finsight-feedback-loop

# Weights & Biases (Optional)
WANDB_API_KEY=your_wandb_key_here
```

### 🚀 Hybrid API Router
The script detects the type of API key configured and routes requests automatically:
* **Groq API** (`gsk_...`): Uses `llama-3.3-70b-versatile` over Groq's high-speed inference endpoints.
* **xAI API** (`xai-...`): Uses `grok-2-latest` over xAI endpoints.
* **Offline Mock Mode**: If no valid credentials are provided, the script runs a local mock generator with temperature-dependent error rates, allowing you to test the entire logging and visualization pipeline offline.

---

## 🏃 Running the Script

Ensure your virtual environment is activated, then choose an execution mode:

### 1. Standard A/B Evaluation
Runs the baseline `v1.0` and improved `v2.0` prompts side-by-side on 10 borrower profiles, logs telemetry to SQLite, prints performance tables, saves local charts, and uploads runs to W&B:
```bash
python colab2.py
```

### 2. Custom Temperature Selection
Runs the evaluation with a customized generation temperature:
```bash
python colab2.py --temperature 0.3
```

### 3. W&B Sweep Mode
Evaluates only the improved `v2.0` prompt at the specified temperature and reports performance metrics directly to Weights & Biases (skipping local plots for faster sweep steps):
```bash
python colab2.py --sweep --temperature 0.2
```

---

## 🧹 Running a W&B Hyperparameter Sweep

To automatically discover the optimal generation temperature for minimizing hallucinations under Llama 3.3, you can initialize a sweep:

1. Create a `sweep.yaml` configuration:
   ```yaml
   program: day13/colab2/colab2.py
   method: grid
   metric:
     name: hallucination_rate
     goal: minimize
   parameters:
     temperature:
       values: [0.0, 0.2, 0.5, 0.7, 1.0]
     sweep:
       value: true
   ```
2. Initialize the sweep in W&B:
   ```bash
   wandb sweep sweep.yaml
   ```
3. Run the sweep agent using the generated Sweep ID:
   ```bash
   wandb agent <sweep_id>
   ```

---

## 📊 Evaluation Probes (Quality Rules)
* **Numeric Hallucinations**: Validates all numbers in the output against the source borrower data to ensure the LLM has not invented financial data.
* **Missing Sections**: Confirms the presence of `BORROWER OVERVIEW`, `KEY FINANCIAL METRICS`, `RISK ASSESSMENT`, and `RECOMMENDATION` headings.
* **Length Violations**: Flags any credit memo that lies outside the target 100–350 word range.
