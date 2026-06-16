# Day 14 - Lab 1: Content Moderation & Bias Evaluation

FinanceGuard AI lab for auditing the synthetic CreditLens loan-rejection workflow.

## What This Lab Does

- Generates a 3,000-row synthetic loan application dataset.
- Computes demographic parity by gender and region.
- Computes equalised odds style rejection metrics.
- Runs an 80% rule compliance check.
- Saves rejection-rate visualisations.
- Implements keyword moderation for discriminatory, PII, jailbreak, and financial misinformation prompts.
- Implements local semantic moderation with `HashingVectorizer`.
- Logs moderation trigger events.
- Optionally compares one prompt with the OpenAI Moderation API if `OPENAI_API_KEY` is valid.

## `.env`

The lab reads secrets from `day14/lab1/.env`:

```env
OPENAI_API_KEY=your_chatgpt_api_key_here
OPENAI_MODERATION_MODEL=omni-moderation-latest
```

`OPENAI_API_KEY` is optional for the core lab. It is only used for the optional OpenAI Moderation API smoke test.

## Install

From the repo root:

```powershell
pip install -r requirements.txt
```

## Run

From `day14/lab1`:

```powershell
python financeguard_bias_moderation_lab.py
```

## Outputs

Files are written to `day14/lab1/output`:

- `synthetic_loan_rejections.csv`
- `moderation_log.csv`
- `audit_summary.json`
- `bias_dashboard.png`
- `rejection_heatmap.png`
- `moderation_triggers.png`
