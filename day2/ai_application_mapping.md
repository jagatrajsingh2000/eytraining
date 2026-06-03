# AI Application Mapping

| EY Application | Model Type | Primary Metric | Why this metric? |
|---|---|---|---|
| Anomaly detection in invoices | Classification model | **Recall** | Missing fraud/anomalies is costly, so we should catch maximum suspicious cases. |
| Spam classification in audit emails | Classification model / NLP | **Precision** | False spam detection may hide important audit emails. |
| Predicting deal close probability | Regression model | **RMSE / MAE** | Measures prediction error for probability or forecast values. |
| Summarising 100-page contracts | Generative AI / LLM | **Human evaluation** | Need to check summary quality, completeness, and correctness. |
| Translating audit reports | LLM | **BLEU score** | Measures translation quality against reference text. |
| Flagging revenue forecasting errors | Regression + anomaly detection | **RMSE** | Large forecasting errors should be penalized strongly. |
