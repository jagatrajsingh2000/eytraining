function MetricCard({ label, value, detail }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <p>{detail}</p>}
    </article>
  )
}

function DailySeries({ title, items = [] }) {
  return (
    <section className="metric-panel">
      <h3>{title}</h3>
      <div className="daily-series">
        {items.map((item) => (
          <div className="daily-series-row" key={item.date}>
            <span>{item.date}</span>
            <b>{item.count}</b>
          </div>
        ))}
      </div>
    </section>
  )
}

function formatPercent(value) {
  return `${Math.round((value || 0) * 100)}%`
}

function formatOptionalPercent(value) {
  if (typeof value !== 'number') {
    return 'Not run'
  }
  return formatPercent(value)
}

function formatDateTime(value) {
  if (!value) {
    return 'Not published yet'
  }
  return new Date(value).toLocaleString()
}

function formatUsd(value) {
  return `$${Number(value || 0).toFixed(6)}`
}

export default function AdminPage({
  metrics,
  loadAdminMetrics,
  loading,
  adminStartDate,
  setAdminStartDate,
  adminEndDate,
  setAdminEndDate,
}) {
  const feedback = metrics?.feedback || {}
  const reports = metrics?.reports || {}
  const notifications = metrics?.notifications || {}
  const gemini = metrics?.gemini || {}
  const llmFallbacks = metrics?.llm_fallbacks || {}
  const apiLatency = metrics?.api_latency || {}
  const agentLatency = metrics?.agent_latency || {}
  const tokenCost = metrics?.token_cost || {}
  const loadTest = metrics?.load_test?.latest
  const ragEval = metrics?.rag_eval?.latest
  const retrievalMetrics = ragEval?.metrics?.retrieval_metrics || {}
  const ragasMetrics = ragEval?.metrics?.ragas_metrics || {}

  return (
    <section className="panel page-panel admin-page">
      <div className="report-head">
        <div>
          <span className="eyebrow">Observability</span>
          <h2>Admin Metrics</h2>
          <p className="muted">Simple DB-backed product metrics for demo monitoring.</p>
        </div>
        <div className="admin-filter-bar">
          <label>
            Start
            <input type="date" value={adminStartDate} onChange={(event) => setAdminStartDate(event.target.value)} />
          </label>
          <label>
            End
            <input type="date" value={adminEndDate} onChange={(event) => setAdminEndDate(event.target.value)} />
          </label>
          <button onClick={loadAdminMetrics} disabled={loading}>{loading ? 'Loading...' : 'Apply'}</button>
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard label="Meals submitted" value={metrics?.meals?.total ?? 0} />
        <MetricCard label="Reports completed" value={reports.completed_total ?? 0} />
        <MetricCard label="Failed reports" value={reports.failed_total ?? 0} />
        <MetricCard label="Avg processing" value={`${reports.average_processing_seconds ?? 0}s`} />
        <MetricCard label="Feedback liked" value={feedback.liked ?? 0} />
        <MetricCard label="Feedback disliked" value={feedback.disliked ?? 0} />
        <MetricCard label="Missed meal nudges" value={notifications.missed_meal_total ?? 0} />
        <MetricCard label="Unread notifications" value={notifications.unread_total ?? 0} />
        <MetricCard label="Gemini fallbacks" value={llmFallbacks.gemini_fallback_total ?? gemini.fallback_total ?? 0} />
        <MetricCard label="OpenAI answers" value={llmFallbacks.openai_answer_total ?? 0} />
        <MetricCard label="OpenAI fallbacks" value={llmFallbacks.openai_fallback_total ?? 0} />
        <MetricCard label="Rule fallbacks" value={llmFallbacks.rule_fallback_total ?? 0} />
        <MetricCard label="API requests" value={apiLatency.total_requests ?? 0} />
        <MetricCard label="Avg API latency" value={`${apiLatency.average_ms ?? 0}ms`} />
        <MetricCard label="P95 API latency" value={`${apiLatency.p95_ms ?? 0}ms`} />
        <MetricCard label="Slowest API" value={`${apiLatency.max_ms ?? 0}ms`} />
        <MetricCard label="Agent runs" value={agentLatency.total_runs ?? 0} />
        <MetricCard label="Avg agent latency" value={`${agentLatency.average_ms ?? 0}ms`} />
        <MetricCard label="P95 agent latency" value={`${agentLatency.p95_ms ?? 0}ms`} />
        <MetricCard label="Slowest agent" value={`${agentLatency.max_ms ?? 0}ms`} />
        <MetricCard label="LLM calls" value={tokenCost.calls ?? 0} />
        <MetricCard label="LLM tokens" value={tokenCost.total_tokens ?? 0} detail={`${tokenCost.input_tokens ?? 0} in / ${tokenCost.output_tokens ?? 0} out`} />
        <MetricCard label="Estimated LLM cost" value={formatUsd(tokenCost.estimated_cost_usd)} />
        <MetricCard
          label="Latest load p95"
          value={loadTest ? `${loadTest.p95_ms ?? 0}ms` : 'No run'}
          detail={loadTest ? `${loadTest.requests ?? 0} requests, ${loadTest.failed ?? 0} failed` : 'Publish a load test result'}
        />
        <MetricCard
          label="RAG hit rate"
          value={formatPercent(ragEval?.average_hit_rate)}
          detail={ragEval ? `${ragEval.passed_cases}/${ragEval.total_cases} eval cases passed` : 'No eval published yet'}
        />
      </div>

      <div className="metric-panels">
        <DailySeries title="Meals submitted per day" items={metrics?.meals?.submitted_per_day} />
        <DailySeries title="Reports completed per day" items={reports.completed_per_day} />
        <section className="metric-panel">
          <h3>Feedback by section</h3>
          <div className="feedback-metrics">
            {Object.entries(feedback.by_category || {}).map(([category, counts]) => (
              <p key={category}>
                <b>{category.replace('_', ' ')}</b>
                <span>Liked {counts.liked || 0}</span>
                <span>Disliked {counts.disliked || 0}</span>
              </p>
            ))}
            {!Object.keys(feedback.by_category || {}).length && <p className="muted">No feedback yet.</p>}
          </div>
        </section>
        <section className="metric-panel">
          <h3>LLM fallback by agent</h3>
          <div className="feedback-metrics">
            {Object.entries(llmFallbacks.by_agent || {}).map(([agent, counts]) => (
              <p key={agent}>
                <b>{agent.replace('_', ' ')}</b>
                <span>Gemini fallback {counts.gemini_fallback || 0}</span>
                <span>OpenAI answer {counts.openai_answer || 0}</span>
                <span>OpenAI fallback {counts.openai_fallback || 0}</span>
                <span>Rule fallback {counts.rule_fallback || 0}</span>
              </p>
            ))}
            {!Object.keys(llmFallbacks.by_agent || {}).length && <p className="muted">No LLM fallbacks recorded.</p>}
          </div>
        </section>
        <section className="metric-panel wide-metric-panel">
          <h3>RAGAS / RAG quality</h3>
          {ragEval ? (
            <div className="rag-eval-panel">
              <div className="rag-eval-summary">
                <span>
                  <b>{formatPercent(ragEval.average_hit_rate)}</b>
                  Average retrieval hit rate
                </span>
                <span>
                  <b>{ragEval.passed_cases}/{ragEval.total_cases}</b>
                  Cases passed
                </span>
                <span>
                  <b>{ragEval.source}</b>
                  Source
                </span>
                <span>
                  <b>{formatDateTime(ragEval.created_at)}</b>
                  Last published
                </span>
                <span>
                  <b>{formatOptionalPercent(retrievalMetrics.context_recall ?? ragEval.average_hit_rate)}</b>
                  Context recall
                </span>
                <span>
                  <b>{formatOptionalPercent(retrievalMetrics.context_precision)}</b>
                  Context precision
                </span>
                <span>
                  <b>{formatOptionalPercent(ragasMetrics.faithfulness)}</b>
                  Faithfulness
                </span>
                <span>
                  <b>{formatOptionalPercent(ragasMetrics.context_precision)}</b>
                  RAGAS context precision
                </span>
                <span>
                  <b>{formatOptionalPercent(ragasMetrics.context_recall)}</b>
                  RAGAS context recall
                </span>
                <span>
                  <b>{ragEval.metrics?.judge?.provider || 'local only'}</b>
                  Judge
                </span>
              </div>
              <div className="rag-case-list">
                {(ragEval.metrics?.cases || []).map((item) => (
                  <article className="rag-case-row" key={item.id}>
                    <div>
                      <b>{item.id}</b>
                      <p>{item.question}</p>
                    </div>
                    <div className="rag-case-scores">
                      <span>Recall {formatPercent(item.hit_rate)}</span>
                      <span>Precision {formatPercent(item.context_precision)}</span>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ) : (
            <p className="muted">
              No RAG eval result yet. Run the local RAGAS script with publish enabled, then refresh this page.
            </p>
          )}
        </section>
        <section className="metric-panel wide-metric-panel">
          <h3>Latest load test</h3>
          {loadTest ? (
            <div className="latency-table">
              <div className="latency-row">
                <b>{loadTest.endpoint || 'unknown endpoint'}</b>
                <span>{loadTest.requests || 0} requests</span>
                <span>{loadTest.concurrency || 0} concurrency</span>
                <span>{loadTest.success || 0} success</span>
                <span>{loadTest.failed || 0} failed</span>
                <span>{loadTest.wall_time_seconds || 0}s wall</span>
              </div>
              <div className="latency-row">
                <b>{loadTest.base_url || 'unknown target'}</b>
                <span>avg {loadTest.average_ms || 0}ms</span>
                <span>p95 {loadTest.p95_ms || 0}ms</span>
                <span>max {loadTest.max_ms || 0}ms</span>
                <span>{formatDateTime(loadTest.created_at)}</span>
                <span>{loadTest.source || 'load_test_api'}</span>
              </div>
            </div>
          ) : (
            <p className="muted">No load test report published yet. Run the load test script with publish enabled.</p>
          )}
        </section>
        <section className="metric-panel wide-metric-panel">
          <h3>Agent latency by stage</h3>
          <div className="latency-table">
            {(agentLatency.by_agent || []).map((item) => (
              <div className="latency-row" key={item.agent}>
                <b>{item.agent.replace('_', ' ')}</b>
                <span>{item.count} runs</span>
                <span>avg {item.average_ms}ms</span>
                <span>p95 {item.p95_ms}ms</span>
                <span>max {item.max_ms}ms</span>
                <span>{item.fallback_count} fallback</span>
              </div>
            ))}
            {!agentLatency.by_agent?.length && (
              <p className="muted">No agent latency data yet. Submit a meal and wait for the orchestrator result.</p>
            )}
          </div>
        </section>
        <section className="metric-panel wide-metric-panel">
          <h3>Token cost by provider</h3>
          <div className="latency-table">
            {Object.entries(tokenCost.by_provider || {}).map(([provider, item]) => (
              <div className="latency-row" key={provider}>
                <b>{provider}</b>
                <span>{item.calls || 0} calls</span>
                <span>{item.input_tokens || 0} in</span>
                <span>{item.output_tokens || 0} out</span>
                <span>{item.total_tokens || 0} total</span>
                <span>{formatUsd(item.estimated_cost_usd)}</span>
              </div>
            ))}
            {!Object.keys(tokenCost.by_provider || {}).length && (
              <p className="muted">No token usage data yet. Submit a meal after deploying token-cost tracking.</p>
            )}
          </div>
        </section>
        <section className="metric-panel wide-metric-panel">
          <h3>Token cost by agent</h3>
          <div className="latency-table">
            {Object.entries(tokenCost.by_agent || {}).map(([agent, item]) => (
              <div className="latency-row" key={agent}>
                <b>{agent.replace('_', ' ')}</b>
                <span>{item.calls || 0} calls</span>
                <span>{item.input_tokens || 0} in</span>
                <span>{item.output_tokens || 0} out</span>
                <span>{item.total_tokens || 0} total</span>
                <span>{formatUsd(item.estimated_cost_usd)}</span>
              </div>
            ))}
            {!Object.keys(tokenCost.by_agent || {}).length && (
              <p className="muted">No agent token usage data yet.</p>
            )}
          </div>
        </section>
        <section className="metric-panel wide-metric-panel">
          <h3>API latency by endpoint</h3>
          <div className="latency-table">
            {(apiLatency.by_endpoint || []).map((item) => (
              <div className="latency-row" key={item.endpoint}>
                <b>{item.endpoint}</b>
                <span>{item.count} calls</span>
                <span>avg {item.average_ms}ms</span>
                <span>p95 {item.p95_ms}ms</span>
                <span>max {item.max_ms}ms</span>
                <span>{item.latest_status}</span>
              </div>
            ))}
            {!apiLatency.by_endpoint?.length && <p className="muted">No API latency data yet. Use the app, then refresh this page.</p>}
          </div>
        </section>
      </div>
    </section>
  )
}
