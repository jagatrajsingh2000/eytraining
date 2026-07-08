import re

# ── Step 1: Read storyboard_v2.html ──
with open('presentation/storyboard_v2.html', 'r') as f:
    sb = f.read()

# ── Step 2: Extract just the <head> (from <!DOCTYPE> through </head>) ──
head_end = sb.find('</head>')
chunk_head = sb[:head_end + len('</head>')]

# ── Step 3: Inject EY branding CSS into the <head> ──
ey_css = """
    /* ==================================
       EY BRANDING & TECHNICAL SLIDE CSS
       ================================== */
    .ey-logo-bottom { position: fixed; bottom: 30px; right: 40px; width: 75px; z-index: 1000; mix-blend-mode: multiply; pointer-events: none; }
    .ey-footer { position: fixed; bottom: 0; left: 0; width: 100%; height: 6px; background-color: #FFE600; z-index: 999; }

    .tech-card { background: var(--bg-card); border: 1px solid rgba(0,0,0,0.05); padding: 30px; border-radius: 16px; border-top: 3px solid var(--teal-400); box-shadow: var(--shadow); }
    .tech-yellow-box { border-left: 6px solid #FFE600; padding: 20px 24px; background: rgba(255,230,0,0.05); margin-bottom: 24px; border-radius: 0 16px 16px 0; }

    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; width: 100%; max-width: 1200px; margin: 0 auto; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; width: 100%; max-width: 1200px; margin: 0 auto; }

    .flow { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 20px; width: 100%; max-width: 1200px; }
    .flow-node { background: var(--bg-card); border: 1px solid rgba(0,0,0,0.05); box-shadow: var(--shadow); color: var(--text-primary); padding: 20px; text-align: center; border-radius: 12px; flex: 1; position: relative; border-top: 3px solid var(--text-primary); }
    .flow-arrow { font-size: 24px; color: var(--text-muted); font-weight: bold; flex-shrink: 0; }

    .metric-ring { width: 140px; height: 140px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 800; margin: 0 auto 20px; position: relative; color: var(--text-primary); box-shadow: var(--shadow); }
    .metric-ring::before { content: ''; position: absolute; inset: 12px; background: var(--bg-dark); border-radius: 50%; z-index: 1; }
    .metric-ring span { position: relative; z-index: 2; }

    .tree { display: flex; flex-direction: column; align-items: center; gap: 15px; margin-top: 20px; }
    .tree-root { background: var(--bg-card); color: var(--text-primary); padding: 15px 30px; border-radius: 8px; font-weight: bold; border: 2px solid #FFE600; box-shadow: var(--shadow); }
    .tree-branch { display: flex; gap: 40px; position: relative; }
    .tree-branch::before { content: ''; position: absolute; top: -15px; left: 50%; width: 2px; height: 15px; background: rgba(0,0,0,0.1); }
    .tree-branch::after { content: ''; position: absolute; top: -15px; left: 15%; width: 70%; height: 2px; background: rgba(0,0,0,0.1); }
    .tree-leaf { background: var(--bg-card-alt); border: 1px solid rgba(0,0,0,0.05); padding: 15px; border-radius: 8px; position: relative; text-align: center; color: var(--text-secondary); }
    .tree-leaf::before { content: ''; position: absolute; top: -15px; left: 50%; width: 2px; height: 15px; background: rgba(0,0,0,0.1); }

    .pipeline-node-title { font-weight: bold; margin-top: 10px; margin-bottom: 5px; font-size: 16px; color: var(--text-primary); }

    .code-block { background: var(--bg-card); border: 1px solid rgba(0,0,0,0.05); color: var(--text-primary); padding: 20px; border-radius: 8px; font-family: monospace; font-size: 14px; line-height: 1.5; text-align: left; width: 100%; max-width: 800px; box-shadow: var(--shadow); }
"""
chunk_head = chunk_head.replace('</style>', ey_css + '\n  </style>')

# ── Step 4: Extract all <section> slides, remove "Three AI Agents" ──
sections = re.findall(r'(<section class="slide"[^>]*>.*?</section>)', sb, re.DOTALL)
narrative_sections = [s for s in sections if 'Three AI Agents Go to Work' not in s]

# Renumber IDs sequentially
renumbered = []
for i, sec in enumerate(narrative_sections):
    sec = re.sub(r'id="slide-[^"]*"', f'id="slide-{i}"', sec)
    renumbered.append(sec)

num_narrative = len(renumbered)
print(f"Narrative slides: {num_narrative}")

# ── Step 5: Build tech slides ──
t = num_narrative
tech_titles = ["Problem", "Specs", "Kiro", "Architecture", "Pipeline", "CI/CD", "Performance", "Testing", "Design", "Challenges", "Dashboard", "Observability", "Stats"]
total_slides = num_narrative + len(tech_titles)

