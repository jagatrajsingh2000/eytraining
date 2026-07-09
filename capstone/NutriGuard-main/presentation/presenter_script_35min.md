# NutriGuard AI Presenter Script - 35 Minutes

Target timing: about 32 minutes 45 seconds of presentation + 2 minutes 10 seconds Q&A.

Use this as a talk track, not a word-for-word script. If a slide feels crowded, say only the bold idea and move on.

## Slide 0 - NutriGuard AI
Time: 0:45

Hi everyone. Today I am presenting NutriGuard AI, a personalized nutrition guidance app that helps users understand how their meals interact with their health profile.

The core idea is simple: people do not just need calorie tracking. They need context-aware guidance that can catch risks like food and supplement interactions, and explain them in a way that is easy to act on.

## Slide 1 - Meet Priya
Time: 1:00

Let me introduce Priya, the main character in our story.

Priya is 28, vegetarian, and works a busy full-time job. Her latest reports show iron deficiency and low vitamin D, so she takes an iron tablet every morning.

Her doctor has told her to “watch your diet.” The advice is medically sensible, but it does not tell Priya what to eat for breakfast, when to take her supplement, or which everyday combinations may work against her treatment.

She searches through lab reports, diet charts, calorie apps, and food advice online. The information is everywhere, but none of it connects her medical context to the meal in front of her. This is Stage 1: Priya is confused, not because she lacks motivation, but because the guidance is not specific enough to act on.

## Slide 2 - The Invisible Problem
Time: 1:10

The next morning, Priya tries to do the right thing. She takes her iron tablet with breakfast and her usual cup of tea.

But the tannins in tea can interfere with iron absorption. At lunch, she has dahi rice; calcium close to iron can also compete with absorption. None of these foods looks unhealthy by itself. The problem appears only when we connect the food, supplement, health condition, and timing.

Priya cannot see that connection, and her calorie app cannot see it either. It may tell her how many calories were in breakfast, but not whether that breakfast supported the reason her doctor prescribed iron.

This is Stage 2: the invisible mistake. Priya is following generic advice while unknowingly reducing its benefit.

## Slide 3 - Onboarding in 60 Seconds
Time: 1:00

This is where Priya discovers NutriGuard.

She does not need to understand medical data structures or complete a long clinical form. She simply writes: “I have iron deficiency,” “I take an iron tablet in the morning,” and uploads or pastes the relevant lab report. She also selects that she is vegetarian and wants to reduce her deficiency.

Behind the screen, NutriGuard converts her natural language into consistent fields: iron deficiency, vitamin D deficiency, iron supplement, vegetarian diet, and her health goals.

For Priya, this takes about a minute. This is Stage 3: the experience becomes frictionless, while the system quietly builds the context needed for personalized reasoning.

## Slide 4 - Log a Meal in 10 Seconds
Time: 1:00

The next morning, Priya opens NutriGuard and types exactly what happened: “Breakfast: poha, tea, iron tablet.”

She does not scan barcodes, count calories, or search for every ingredient. In about ten seconds, the meal is saved and queued for analysis.

Now the system combines this meal with Priya’s profile and the rest of her day. The meal analyzer identifies the foods and supplement. The health-risk agent retrieves relevant nutrition guidance and checks timing and interactions. The report agent turns that analysis into language Priya can use.

The technical complexity stays in the background. Priya’s only task is to describe what she ate.

## Slide 5 - The Report That Changes Behavior
Time: 1:20

Priya then receives something her earlier tools never gave her: an explanation connected to her own day.

The report explains that her tea was too close to the iron tablet, that dahi may be better moved away from that absorption window, and that her breakfast could use more protein.

More importantly, it gives her simple actions: move tea to around 10 AM, add sprouts, paneer, or tofu for protein, and follow her doctor’s instructions for supplement timing and dosage.

NutriGuard does not diagnose Priya or replace her doctor. It translates the doctor’s broad guidance into practical, day-level choices while preserving a clear safety boundary.

This is Stage 5: clarity. Priya is no longer staring at disconnected reports and food myths. She knows what small change to make tomorrow.

## Slide 6 - The User Journey
Time: 0:50

If we step back, Priya’s journey has five stages.

She begins confused by generic guidance. She makes an invisible timing mistake. She describes her health and meals without friction. The AI connects her profile, timeline, and relevant evidence. Finally, she receives clear and safe actions.

The transformation is not from “unhealthy” to “healthy” in one day. It is from uncertainty to informed daily decisions, with very little added effort.

## Slide 7 - Core Message
Time: 0:50

Priya’s story captures the product’s core message: NutriGuard turns every meal into a personalized nutrition checkpoint.

It is proactive because it catches a pattern before it continues. It is personalized because the guidance depends on Priya’s deficiency, supplement, diet, and timing. And it is effortless because Priya only needs to describe her health and meals in ordinary language.

Priya remains in control, her doctor remains the medical authority, and NutriGuard bridges the gap between clinical guidance and everyday food choices.

