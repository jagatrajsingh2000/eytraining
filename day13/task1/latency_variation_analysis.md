# Latency Variation Analysis using BLEU, ROUGE and Faithfulness

## Main Observation

From the latency waterfall chart, the main cause of latency variation is the **Claude answer generation stage**, not embedding or Azure retrieval.

Embedding query time is small and mostly stable across all queries. Azure retrieval time is also small and does not vary much. The large latency differences are mainly caused by Claude generation time.

Queries like **Q3, Q6 and Q7** have high latency because Claude takes much longer to generate the final answer. Queries like **Q1 and Q2** have lower latency because Claude generation time is smaller.

## Metrics Used for Evaluation

To understand whether the extra generation time is useful, we evaluate answer quality using **BLEU**, **ROUGE**, and **Faithfulness**.

| Metric | What it checks | Meaning in latency analysis |
| --- | --- | --- |
| **BLEU** | Word and phrase overlap with the reference answer | Higher BLEU means the generated answer is closer to the expected answer |
| **ROUGE** | Recall-based overlap with the reference answer | Higher ROUGE means the answer covers more important points from the expected answer |
| **Faithfulness** | Whether the answer is supported by the retrieved context | Higher faithfulness means the answer is grounded and less likely to hallucinate |

## Metric-Based Interpretation

If a high-latency query also has **high BLEU**, **high ROUGE**, and **high Faithfulness**, then the extra latency is acceptable. It means Claude is taking more time but producing a better, more complete, and more grounded answer.

If a high-latency query has **low BLEU**, **low ROUGE**, or **low Faithfulness**, then the generation stage is inefficient. In that case, Claude is spending more time without improving answer quality.

So latency should not be judged only by response time. It should be compared with answer quality metrics.

## Final Conclusion

The root cause of latency variation is:

> **Claude generation time**, mainly affected by answer length, query complexity, retrieved context size, and reasoning required by the model.

Embedding and Azure retrieval contribute very little to the variation because their timings remain mostly stable.

The optimization should focus on:

- Reducing prompt and retrieved context size.
- Limiting unnecessary long output.
- Improving chunk retrieval quality.
- Sending only the most relevant context to the model.
- Avoiding prompts that force unnecessary reasoning or verbose answers.

Final decision:

> If high-latency answers have strong BLEU, ROUGE, and Faithfulness scores, the latency is justified. If those scores are weak, the generation stage must be optimized because it is adding cost and delay without improving answer quality.