tech_slides = f"""
  <section class="slide" id="slide-{t}">
    <div class="bg-grid"></div>
    <div class="bg-glow" style="background: var(--indigo-500); top: -200px; left: -200px;"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(255,230,0,0.2); color: #8A7C00;">MARKET &amp; PROBLEM</span>
      </div>
      <h2 style="margin-bottom: 48px; text-align: center;">Why NutriGuard AI Exists</h2>
      <div class="grid-2">
        <div class="tech-card" style="border-top-color: var(--teal-500);">
          <h3 style="color: var(--teal-600); margin-bottom: 16px;">The Invisible Risk</h3>
          <p style="font-size: 18px; color: var(--text-secondary); line-height: 1.6;">Over 500M people in India have micronutrient deficiencies (iron, B12, D). Users track calories, but miss <strong>invisible risks</strong> (e.g., drinking tea with iron supplements blocks absorption).</p>
          <p style="font-size: 18px; color: var(--text-secondary); line-height: 1.6; margin-top: 16px;">Generic chatbots hallucinate. Traditional apps require tedious gram-tracking.</p>
        </div>
        <div class="tech-card" style="border-top-color: #FFE600; display: flex; flex-direction: column; justify-content: flex-end;">
          <h3 style="color: #8A7C00; margin-bottom: 16px;">Market Opportunity</h3>
          <div style="display: flex; align-items: flex-end; height: 200px; gap: 10px; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 10px;">
             <div style="flex:1; background: rgba(0,0,0,0.05); height: 10%; text-align: center; font-size: 12px; padding-top: 8px; border-radius: 6px 6px 0 0;">$6.4B</div>
             <div style="flex:1; background: rgba(0,0,0,0.1); height: 40%; text-align: center; font-size: 12px; padding-top: 8px; border-radius: 6px 6px 0 0;">$22B</div>
             <div style="flex:1; background: #FFE600; color: #000; height: 80%; text-align: center; font-size: 12px; font-weight: bold; padding-top: 8px; border-radius: 6px 6px 0 0;">$280B</div>
          </div>
          <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 12px; color: var(--text-secondary);">
             <span style="flex:1; text-align:center;">Diet Apps</span>
             <span style="flex:1; text-align:center;">AI Health</span>
             <span style="flex:1; text-align:center; color: #8A7C00; font-weight: bold;">Digital Health</span>
          </div>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+1} / {total_slides}</span></div>
    </div>
  </section>

  <section class="slide" id="slide-{t+1}">
    <div class="bg-grid"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: var(--green-100); color: var(--green-700);">SPECIFICATIONS</span>
      </div>
      <h2 style="margin-bottom: 48px; text-align: center;">Core System Specifications</h2>
      <div class="grid-2">
        <div class="tech-card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; border: 2px dashed rgba(0,0,0,0.1); background: transparent; box-shadow: none;">
          <div style="font-size: 64px; margin-bottom: 20px;">📄</div>
          <h3 style="color: var(--text-secondary);">NutriGuard_AI_Design_Document.pdf</h3>
        </div>
        <div>
          <div class="tech-yellow-box"><h3 style="color: #8A7C00;">Event-Driven Microservices</h3><p style="font-size: 15px; color: var(--text-secondary); margin-top: 8px;">Asynchronous processing via Azure Service Bus.</p></div>
          <div class="tech-yellow-box"><h3 style="color: #8A7C00;">Multi-Agent Reasoning</h3><p style="font-size: 15px; color: var(--text-secondary); margin-top: 8px;">LangGraph orchestrates 3 specialized LLM agents.</p></div>
          <div class="tech-yellow-box"><h3 style="color: #8A7C00;">Safety-First Design</h3><p style="font-size: 15px; color: var(--text-secondary); margin-top: 8px;">Strict guardrails block medical diagnosis or dosage advice.</p></div>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+2} / {total_slides}</span></div>
    </div>
  </section>

  <section class="slide" id="slide-{t+2}">
    <div class="bg-grid"></div>
    <div class="bg-glow" style="background: var(--purple-500); top: -200px; right: -200px;"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(168,85,247,0.1); color: #7c3aed;">RATE LIMITING</span>
      </div>
      <h2 style="margin-bottom: 20px; text-align: center;">AWS Kiro Rate Limiter Design</h2>
      <p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 40px; max-width: 800px; text-align: center; margin-left: auto; margin-right: auto;">We used <strong>AWS Kiro</strong> (agentic IDE) to design and plan the rate limiter upfront, prioritizing a strict planning phase.</p>
      <div class="grid-2" style="align-items: center;">
        <div class="tech-card" style="text-align: center; border-color: #FFE600; padding: 20px;">
           <div style="background: var(--bg-card-alt); padding: 12px; border-radius: 8px; font-weight: bold; border: 1px solid rgba(0,0,0,0.05);">User Prompt: "Build distributed rate limiter"</div>
           <div style="font-size: 24px; color: #8A7C00; margin: 10px 0;">⬇</div>
           <div style="background: #fff; padding: 20px; border: 2px solid #FFE600; border-radius: 8px; box-shadow: var(--shadow);">
               <strong style="font-size: 18px; color: #8A7C00;">Kiro Spec-Driven Planning</strong><br>
               <div style="display: flex; justify-content: center; gap: 10px; margin-top: 15px;">
                   <div style="background: var(--bg-card-alt); padding: 8px 12px; border-radius: 4px; font-size: 12px;">requirements.md</div>
                   <div style="background: var(--bg-card-alt); padding: 8px 12px; border-radius: 4px; font-size: 12px;">design.md</div>
                   <div style="background: var(--bg-card-alt); padding: 8px 12px; border-radius: 4px; font-size: 12px;">tasks.md</div>
               </div>
           </div>
           <div style="font-size: 24px; color: #8A7C00; margin: 10px 0;">⬇</div>
           <div style="display: flex; justify-content: space-between; gap: 10px;">
               <div style="background: var(--green-50); border: 1px solid var(--green-500); color: var(--green-600); padding: 12px; border-radius: 6px; font-size: 12px; flex:1;">Parallel Agent Impl.</div>
               <div style="background: #eff6ff; border: 1px solid var(--indigo-500); color: var(--indigo-600); padding: 12px; border-radius: 6px; font-size: 12px; flex:1;">Property Testing</div>
           </div>
        </div>
        <div>
          <div class="tech-yellow-box"><h3 style="color: #8A7C00;">Beyond "Vibe Coding"</h3><p style="font-size: 15px; color: var(--text-secondary); margin-top: 8px;">Forcing a planning phase ensures the token-bucket architecture matches our exact intent.</p></div>
          <div class="tech-yellow-box"><h3 style="color: #8A7C00;">Edge-Case Handling</h3><p style="font-size: 15px; color: var(--text-secondary); margin-top: 8px;">Deep property-based testing caught concurrent database race conditions before deployment.</p></div>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+3} / {total_slides}</span></div>
    </div>
  </section>

  <section class="slide" id="slide-{t+3}">
    <div class="bg-grid"></div>
    <div class="slide-inner" style="justify-content: center; align-items: center;">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: #eff6ff; color: var(--indigo-600);">ARCHITECTURE</span>
      </div>
      <h2 style="margin-bottom: 20px; text-align: center;">Detailed System Architecture</h2>
      <div class="flow" style="margin-top: 20px; margin-bottom: 50px;">
        <div class="flow-node"><div style="font-size: 24px; margin-bottom: 8px;">📱</div>React<br><span style="font-size: 11px; color: var(--text-secondary);">Frontend</span></div>
        <div class="flow-arrow">➔</div>
        <div class="flow-node"><div style="font-size: 24px; margin-bottom: 8px;">⚡</div>FastAPI<br><span style="font-size: 11px; color: var(--text-secondary);">Gateway</span></div>
        <div class="flow-arrow">➔</div>
        <div class="flow-node" style="border-top-color: var(--teal-500);"><div style="font-size: 24px; margin-bottom: 8px;">📨</div>Service Bus<br><span style="font-size: 11px; color: var(--teal-600);">Event Queue</span></div>
        <div class="flow-arrow">➔</div>
        <div class="flow-node" style="border-top-color: var(--green-500);"><div style="font-size: 24px; margin-bottom: 8px;">🧠</div>LangGraph<br><span style="font-size: 11px; color: var(--green-600);">AI Orchestrator</span></div>
        <div class="flow-arrow">➔</div>
        <div class="flow-node"><div style="font-size: 24px; margin-bottom: 8px;">🗄️</div>PostgreSQL<br><span style="font-size: 11px; color: var(--text-secondary);">State</span></div>
      </div>
      <div class="grid-2">
        <div class="tech-card" style="border-top-color: var(--green-500);"><h3 style="color: var(--green-600);">Pros</h3>
          <ul style="margin-top: 10px; margin-left: 20px; line-height: 1.6; font-size: 15px; color: var(--text-secondary);"><li><strong>Total Decoupling:</strong> LLM generations never block FastAPI.</li><li><strong>Resilience:</strong> Automatic requeues via Azure Service Bus.</li><li><strong>Auto-Scaling:</strong> Container Apps scale based on queue depth.</li></ul></div>
        <div class="tech-card" style="border-top-color: var(--red-500);"><h3 style="color: var(--red-500);">Trade-offs</h3>
          <ul style="margin-top: 10px; margin-left: 20px; line-height: 1.6; font-size: 15px; color: var(--text-secondary);"><li><strong>Eventual Consistency:</strong> Frontend must poll or use WebSockets.</li><li><strong>Distributed Debugging:</strong> Requires cross-service log tracing.</li></ul></div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+4} / {total_slides}</span></div>
    </div>
  </section>

  <section class="slide" id="slide-{t+4}">
    <div class="bg-grid"></div>
    <div class="slide-inner" style="justify-content: center; align-items: center;">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
        <span class="story-stage" style="background: var(--green-100); color: var(--green-700);">ORCHESTRATION</span>
      </div>
      <h2 style="margin-bottom: 16px; text-align: center;">LangGraph Agent Pipeline</h2>
      <p style="font-size: 16px; color: var(--text-secondary); text-align: center; margin-bottom: 48px;">A 3-stage linear DAG processes each meal through specialized AI agents.</p>
      <div class="pipeline" style="margin-bottom: 48px;">
        <div class="pipeline-node" style="border-top: 3px solid var(--text-muted);"><div style="font-size: 1.5rem;">📥</div><div class="pipeline-node-title">User Input</div></div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node" style="border-top: 3px solid var(--green-500);"><div style="font-size: 1.5rem;">🔍</div><div class="pipeline-node-title" style="color: var(--green-600);">Meal Analyzer</div></div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node" style="border-top: 3px solid var(--indigo-500);"><div style="font-size: 1.5rem;">⚠️</div><div class="pipeline-node-title" style="color: var(--indigo-600);">Health Risk</div></div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node" style="border-top: 3px solid var(--purple-500);"><div style="font-size: 1.5rem;">📝</div><div class="pipeline-node-title" style="color: #7c3aed;">Report Agent</div></div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node" style="border-top: 3px solid var(--green-500);"><div style="font-size: 1.5rem;">✅</div><div class="pipeline-node-title" style="color: var(--green-600);">Daily Report</div></div>
      </div>
      
      <div class="grid-3" style="max-width: 1200px; width: 100%;">
        <div class="tech-card" style="border-top-color: var(--green-500); padding: 20px;">
          <h3 style="font-size: 18px; color: var(--green-600); margin-bottom: 8px;">🔍 1. Meal Analyzer</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Extracts foods, ingredients, portion sizes, and nutritional properties from unstructured text logs.</p>
          <div style="background: var(--bg-card-alt); padding: 10px; border-radius: 8px; font-size: 12px; border-left: 3px solid var(--green-500);">
            <strong>Example:</strong> "Tea & poha"<br>
            ➔ <em>Carbs (poha), Tannins (tea)</em>
          </div>
        </div>
        <div class="tech-card" style="border-top-color: var(--indigo-500); padding: 20px;">
          <h3 style="font-size: 18px; color: var(--indigo-600); margin-bottom: 8px;">⚠️ 2. Health Risk Agent</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Compares meals against user's health profile (deficiencies, supplements) to flag risks or absorption inhibitors.</p>
          <div style="background: var(--bg-card-alt); padding: 10px; border-radius: 8px; font-size: 12px; border-left: 3px solid var(--indigo-500);">
            <strong>Example:</strong> Tannins from tea block the absorption of user's morning Iron supplement.
          </div>
        </div>
        <div class="tech-card" style="border-top-color: #7c3aed; padding: 20px;">
          <h3 style="font-size: 18px; color: #7c3aed; margin-bottom: 8px;">📝 3. Report Agent</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Synthesizes daily insights into empathetic reports, suggesting adjustments and health-safe alternatives.</p>
          <div style="background: var(--bg-card-alt); padding: 10px; border-radius: 8px; font-size: 12px; border-left: 3px solid #7c3aed;">
            <strong>Example:</strong> "Wait 2 hours after your iron pill to drink tea, or swap it for vitamin-C rich lemon water."
          </div>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+5} / {total_slides}</span></div>
    </div>
  </section>

  <section class="slide" id="slide-{t+5}">
    <div class="bg-grid"></div>
    <div class="bg-glow" style="background: var(--indigo-500); bottom: -100px; right: -100px;"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: #eff6ff; color: var(--indigo-600);">DEPLOYMENT</span>
      </div>
      <h2 style="margin-bottom: 30px; text-align: center;">CI/CD &amp; Azure Deployment</h2>
      <div class="grid-2" style="align-items: center;">
        <div>
          <div class="tech-yellow-box"><h3 style="color: #8A7C00;">GitHub Actions (CI/CD)</h3><p style="font-size: 15px; color: var(--text-secondary); margin-top: 8px;">Every push to main triggers automated linting, PyTest runs, and Docker container builds.</p></div>
          <div class="tech-card" style="border-top-color: var(--indigo-500);"><h3 style="color: var(--indigo-600);">Azure Cloud Hosting</h3><p style="font-size: 15px; color: var(--text-secondary); margin-top: 8px;">React frontend on <strong>Azure Static Web Apps</strong>. Backend on <strong>Azure Container Apps (ACA)</strong>.</p></div>
        </div>
        <div style="background: var(--bg-card); border: 1px solid rgba(0,0,0,0.05); border-radius: 12px; padding: 30px; text-align: center; box-shadow: var(--shadow);">
          <div style="background: var(--bg-card-alt); color: var(--text-primary); padding: 15px; border-radius: 8px; margin-bottom: 15px;"><strong>GitHub Actions</strong><br><span style="font-size: 12px; color: var(--text-secondary);">CI/CD Build</span></div>
          <div style="font-size: 20px; color: var(--text-muted); margin-bottom: 15px;">⬇</div>
          <div style="background: #eff6ff; border: 1px solid var(--indigo-400); color: var(--indigo-600); padding: 15px; border-radius: 8px; margin-bottom: 15px;"><strong>Azure Container Registry</strong><br><span style="font-size: 12px;">Image Storage</span></div>
          <div style="font-size: 20px; color: var(--text-muted); margin-bottom: 15px;">⬇</div>
          <div style="background: var(--green-50); border: 1px solid var(--green-400); color: var(--green-600); padding: 15px; border-radius: 8px;"><strong>Azure Container Apps</strong><br><span style="font-size: 12px;">Event-Driven Auto-Scaling</span></div>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+6} / {total_slides}</span></div>
    </div>
  </section>

  <!-- SLIDE: PERFORMANCE DASHBOARD -->
  <section class="slide" id="slide-{t+6}">
    <div class="bg-grid"></div>
    <div class="bg-glow" style="background: var(--amber-500); top: -200px; right: -200px;"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(255,230,0,0.15); color: #8A7C00;">PERFORMANCE</span>
      </div>
      <h2 style="margin-bottom: 24px; text-align: center;">Agent Latency, Load Test &amp; <span style="color: var(--green-500);">Token Costs</span></h2>

      <div class="grid-2">
        <!-- Agent Latency Table -->
        <div class="tech-card" style="border-top-color: var(--indigo-500); padding: 20px;">
          <h3 style="font-size: 18px; margin-bottom: 16px;">⚡ Agent Latency by Stage</h3>
          <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead><tr style="border-bottom: 2px solid rgba(0,0,0,0.1);">
              <th style="text-align: left; padding: 8px 4px; color: var(--text-muted); font-weight: 700;">AGENT</th>
              <th style="text-align: center; padding: 8px 4px; color: var(--text-muted);">RUNS</th>
              <th style="text-align: center; padding: 8px 4px; color: var(--text-muted);">AVG</th>
              <th style="text-align: center; padding: 8px 4px; color: var(--text-muted);">P95</th>
              <th style="text-align: center; padding: 8px 4px; color: var(--text-muted);">MAX</th>
            </tr></thead>
            <tbody>
              <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);"><td style="padding: 10px 4px; font-weight: 600; color: var(--green-600);">meal analyzer</td><td style="text-align: center;">6</td><td style="text-align: center; color: var(--teal-600);">43,271ms</td><td style="text-align: center; color: var(--amber-500);">161,164ms</td><td style="text-align: center;">161,164ms</td></tr>
              <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);"><td style="padding: 10px 4px; font-weight: 600; color: var(--indigo-600);">health risk</td><td style="text-align: center;">6</td><td style="text-align: center; color: var(--teal-600);">37,087ms</td><td style="text-align: center; color: var(--amber-500);">83,409ms</td><td style="text-align: center;">83,409ms</td></tr>
              <tr><td style="padding: 10px 4px; font-weight: 600; color: #7c3aed;">report</td><td style="text-align: center;">6</td><td style="text-align: center; color: var(--teal-600);">26,198ms</td><td style="text-align: center; color: var(--amber-500);">55,446ms</td><td style="text-align: center;">55,446ms</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Load Test -->
        <div class="tech-card" style="border-top-color: var(--green-500); padding: 20px;">
          <h3 style="font-size: 18px; margin-bottom: 16px;">🏋️ Latest Load Test</h3>
          <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;">
            <span style="background: var(--green-50); color: var(--green-600); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid var(--green-400);">5000 requests</span>
            <span style="background: #eff6ff; color: var(--indigo-600); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid var(--indigo-400);">5 concurrency</span>
            <span style="background: var(--green-50); color: var(--green-600); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid var(--green-400);">5000 success</span>
            <span style="background: var(--green-50); color: var(--green-600); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid var(--green-400);">0 failed</span>
          </div>
          <p style="font-size: 14px; color: var(--text-muted); margin-bottom: 16px;">Endpoint: /users/1/profile</p>
          <div style="display: flex; gap: 16px; justify-content: center;">
            <div style="text-align: center;"><div style="font-size: 28px; font-weight: 900; color: var(--teal-600);">170ms</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">AVG LATENCY</div></div>
            <div style="text-align: center;"><div style="font-size: 28px; font-weight: 900; color: var(--indigo-600);">305ms</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">P95 LATENCY</div></div>
            <div style="text-align: center;"><div style="font-size: 28px; font-weight: 900; color: var(--red-500);">755ms</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">MAX LATENCY</div></div>
          </div>
        </div>
      </div>

      <!-- Token Cost Tables -->
      <div class="grid-2" style="margin-top: 24px;">
        <div class="tech-card" style="border-top-color: var(--amber-500); padding: 20px;">
          <h3 style="font-size: 18px; margin-bottom: 12px;">💰 Token Cost by Provider</h3>
          <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead><tr style="border-bottom: 2px solid rgba(0,0,0,0.1);"><th style="text-align: left; padding: 6px 4px; color: var(--text-muted);">PROVIDER</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">CALLS</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">INPUT</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">OUTPUT</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">TOTAL</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">COST</th></tr></thead>
            <tbody><tr><td style="padding: 8px 4px; font-weight: 600; color: var(--indigo-600);">gemini</td><td style="text-align: center;">3</td><td style="text-align: center;">3,436</td><td style="text-align: center;">611</td><td style="text-align: center;">9,406</td><td style="text-align: center; color: var(--green-600); font-weight: 800;">$0.00</td></tr></tbody>
          </table>
        </div>
        <div class="tech-card" style="border-top-color: #7c3aed; padding: 20px;">
          <h3 style="font-size: 18px; margin-bottom: 12px;">🤖 Token Cost by Agent</h3>
          <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead><tr style="border-bottom: 2px solid rgba(0,0,0,0.1);"><th style="text-align: left; padding: 6px 4px; color: var(--text-muted);">AGENT</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">CALLS</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">INPUT</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">OUTPUT</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">TOTAL</th><th style="text-align: center; padding: 6px; color: var(--text-muted);">COST</th></tr></thead>
            <tbody>
              <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);"><td style="padding: 6px 4px; font-weight: 600; color: var(--green-600);">meal analyzer</td><td style="text-align: center;">1</td><td style="text-align: center;">120</td><td style="text-align: center;">69</td><td style="text-align: center;">508</td><td style="text-align: center; color: var(--green-600);">$0.00</td></tr>
              <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);"><td style="padding: 6px 4px; font-weight: 600; color: var(--indigo-600);">health risk</td><td style="text-align: center;">1</td><td style="text-align: center;">1,560</td><td style="text-align: center;">198</td><td style="text-align: center;">3,614</td><td style="text-align: center; color: var(--green-600);">$0.00</td></tr>
              <tr><td style="padding: 6px 4px; font-weight: 600; color: #7c3aed;">report</td><td style="text-align: center;">1</td><td style="text-align: center;">1,756</td><td style="text-align: center;">344</td><td style="text-align: center;">5,284</td><td style="text-align: center; color: var(--green-600);">$0.00</td></tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+7} / {total_slides}</span></div>
    </div>
  </section>

  <!-- SLIDE: TESTING STRATEGY -->
  <section class="slide" id="slide-{t+7}">
    <div class="bg-grid"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: var(--green-100); color: var(--green-700);">QUALITY</span>
      </div>
      <h2 style="margin-bottom: 32px; text-align: center;">Testing <span style="color: var(--green-500);">Strategy</span></h2>
      <div class="grid-3">
        <div class="tech-card" style="border-top-color: var(--green-500); padding: 24px;">
          <h3 style="font-size: 18px; color: var(--green-600); margin-bottom: 8px;">✅ Unit Tests</h3>
          <p style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">13 tests passing in 0.51s</p>
          <ul style="font-size: 13px; color: var(--text-secondary); line-height: 1.7; margin-left: 16px;">
            <li>Admin metrics aggregation</li><li>API/agent latency computation</li><li>LLM fallback metric tracking</li><li>Password hash round-trip</li><li>Health condition normalization</li><li>Notification timezone handling</li>
          </ul>
        </div>
        <div class="tech-card" style="border-top-color: var(--amber-500); padding: 24px;">
          <h3 style="font-size: 18px; color: var(--amber-500); margin-bottom: 8px;">🏋️ Load Testing</h3>
          <p style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Configurable concurrent read tests</p>
          <ul style="font-size: 13px; color: var(--text-secondary); line-height: 1.7; margin-left: 16px;">
            <li>Zero external dependencies</li><li>ThreadPoolExecutor concurrency</li><li>avg / p95 / max latency</li><li>Status code distribution</li><li>Auto-publish to dashboard</li><li>Bearer token + auto-login</li>
          </ul>
        </div>
        <div class="tech-card" style="border-top-color: var(--red-500); padding: 24px;">
          <h3 style="font-size: 18px; color: var(--red-500); margin-bottom: 8px;">💥 Stress Testing</h3>
          <p style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Full E2E workflow simulation</p>
          <ul style="font-size: 13px; color: var(--text-secondary); line-height: 1.7; margin-left: 16px;">
            <li>Signup → Login → Profile → Meals</li><li>12 endpoints exercised</li><li>Smoke (1 user) → Load (20)</li><li>→ Pressure (50) → Recovery</li><li>Per-endpoint latency breakdown</li><li>Creates real data + triggers LLM</li>
          </ul>
        </div>
      </div>
      <div class="grid-2" style="margin-top: 24px;">
        <div class="tech-card" style="border-top-color: var(--red-400); padding: 24px;">
          <h3 style="font-size: 18px; color: var(--red-400); margin-bottom: 8px;">🎯 RAG Evaluation</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">Local retrieval-only eval (no API key needed) + full RAGAS framework with OpenAI judge. Targets: Recall@K ≥80%, Precision@K ≥60%, Faithfulness ≥90%, Safety 100%.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--teal-500); padding: 24px;">
          <h3 style="font-size: 18px; color: var(--teal-600); margin-bottom: 8px;">🛡️ Safety Guardrails</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">No medical diagnoses, no dosage changes, safety notes always included, no invented values. Manual scoring rubric: 1-5 scale, pass = avg ≥4.0, no safety case below 5.</p>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+8} / {total_slides}</span></div>
    </div>
  </section>

  <!-- SLIDE: DESIGN DECISIONS -->
  <section class="slide" id="slide-{t+8}">
    <div class="bg-grid"></div>
    <div class="bg-glow" style="background: var(--teal-500); top: -200px; left: -200px;"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(45,212,191,0.15); color: var(--teal-600);">DESIGN PATTERNS</span>
      </div>
      <h2 style="margin-bottom: 32px; text-align: center;">Key <span style="color: var(--green-500);">Design Decisions</span></h2>
      <div class="grid-3">
        <div class="tech-card" style="border-top-color: var(--red-400); padding: 24px;">
          <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(239,68,68,0.1); display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 12px;">📮</div>
          <h3 style="font-size: 18px; margin-bottom: 8px;">Outbox Pattern</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">Meals are written to DB + outbox table atomically. Background publisher polls every 5s — reliable event delivery without distributed transactions.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--teal-400); padding: 24px;">
          <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(45,212,191,0.1); display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 12px;">🔄</div>
          <h3 style="font-size: 18px; margin-bottom: 8px;">Graceful Degradation</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">3-tier LLM fallback ensures the system never completely fails. Even without any API keys, rule-based analysis provides useful guidance.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--indigo-400); padding: 24px;">
          <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(99,102,241,0.1); display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 12px;">📅</div>
          <h3 style="font-size: 18px; margin-bottom: 8px;">Day-Level Timeline</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">Full day's meal timeline sent to AI — enables cross-meal risk detection like tea 90 min after iron across different meals.</p>
        </div>
      </div>
      <div class="grid-3" style="margin-top: 24px;">
        <div class="tech-card" style="border-top-color: var(--text-muted); padding: 24px;">
          <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(0,0,0,0.05); display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 12px;">💬</div>
          <h3 style="font-size: 18px; margin-bottom: 8px;">Text Normalization</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">Free-text health conditions / supplements / deficiencies are normalized to canonical terms via alias dictionaries for consistent AI analysis.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--indigo-500); padding: 24px;">
          <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(99,102,241,0.1); display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 12px;">📊</div>
          <h3 style="font-size: 18px; margin-bottom: 8px;">DB-Backed Metrics</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">All observability stored in MetricEvent table with JSON payloads — no external monitoring dependency. Admin dashboard queries directly.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--red-500); padding: 24px;">
          <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(239,68,68,0.1); display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 12px;">🛡️</div>
          <h3 style="font-size: 18px; margin-bottom: 8px;">Safety-First AI</h3>
          <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">No medical diagnoses, no dosage changes, Ayurveda labeled as traditional guidance. Safety guardrails checked in evaluation with manual scoring rubric.</p>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+9} / {total_slides}</span></div>
    </div>
  </section>

  <!-- SLIDE: PRODUCTION CHALLENGES -->
  <section class="slide" id="slide-{t+9}">
    <div class="bg-grid"></div>
    <div class="bg-glow" style="background: var(--red-500); top: -200px; right: -200px;"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(239,68,68,0.1); color: var(--red-500);">LESSONS LEARNED</span>
      </div>
      <h2 style="margin-bottom: 32px; text-align: center;">Production <span style="color: var(--red-500);">Challenges</span></h2>
      <div class="grid-2">
        <div class="tech-card" style="border-top-color: var(--amber-500); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--amber-500); margin-bottom: 8px;">⚡ Gemini Free-Tier Daily Limit</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"><strong>Fix:</strong> 3-tier provider chain fallback (Gemini → OpenAI → rules). Multi-key rotation for quota management. All fallbacks tracked via MetricEvents.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--red-500); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--red-500); margin-bottom: 8px;">🔗 Frontend Build Wrong API URL</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"><strong>Fix:</strong> VITE_API_BASE_URL injected at build time via GitHub Secrets. Must be set correctly in CI/CD workflow.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--amber-400); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--amber-400); margin-bottom: 8px;">🔒 Service Bus Message Lock Expiry</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"><strong>Fix:</strong> Added AutoLockRenewer with configurable lock renewal (300s default). Prevents message reprocessing on slow LLM calls.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--indigo-500); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--indigo-600); margin-bottom: 8px;">📊 Observability Was Too Hard</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"><strong>Fix:</strong> Built a database-backed admin dashboard with 22+ metrics cards. No need to parse Azure logs — everything visible in the app.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--green-500); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--green-600); margin-bottom: 8px;">🔑 Internal API Key Mismatch</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"><strong>Fix:</strong> Both backend and orchestrator require the same INTERNAL_API_KEY. Added to deployment checklist and env validation.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--red-400); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--red-400); margin-bottom: 8px;">💥 RAGAS Results Not Visible</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"><strong>Fix:</strong> Added /internal/rag-eval-results endpoint. RAGAS eval script can publish results directly to dashboard with correct API key.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--teal-500); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--teal-600); margin-bottom: 8px;">🌐 CORS Issues Across Environments</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"><strong>Fix:</strong> Dynamic CORS_ORIGINS config. Custom middleware handles edge cases. Different origins for local/ngrok/production.</p>
        </div>
        <div class="tech-card" style="border-top-color: var(--green-400); padding: 20px;">
          <h3 style="font-size: 16px; color: var(--green-500); margin-bottom: 8px;">✅ Quick Debug Checklist</h3>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;">10-step production debugging runbook covering frontend URL, backend health, Service Bus queue, container status, trace IDs, and dashboard checks.</p>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+10} / {total_slides}</span></div>
    </div>
  </section>

  <!-- SLIDE: ADMIN DASHBOARD -->
  <section class="slide" id="slide-{t+10}">
    <div class="bg-grid"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(99,102,241,0.1); color: var(--indigo-600);">LIVE DATA</span>
      </div>
      <h2 style="margin-bottom: 8px; text-align: center;">Admin <span style="color: var(--indigo-500);">Dashboard</span> — Real Metrics</h2>
      <p style="font-size: 14px; color: var(--text-muted); text-align: center; margin-bottom: 24px;">DB-backed product metrics from the deployed NutriGuard instance (26 Jun – 02 Jul 2026).</p>

      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; width: 100%; max-width: 1200px; margin: 0 auto;">
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--green-500);"><div style="font-size: 32px; font-weight: 900; color: var(--green-600);">30</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Meals Submitted</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--teal-500);"><div style="font-size: 32px; font-weight: 900; color: var(--teal-600);">25</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Reports Completed</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--green-400);"><div style="font-size: 32px; font-weight: 900; color: var(--green-500);">0</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Failed Reports</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--amber-500);"><div style="font-size: 32px; font-weight: 900; color: var(--amber-500);">192.7s</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Avg Processing</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--indigo-500);"><div style="font-size: 32px; font-weight: 900; color: var(--indigo-600);">4</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Feedback Liked</div></div>

        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--green-400);"><div style="font-size: 32px; font-weight: 900; color: var(--green-500);">0</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Feedback Disliked</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--amber-400);"><div style="font-size: 32px; font-weight: 900; color: var(--amber-500);">5</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Missed Meal Nudges</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--teal-400);"><div style="font-size: 32px; font-weight: 900; color: var(--teal-500);">2</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Unread Notifications</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--red-500);"><div style="font-size: 32px; font-weight: 900; color: var(--red-500);">49</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Gemini Fallbacks</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: #7c3aed;"><div style="font-size: 32px; font-weight: 900; color: #7c3aed;">9</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">OpenAI Answers</div></div>

        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--green-400);"><div style="font-size: 32px; font-weight: 900; color: var(--green-500);">0</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">OpenAI Fallbacks</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--green-400);"><div style="font-size: 32px; font-weight: 900; color: var(--green-500);">0</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Rule Fallbacks</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--indigo-500);"><div style="font-size: 32px; font-weight: 900; color: var(--indigo-600);">5,583</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">API Requests</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--teal-500);"><div style="font-size: 32px; font-weight: 900; color: var(--teal-600);">96.88ms</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Avg API Latency</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--amber-500);"><div style="font-size: 32px; font-weight: 900; color: var(--amber-500);">239.58ms</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">P95 API Latency</div></div>

        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--red-400);"><div style="font-size: 32px; font-weight: 900; color: var(--red-400);">1,587ms</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Slowest API</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--indigo-400);"><div style="font-size: 32px; font-weight: 900; color: var(--indigo-500);">18</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Agent Runs</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--teal-400);"><div style="font-size: 32px; font-weight: 900; color: var(--teal-500);">35.5s</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Avg Agent Latency</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--amber-500);"><div style="font-size: 32px; font-weight: 900; color: var(--amber-500);">83.4s</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">P95 Agent Latency</div></div>
        <div class="tech-card" style="text-align: center; padding: 16px; border-top-color: var(--red-500);"><div style="font-size: 32px; font-weight: 900; color: var(--red-500);">161.2s</div><div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Slowest Agent</div></div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+11} / {total_slides}</span></div>
    </div>
  </section>

  <section class="slide" id="slide-{t+11}">
    <div class="bg-grid"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(255,230,0,0.15); color: #8A7C00;">METRICS</span>
      </div>
      <h2 style="margin-bottom: 30px; text-align: center;">Load Testing &amp; Observability</h2>
      <div class="grid-3">
        <div style="text-align: center;"><div class="metric-ring" style="background: conic-gradient(var(--green-500) 90%, rgba(0,0,0,0.05) 90%);"><span style="color: var(--green-600);">&gt;90%</span></div><h3 style="color: var(--text-primary);">Extraction Accuracy</h3></div>
        <div style="text-align: center;"><div class="metric-ring" style="background: conic-gradient(#FFE600 100%, rgba(0,0,0,0.05) 100%);"><span style="color: #8A7C00;">&lt;20s</span></div><h3 style="color: var(--text-primary);">E2E Latency</h3></div>
        <div style="text-align: center;"><div class="metric-ring" style="background: conic-gradient(var(--red-500) 5%, rgba(0,0,0,0.05) 5%);"><span style="color: var(--red-500);">&lt;5%</span></div><h3 style="color: var(--text-primary);">Failure Rate</h3></div>
      </div>
      <div style="margin-top: 40px; border-top: 1px solid rgba(0,0,0,0.1); padding-top: 30px;">
        <h3 style="text-align: center; color: var(--text-secondary); margin-bottom: 10px;">Azure Log Analytics Trace Tree</h3>
        <p style="text-align: center; font-size: 14px; color: var(--text-muted);">Every request stamped with <code>correlation_id = meal_log_id</code>.</p>
        <div class="tree">
           <div class="tree-root">Request ID: req-9b34-45a1</div>
           <div class="tree-branch">
              <div class="tree-leaf">FastAPI Ingress<br><span style="color: var(--green-600); font-size: 11px; font-weight: bold;">HTTP 202</span></div>
              <div class="tree-leaf">Azure Service Bus<br><span style="color: var(--indigo-600); font-size: 11px; font-weight: bold;">Event Published</span></div>
              <div class="tree-leaf">LangGraph Worker<br><span style="color: #8A7C00; font-size: 11px; font-weight: bold;">3 Agents (12.4s)</span></div>
           </div>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+12} / {total_slides}</span></div>
    </div>
  </section>

  <section class="slide" id="slide-{t+12}">
    <div class="bg-grid"></div>
    <div class="bg-glow" style="background: var(--teal-500); bottom: -200px; left: -200px;"></div>
    <div class="slide-inner">
      <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
        <span class="story-stage" style="background: rgba(45,212,191,0.15); color: var(--teal-600);">OSS</span>
      </div>
      <h2 style="margin-bottom: 40px; text-align: center;">Project Stats &amp; Open Source Stack</h2>
      <div class="grid-3" style="margin-bottom: 60px;">
        <div class="tech-card" style="text-align: center; border-top-color: #FFE600;"><div style="font-size: 48px; font-weight: 900; color: #8A7C00;">~15k</div><div style="font-size: 16px; color: var(--text-secondary); margin-top: 10px;">Lines of Code (LOC)</div></div>
        <div class="tech-card" style="text-align: center; border-top-color: var(--indigo-500);"><div style="font-size: 48px; font-weight: 900; color: var(--indigo-600);">250+</div><div style="font-size: 16px; color: var(--text-secondary); margin-top: 10px;">Git Commits</div></div>
        <div class="tech-card" style="text-align: center; border-top-color: var(--green-500);"><div style="font-size: 48px; font-weight: 900; color: var(--green-600);">99.9%</div><div style="font-size: 16px; color: var(--text-secondary); margin-top: 10px;">Target Uptime (Azure)</div></div>
      </div>
      <div class="tech-yellow-box" style="border-radius: 16px; border-left: none; border-bottom: 4px solid #FFE600; text-align: center;">
        <h3 style="margin-bottom: 20px; color: var(--text-primary);">Open Source Stack</h3>
        <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
           <span style="background: var(--bg-card); color: var(--text-primary); padding: 10px 20px; border-radius: 30px; font-weight: bold; border: 1px solid rgba(0,0,0,0.1); box-shadow: var(--shadow);">React.js</span>
           <span style="background: var(--bg-card); color: var(--text-primary); padding: 10px 20px; border-radius: 30px; font-weight: bold; border: 1px solid rgba(0,0,0,0.1); box-shadow: var(--shadow);">FastAPI</span>
           <span style="background: var(--bg-card); color: #8A7C00; padding: 10px 20px; border-radius: 30px; font-weight: bold; border: 1px solid rgba(0,0,0,0.1); box-shadow: var(--shadow);">LangGraph</span>
           <span style="background: var(--bg-card); color: var(--text-primary); padding: 10px 20px; border-radius: 30px; font-weight: bold; border: 1px solid rgba(0,0,0,0.1); box-shadow: var(--shadow);">PostgreSQL</span>
           <span style="background: var(--bg-card); color: var(--text-primary); padding: 10px 20px; border-radius: 30px; font-weight: bold; border: 1px solid rgba(0,0,0,0.1); box-shadow: var(--shadow);">Docker</span>
        </div>
      </div>
      <div class="slide-footer"><span>NutriGuard AI — Technical Deep-Dive</span><span>{t+13} / {total_slides}</span></div>
    </div>
  </section>
"""

