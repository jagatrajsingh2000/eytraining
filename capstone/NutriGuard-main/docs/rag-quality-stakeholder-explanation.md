# RAG Quality Metrics: Stakeholder Explanation

This document explains the RAG quality dashboard in NutriGuard in business-friendly language.

RAG means Retrieval Augmented Generation. In NutriGuard, it means the AI does not answer only from the model's memory. It first retrieves relevant nutrition guidance from our local knowledge base, then uses that retrieved context while preparing meal recommendations.

## Why This Matters

NutriGuard gives nutrition suggestions based on:

- user profile
- health goals
- deficiencies
- supplements
- meal timing
- RAG knowledge base
- LLM reasoning

For a health-adjacent product, we need to know two things:

1. Did the system retrieve the right information?
2. Did the final answer stay grounded in that information?

The RAG quality dashboard helps answer those questions.

## Current Dashboard Summary

The current dashboard shows:

```text
Average retrieval hit rate: 100%
Cases passed: 4/4
Context recall: 100%
Context precision: 24%
Faithfulness: 96%
RAGAS context precision: 83%
RAGAS context recall: 62%
Judge: OpenAI
```

Simple interpretation:

```text
The retriever is good at finding the right information.
The system is also bringing some extra context.
The generated answers are mostly grounded and not heavily hallucinated.
```

## What We Are Evaluating

We currently evaluate 4 sample RAG scenarios:

```text
protein_veg_breakfast
iron_tea_timing
fat_loss_satiety
ayurveda_milk_fruit
```

These represent important NutriGuard use cases:

- vegetarian protein improvement
- iron deficiency and tea timing
- fat loss and satiety
- traditional Ayurveda food-combination guidance

Each test asks a question, runs retrieval, checks which knowledge documents came back, and optionally uses an LLM judge to score quality.

## Metric 1: Average Retrieval Hit Rate

Current value:

```text
100%
```

Meaning:

The retriever found at least one expected relevant knowledge item for every test case.

Example:

```text
Question:
What should a vegetarian user add to poha breakfast for better protein?

Expected:
Vegetarian protein guidance

Retrieved:
Vegetarian protein guidance

Result:
Hit
```

Why it matters:

This tells us the system is not missing the main knowledge source for each test.

Stakeholder interpretation:

```text
Good. The system is reliably finding the key knowledge document in our current test set.
```

## Metric 2: Cases Passed

Current value:

```text
4/4
```

Meaning:

All 4 evaluation examples passed the local retrieval check.

Why it matters:

This gives a simple pass/fail view for demo and quality tracking.

Stakeholder interpretation:

```text
Good for the current small test suite, but the test suite should grow before production claims.
```

## Metric 3: Context Recall

Current value:

```text
100%
```

Meaning:

Recall asks:

```text
Did we retrieve all the important context we expected?
```

Example:

```text
Expected documents:
A, B

Retrieved documents:
A, B, C, D

Recall:
2 expected found / 2 expected = 100%
```

Why it matters:

High recall means important information is not being missed.

This is especially important for NutriGuard because missing relevant context can lead to incomplete recommendations, for example missing iron and tea timing guidance for a user with iron deficiency.

Stakeholder interpretation:

```text
Very good. The system is finding the expected important context in current tests.
```

## Metric 4: Context Precision

Current value:

```text
24%
```

Meaning:

Precision asks:

```text
Out of all retrieved context, how much was actually relevant?
```

Example:

```text
Expected document:
A

Retrieved documents:
A, B, C, D, E

Recall:
100%, because A was found

Precision:
Low, because B, C, D, E were extra
```

Why it matters:

Low precision means the AI may receive too much extra information. This can make prompts larger, increase token usage, and sometimes dilute answer quality.

Stakeholder interpretation:

```text
The system finds the right information, but it also retrieves extra context.
This is acceptable for an early version, but precision should improve as the knowledge base grows.
```

## Metric 5: Faithfulness

Current value:

```text
96%
```

Meaning:

Faithfulness asks:

```text
Is the generated answer supported by the retrieved context?
```

High faithfulness means the answer mostly stays grounded in retrieved knowledge and does not invent unsupported claims.

Why it matters:

For health-adjacent recommendations, hallucination risk must be controlled. Faithfulness is one of the most important quality metrics.

Stakeholder interpretation:

```text
Strong result. The model is mostly using the provided context instead of making unsupported claims.
```

## Metric 6: RAGAS Context Precision

Current value:

```text
83%
```

Meaning:

This is an LLM-judge version of context precision.

It asks:

```text
Were the retrieved chunks useful for answering the question?
```

Why it differs from local precision:

Our local precision is strict and based on expected document matching.

RAGAS context precision is semantic. OpenAI judges whether retrieved context was useful, even if it was not an exact expected document.

Stakeholder interpretation:

```text
Good. Although strict local precision is low, the LLM judge thinks much of the retrieved context is still useful.
```

## Metric 7: RAGAS Context Recall

Current value:

```text
62%
```

Meaning:

This is an LLM-judge version of recall.

It asks:

```text
Did the retrieved context contain enough information to fully support the reference answer?
```

Why it matters:

This can reveal that our knowledge base or retrieved chunks do not fully cover what the ideal answer should say.

Stakeholder interpretation:

```text
Needs improvement. The system retrieves the main documents, but the retrieved context may not fully cover every part of the ideal answer.
```

## Why Local Metrics And RAGAS Metrics Differ

The dashboard shows both local metrics and RAGAS metrics because they answer different questions.

Local metrics:

- deterministic
- simple
- fast
- based on expected document IDs or tags
- useful for regression checks

RAGAS metrics:

- judged semantically by an LLM
- better at understanding meaning
- useful for answer quality
- may vary depending on judge model and prompt

Example difference:

```text
Local precision: 24%
RAGAS context precision: 83%
```

This means:

```text
Strict matching says we retrieved extra documents.
The LLM judge says many of those extra documents were still useful.
```

## Per-Case Results

### protein_veg_breakfast

Question:

```text
What should a vegetarian user add to poha breakfast for better protein?
```

Current result:

```text
Recall: 100%
Precision: 40%
```

Meaning:

The system found the relevant protein guidance, but also retrieved extra context.

### iron_tea_timing

Question:

```text
What should a user with iron deficiency know about tea near meals?
```

Current result:

```text
Recall: 100%
Precision: 20%
```

Meaning:

The important iron and tea guidance was found, but the retrieval included extra information.

### fat_loss_satiety

Question:

```text
What should a fat-loss meal recommendation prioritize?
```

Current result:

```text
Recall: 100%
Precision: 20%
```

Meaning:

The system found the right fat-loss/satiety context but retrieved additional less-specific context.

### ayurveda_milk_fruit

Question:

```text
How should Ayurveda combination guidance be presented for milk and fruit?
```

Current result:

```text
Recall: 100%
Precision: 17%
```

Meaning:

The system found the expected Ayurveda context but retrieved other context too.

Important note:

Ayurveda content is labeled as traditional guidance, not clinical evidence. The report should present it carefully as optional traditional context.

## Overall Quality Interpretation

Current system behavior:

```text
High recall
Low strict precision
High faithfulness
Moderate RAGAS recall
Good RAGAS precision
```

Business interpretation:

```text
NutriGuard is good at finding important knowledge.
It is not yet optimized for retrieving only the most relevant knowledge.
The generated answers are mostly grounded in context.
The next quality improvement should focus on reducing retrieval noise.
```

## Current Strengths

- Important context is not missed in current tests.
- The system supports profile-aware and goal-aware recommendations.
- Safety-sensitive cases like iron and tea timing are retrievable.
- The model is mostly faithful to retrieved context.
- RAG quality is visible in the admin dashboard.

## Current Limitations

- Test set is small.
- Precision needs improvement.
- Some retrieved context is extra/noisy.
- RAGAS metrics depend on an LLM judge.
- Ayurveda guidance must be carefully labeled and not treated as clinical advice.

## Recommended Improvements

### 1. Improve Knowledge Tags

Add clearer tags to knowledge base entries.

Example:

```text
protein
vegetarian
breakfast
iron_absorption
tea_timing
fat_loss
satiety
traditional_ayurveda
```

### 2. Reduce `top_k`

If the retriever returns too many chunks, reduce the number of retrieved documents.

This can improve precision and reduce token cost.

### 3. Split Large Chunks

Make each knowledge entry smaller and more focused.

Good chunk:

```text
Vegetarian protein additions for breakfast
```

Less ideal chunk:

```text
All vegetarian nutrition guidance
```

### 4. Add More Evaluation Cases

Add cases for:

- diabetes-friendly meal timing
- vitamin D and calcium
- muscle gain protein targets
- energy improvement
- late dinner timing
- supplement and meal gap checks

### 5. Track RAG Over Time

Keep publishing RAGAS results after knowledge base changes.

Dashboard should show whether quality improves or drops.

## Stakeholder Talking Points

Use this summary in demos:

```text
We evaluate whether NutriGuard retrieves the right nutrition context before generating advice.
Current recall is strong, meaning important context is being found.
Faithfulness is high, meaning the AI is mostly grounded in retrieved knowledge.
Precision is the main improvement area because the system retrieves some extra context.
This is expected in an early RAG system, and we already know the next steps: better tags, smaller chunks, and more evaluation cases.
```

## Bottom Line

The current RAG quality result is good for a demo-stage product.

It shows:

- strong retrieval coverage
- strong answer grounding
- visible quality metrics
- clear path for improvement

The main next step is precision improvement, not recall recovery.
