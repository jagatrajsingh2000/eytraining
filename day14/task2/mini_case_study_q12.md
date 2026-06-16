# Q12. Mini Case Study

## Question

A logistics company processes 10,000 customer support emails daily. They want to:

1. Automatically classify each email into a category
2. Retrieve relevant policy documents to generate a draft reply
3. Escalate complex cases to a human agent via a ticketing API

Which framework(s) would you recommend and why? Outline a high-level architecture in 4-6 bullet points.

## Answer

### Framework Chosen

`LangChain` / `LangGraph` + `LlamaIndex`

### Why These Frameworks

- `LangChain` or `LangGraph` is a strong fit for workflow orchestration, classification, tool calling, branching logic, and external API integration.
- `LlamaIndex` is a strong fit for document ingestion, indexing, retrieval, and RAG over policy documents.
- Together they support high-volume support automation with clear separation between orchestration and retrieval.

### High-Level Architecture

- Ingest 10,000 daily customer emails through an email API or message queue such as Kafka or Azure Service Bus.
- Use `LangChain` / `LangGraph` to classify each email into categories such as refund, shipment delay, damaged package, address change, or complaint.
- Use `LlamaIndex` to index and retrieve the most relevant policy documents from a vector database using RAG.
- Pass the retrieved policy context and customer email into an LLM to generate a grounded draft reply.
- Use `LangGraph` decision logic to evaluate confidence, complexity, sentiment, or exception conditions.
- If the case is complex or low-confidence, call the ticketing API and escalate it to a human support agent.

### Justification

`LlamaIndex` is best suited for document indexing and retrieval, while `LangChain` / `LangGraph` is best suited for workflow orchestration, routing, classification, tool use, and API-based escalation. This combination makes the system scalable, automated, and practical for high-volume customer support operations.