## Slide 8 - Why NutriGuard AI Exists
Time: 1:10

NutriGuard exists because current tools usually fall into two categories.

Some apps are food journals, but they do not understand medical context. Other tools provide health information, but they are not connected to everyday meals.

NutriGuard sits between those two: daily meal tracking plus personalized safety reasoning.

## Slide 9 - Core System Specifications
Time: 1:10

At the system level, we designed around three specs.

First, event-driven microservices, so slow AI processing does not block the app.

Second, multi-agent reasoning, so meal analysis, risk checking, and report generation are separated.

Third, safety-first design, so the system gives nutrition support without crossing into diagnosis or dosage advice.

## Slide 10 - Key Design Decisions
Time: 1:40

This slide covers the deeper engineering patterns.

The outbox pattern gives reliable event delivery between the database and queue.

Graceful degradation means the system can fall back across providers or even rule-based logic.

The day-level timeline matters because risks often depend on timing across meals, not just one food entry.

For grounding, we use a lightweight local RAG layer. Nutrition guidance is stored as small, focused JSON knowledge entries with tags, source, evidence level, and a safety note. These entries act as our chunks.

The retriever builds a query from the meal, diet, goals, conditions, deficiencies, and supplements. It ranks chunks by keyword and tag overlap, then sends only the top results to the health-risk and report agents. This reduces irrelevant context and makes the result easier to trace than sending the entire knowledge base.

We also normalize health text, store operational metrics in the database, and enforce safety rules around the AI output.

## Slide 11 - Design Choices We Made
Time: 1:30

Here are the main technology choices and why we made them.

We used LangGraph because the AI flow is not one prompt. It is a multi-step workflow with state, retries, and separate responsibilities.

We used React instead of Streamlit because this needed to feel like a production app: routing, auth, responsive UI, and a better mobile experience.

We used Gemini plus OpenAI because we wanted cost-effective primary calls, but also a reliable fallback and evaluation path.

We chose Azure hosting because Static Web Apps and Container Apps gave us managed HTTPS, CI/CD, and simple deployment.

Serverless containers let us scale without managing servers, and Azure Service Bus decouples fast API requests from slower AI jobs.

## Slide 12 - AWS Kiro Rate Limiter Design
Time: 1:00

For rate limiting, we used AWS Kiro as a planning-first agentic IDE.

The point here is that we did not jump straight into code. We first generated requirements, design, and implementation tasks.

That helped us reason about edge cases like concurrent requests and database race conditions before production.

## Slide 13 - Detailed System Architecture
Time: 1:50

Here is the architecture from left to right.

React is the frontend. FastAPI is the backend gateway. Azure Service Bus carries work asynchronously. LangGraph runs the AI orchestration. PostgreSQL stores state, users, meals, reports, and metrics.

The main benefit is decoupling. The user can submit a meal quickly, while the AI work happens in the background.

The trade-off is eventual consistency. The frontend needs to poll or refresh for the final report.

## Slide 14 - LangGraph Agent Pipeline
Time: 1:50

The LangGraph pipeline has three main agents.

The meal analyzer extracts foods, ingredients, and nutrition properties.

The health risk agent compares that meal against the user's profile, supplements, deficiencies, and timing.

The report agent turns the technical analysis into an empathetic daily report.

This separation keeps the workflow easier to debug and easier to improve.

## Slide 15 - Live System Demonstration
Time: 2:30

Now I will show the live app.

The demo flow is simple: log a meal, run the agents, and get safety-aware guidance.

While demonstrating, call out three things:

First, the user experience stays simple. The user is not thinking about agents, queues, or models.

Second, the backend is doing the heavier reasoning asynchronously.

Third, the final output is designed to be actionable, not just informational.

If the live app is slow, explain that AI processing is asynchronous by design and move to the next slide.

## Slide 16 - CI/CD & Azure Deployment
Time: 1:20

The deployment pipeline uses GitHub Actions and Azure.

The frontend is deployed to Azure Static Web Apps. The backend and worker run as containerized services.

This gives a clean path from code changes to production without manual deployment steps.

## Slide 17 - Testing Strategy
Time: 2:30

Testing had to cover more than normal API behavior.

We tested backend endpoints, user and meal workflows, admin metrics, and notification behavior. For the RAG pipeline, we test retrieval separately from generation, because a fluent final answer can hide weak retrieval.

Our local evaluation dataset contains a question, the user and meal state, a reference answer, and the IDs of the chunks we expect to retrieve. This gives us deterministic retrieval metrics without needing an API key.

Recall at K asks: did the expected evidence appear in the top K chunks? Precision at K asks: how much of what we retrieved was actually relevant? Our targets are at least 80 percent recall and 60 percent precision.

We then optionally run RAGAS with an OpenAI judge. Context precision and context recall assess the retrieved evidence semantically, while faithfulness checks whether the generated answer is supported by that evidence. Our faithfulness target is at least 90 percent, and safety must be 100 percent.