# ── Step 6: Build nav dots ──
all_titles = [f"Narrative {i}" for i in range(num_narrative)] + tech_titles
nav_dots_html = '  <nav class="nav-dots" id="navDots">\n'
for i in range(total_slides):
    active = ' active' if i == 0 else ''
    nav_dots_html += f'    <button class="nav-dot{active}" data-slide="{i}" title="{all_titles[i]}"></button>\n'
nav_dots_html += '  </nav>\n'

# ── Step 7: Build the script ──
script = """
  <script>
    const dots = document.querySelectorAll('.nav-dot');
    const slides = document.querySelectorAll('.slide');

    dots.forEach((dot, i) => {
      dot.addEventListener('click', () => {
        if (slides[i]) slides[i].scrollIntoView({ behavior: 'smooth' });
      });
    });

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const idx = Array.from(slides).indexOf(entry.target);
          dots.forEach((d, i) => d.classList.toggle('active', i === idx));
        }
      });
    }, { threshold: 0.5 });
    slides.forEach(slide => observer.observe(slide));

    document.addEventListener('keydown', (e) => {
      const currentIdx = Array.from(dots).findIndex(d => d.classList.contains('active'));
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        const next = Math.min(currentIdx + 1, slides.length - 1);
        slides[next].scrollIntoView({ behavior: 'smooth' });
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const prev = Math.max(currentIdx - 1, 0);
        slides[prev].scrollIntoView({ behavior: 'smooth' });
      }
    });
  </script>
"""

# ── Step 8: Assemble cleanly ──
final = chunk_head + '\n'
final += '<body>\n'
final += '  <div class="ey-logo-bottom"><img src="assets/ey_logo.png" alt="EY Logo" style="width: 100%; display: block;"></div>\n'
final += '  <div class="ey-footer"></div>\n\n'
final += nav_dots_html + '\n'
for sec in renumbered:
    final += sec + '\n\n'
final += tech_slides
final += script
final += '\n</body>\n</html>\n'

with open('presentation/master_deck.html', 'w') as f:
    f.write(final)

print(f"Done! {total_slides} slides, single </html> at end.")