Chunking directly affects these numbers. Large chunks preserve context but introduce unrelated text, lowering precision and increasing tokens. Very small chunks improve focus but can split a safety rule from its explanation and hurt recall. In this version, each curated JSON knowledge entry is one focused semantic chunk; we do not use arbitrary fixed-character splitting or overlap. The next step is to split any broad entries, improve tags, and compare the metrics before and after each change.

## Slide 18 - Load Testing & Observability
Time: 2:10

For production readiness, we added load testing and observability. In an asynchronous multi-agent system, a single HTTP status is not enough to tell us whether the work actually completed.

Every meal workflow carries a correlation ID based on the meal-log ID. That lets us follow one request across FastAPI ingress, the Service Bus event, the LangGraph worker, each agent, and the final report.

We record both technical and AI-specific signals: API and agent latency, success or failure, provider and fallback usage, token counts, queue progress, report completion, and published RAG evaluation results. P95 matters more than averages when diagnosing slow outliers.

This gives us three layers of observability: logs explain what happened, metrics show whether behavior is trending, and the correlation ID connects the distributed steps. The dashboard then makes those signals visible without requiring direct access to cloud logs.

The goal is not only to detect that the system failed. It is to distinguish whether the problem came from retrieval, an LLM provider, the queue, a specific agent, or the API.

## Slide 19 - Agent Latency, Load Test & Token Costs
Time: 1:20

This slide connects performance with cost.

Agent-based systems can be powerful, but every model call has latency and cost.

So we measured the pipeline, tracked token usage, and designed fallbacks. This helps us keep the product practical, not just impressive.

## Slide 20 - Live Dashboard & Analytics Trends
Time: 2:30

The dashboard gives us visibility into the system.

On the RAG chart, Recall at K rises as we retrieve more chunks. That is expected: a larger K makes it more likely that the required evidence is present. But increasing K forever is not the answer, because extra chunks can lower precision, increase token cost, and distract the model. We choose K by balancing recall, precision, latency, and cost rather than optimizing one metric alone.

Local retrieval metrics and RAGAS metrics serve different purposes. The local checks are fast, deterministic, and compare exact expected chunk IDs. RAGAS uses an LLM judge to assess semantic relevance and faithfulness. We keep both because an exact-ID test can be strict, while an LLM judge can recognize useful equivalent context.

The rest of the dashboard shows meal volume, report completion, provider usage, API latency, agent latency, and token use. If report completion falls below meal submission, or fallback usage suddenly rises, we have an operational signal to investigate.

For a health-related app, this matters because invisible failures are risky. If the AI pipeline slows down or reports fail, the team needs to know quickly.

## Slide 21 - Production Challenges
Time: 1:30

These are the practical issues we hit in production.

Gemini free-tier limits required fallback and quota planning.

Service Bus lock expiry required lock renewal for slower AI calls.

Internal API keys and CORS had to be consistent across services and environments.

The key lesson is that AI app deployment is not only about prompts. It is also about reliability, configuration, and operations.

## Slide 22 - Project Stats & Open Source Stack
Time: 0:50

To close the technical story, this is the stack summary.

The project combines React, FastAPI, LangGraph, PostgreSQL, Docker, and Azure.

The important point is that this is not just a prototype screen. It is a deployable, observable, multi-service application.

## Slide 23 - Q&A
Time: 2:10

Thank you. I would love to take questions.

Good areas to ask about are patient safety, agent orchestration, model fallback, Azure deployment, or how we would improve this for a real clinical environment.

If there are no questions, close with:

The main takeaway is that NutriGuard AI shows how meal tracking can evolve from passive logging into proactive, personalized nutrition guidance.

## Timing Checkpoints

- Slide 7 should finish around 7:55.
- Slide 11 should finish around 13:25.
- Live demo should start around 18:05 and end around 20:35.
- Slide 20 should finish around 30:25.
- Q&A should start around 32:45.
- Full session should finish by 35:00.

## Likely Instructor Questions

**Why not send the whole knowledge base to the model?**  
It would add irrelevant context, increase token cost and latency, and make grounding harder to inspect. Retrieval limits the prompt to the most relevant evidence.

**How did you choose chunk size and overlap?**  
The current knowledge base is curated JSON, so each focused entry is already a semantic chunk. We do not use fixed character sizes or overlap yet. Broad entries should be split when evaluation shows low precision; overly narrow entries should be combined when recall or meaning suffers.

**Why use both local metrics and RAGAS?**  
Local Recall@K and Precision@K are deterministic and inexpensive. RAGAS adds semantic judgment for context relevance and answer faithfulness. Together they reveal both retrieval correctness and generation grounding.

**What would you improve next in RAG?**  
Add more evaluation cases, refine tags, split broad chunks, tune top K, and compare the current keyword retriever against embedding-based vector retrieval.

**What makes the system observable?**  
A shared correlation ID traces each meal through the API, queue, worker, agents, and report. We also persist latency, failures, provider fallback, tokens, report completion, and RAG quality metrics for dashboard monitoring.
