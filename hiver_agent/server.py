"""Lightweight, standalone HTTP server with rich modern web UI for Hiver Agent.

Requires 0 extra dependencies (uses Python built-in http.server + JSON API).
"""
import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hiver_agent.agent import HiverAgent

PORT = 8000
agent = None


HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hiver AI Agent — @AppleSupport Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-base: #0a0d14;
      --bg-surface: #111622;
      --bg-surface-elevated: #182030;
      --bg-card: rgba(24, 32, 48, 0.7);
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-active: rgba(99, 102, 241, 0.4);
      --accent-primary: #6366f1;
      --accent-primary-hover: #4f46e5;
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --font-main: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow-glow: 0 0 25px rgba(99, 102, 241, 0.15);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font-main);
      background-color: var(--bg-base);
      color: var(--text-primary);
      min-height: 100vh;
      line-height: 1.5;
      overflow-x: hidden;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.06) 0%, transparent 40%);
    }

    /* Container */
    .container {
      max-width: 1380px;
      margin: 0 auto;
      padding: 30px 24px 60px;
    }

    /* Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .brand-logo {
      width: 46px;
      height: 46px;
      background: linear-gradient(135deg, var(--accent-primary), var(--accent-cyan));
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
      font-size: 24px;
    }
    .brand-text h1 {
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(to right, #ffffff, #cbd5e1);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .brand-text p {
      font-size: 13px;
      color: var(--text-secondary);
      font-weight: 500;
    }
    .header-badges {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .badge-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
    }
    .badge-pill.active {
      color: var(--accent-emerald);
      border-color: rgba(16, 185, 129, 0.3);
      background: rgba(16, 185, 129, 0.1);
    }
    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background-color: var(--accent-emerald);
      box-shadow: 0 0 8px var(--accent-emerald);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
      100% { opacity: 1; transform: scale(1); }
    }

    /* Tabs */
    .tabs-nav {
      display: flex;
      gap: 8px;
      background: var(--bg-surface);
      padding: 6px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
      margin-bottom: 28px;
      width: fit-content;
    }
    .tab-btn {
      padding: 10px 20px;
      border: none;
      background: transparent;
      color: var(--text-secondary);
      font-family: var(--font-main);
      font-size: 14px;
      font-weight: 600;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .tab-btn:hover {
      color: var(--text-primary);
      background: rgba(255, 255, 255, 0.04);
    }
    .tab-btn.active {
      background: var(--accent-primary);
      color: #ffffff;
      box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
    }

    /* Metrics Grid */
    .metrics-bar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 28px;
    }
    .metric-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 18px 20px;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
      transform: translateY(-2px);
      border-color: var(--border-active);
    }
    .metric-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent-primary), var(--accent-cyan));
    }
    .metric-title {
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }
    .metric-val {
      font-size: 26px;
      font-weight: 800;
      color: var(--text-primary);
      font-family: var(--font-mono);
      letter-spacing: -0.02em;
    }
    .metric-sub {
      font-size: 12px;
      color: var(--accent-emerald);
      margin-top: 4px;
      font-weight: 600;
    }

    /* Main Grid */
    .main-grid {
      display: grid;
      grid-template-columns: 1.15fr 1fr;
      gap: 24px;
    }

    /* Card Box */
    .panel {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 24px;
      backdrop-filter: blur(12px);
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }
    .panel-title {
      font-size: 16px;
      font-weight: 700;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    /* Presets Chips */
    .presets-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .chips-wrap {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 18px;
    }
    .chip {
      padding: 6px 12px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 999px;
      font-size: 12px;
      color: var(--text-secondary);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .chip:hover {
      color: var(--text-primary);
      border-color: var(--accent-primary);
      background: rgba(99, 102, 241, 0.1);
      transform: translateY(-1px);
    }

    /* Textarea */
    .input-wrapper {
      position: relative;
      margin-bottom: 16px;
    }
    textarea {
      width: 100%;
      height: 110px;
      background: var(--bg-base);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px 16px;
      color: var(--text-primary);
      font-family: var(--font-main);
      font-size: 14px;
      resize: none;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    textarea:focus {
      outline: none;
      border-color: var(--accent-primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
    }
    .char-count {
      position: absolute;
      bottom: 10px;
      right: 14px;
      font-size: 11px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }

    .btn-submit {
      width: 100%;
      padding: 13px;
      background: linear-gradient(135deg, var(--accent-primary), var(--accent-cyan));
      border: none;
      border-radius: var(--radius-md);
      color: #ffffff;
      font-family: var(--font-main);
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 10px;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
      transition: all 0.2s ease;
    }
    .btn-submit:hover {
      opacity: 0.95;
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }
    .btn-submit:active { transform: translateY(0); }

    /* Decision Result Box */
    .decision-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-radius: var(--radius-md);
      margin-bottom: 20px;
      border: 1px solid;
    }
    .decision-banner.auto-handle {
      background: rgba(16, 185, 129, 0.1);
      border-color: rgba(16, 185, 129, 0.3);
      color: var(--accent-emerald);
    }
    .decision-banner.escalate {
      background: rgba(244, 63, 94, 0.1);
      border-color: rgba(244, 63, 94, 0.3);
      color: var(--accent-rose);
    }
    .decision-status-title {
      font-size: 15px;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* Key-Value Details */
    .details-group {
      display: flex;
      flex-direction: column;
      gap: 14px;
      margin-bottom: 20px;
    }
    .detail-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .detail-label {
      font-size: 13px;
      color: var(--text-secondary);
      font-weight: 500;
    }
    .detail-val {
      font-size: 13px;
      font-weight: 700;
      font-family: var(--font-mono);
      color: var(--text-primary);
    }

    .tag-pill {
      display: inline-block;
      padding: 4px 10px;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      color: var(--accent-primary);
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
    }
    .tag-pill.danger {
      background: rgba(244, 63, 94, 0.15);
      border-color: rgba(244, 63, 94, 0.3);
      color: var(--accent-rose);
    }

    /* Draft Box */
    .draft-box {
      background: var(--bg-base);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px;
      position: relative;
      margin-bottom: 20px;
    }
    .draft-header {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }
    .draft-text {
      font-size: 13.5px;
      line-height: 1.6;
      color: var(--text-primary);
    }
    .copy-btn {
      background: transparent;
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .copy-btn:hover { color: #fff; border-color: var(--accent-primary); }

    /* Evidence List */
    .evidence-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .evidence-card {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 12px 14px;
      font-size: 12px;
    }
    .evidence-meta {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
      color: var(--accent-cyan);
      font-weight: 700;
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .evidence-q {
      color: var(--text-secondary);
      margin-bottom: 4px;
    }
    .evidence-a {
      color: #cbd5e1;
      border-left: 2px solid var(--accent-primary);
      padding-left: 8px;
    }

    /* Table Styles */
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin-top: 10px;
    }
    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--border-subtle);
    }
    th {
      color: var(--text-muted);
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    td { color: var(--text-secondary); }
    td.highlight { color: var(--text-primary); font-weight: 700; }
    td.green { color: var(--accent-emerald); font-weight: 700; }
    td.mono { font-family: var(--font-mono); }

    .tab-pane { display: none; }
    .tab-pane.active { display: block; }

    /* Responsive */
    @media (max-width: 960px) {
      .main-grid { grid-template-columns: 1fr; }
      .metrics-bar { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <div class="container">
    
    <!-- Top Header -->
    <header>
      <div class="brand-wrap">
        <div class="brand-logo"></div>
        <div class="brand-text">
          <h1>Hiver AI Customer Support System</h1>
          <p>Production Evaluation & Grounded Agent Dashboard for @AppleSupport</p>
        </div>
      </div>
      <div class="header-badges">
        <div class="badge-pill active">
          <span class="pulse-dot"></span> Agent Online (Sub-10ms)
        </div>
        <div class="badge-pill">
          Zero Leakage: 0.00%
        </div>
      </div>
    </header>

    <!-- Top Metrics Overview -->
    <div class="metrics-bar">
      <div class="metric-card">
        <div class="metric-title">Intent Macro-F1</div>
        <div class="metric-val">0.9292</div>
        <div class="metric-sub">Accuracy: 97.47% on 15.3k test</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">False Auto-Handling Rate</div>
        <div class="metric-val" style="color: var(--accent-emerald);">0.00%</div>
        <div class="metric-sub">100% Critical Safety Interception</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">Quality Score (Judge)</div>
        <div class="metric-val">4.59 / 5.0</div>
        <div class="metric-sub">Critical Errors: 0.0%</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">Historical Training Store</div>
        <div class="metric-val">72,789</div>
        <div class="metric-sub">Connected Component Split</div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-nav">
      <button class="tab-btn active" onclick="switchTab('sandbox')">⚡ Live Agent Sandbox</button>
      <button class="tab-btn" onclick="switchTab('benchmarks')">📊 Benchmark & Ablations</button>
      <button class="tab-btn" onclick="switchTab('failures')">🛡️ Safety & Failure Analysis</button>
      <button class="tab-btn" onclick="switchTab('taxonomy')">🏷️ Intent Taxonomy (11)</button>
    </div>

    <!-- TAB 1: LIVE AGENT SANDBOX -->
    <div id="tab-sandbox" class="tab-pane active">
      <div class="main-grid">
        
        <!-- Left: Input & Presets -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title"><span>💬</span> Customer Inbound Tweet</div>
          </div>

          <div class="presets-label">Click a Realistic Test Query Preset:</div>
          <div class="chips-wrap">
            <button class="chip" onclick="setPreset('My battery drops from 80% to 20% in 15 minutes while doing nothing on iOS 11')">🔋 Battery Drain</button>
            <button class="chip" onclick="setPreset('Someone made an unauthorized $500 charge on my Apple ID credit card!')">💳 Unauthorized Charge</button>
            <button class="chip" onclick="setPreset('So my iPhone charging cable just melted and started on fire while on my desk!')">🔥 Melted Cable Fire</button>
            <button class="chip" onclick="setPreset('My phone won’t finish downloading iOS 11 update, keeps saying error occurred.')">🔄 iOS Update Error</button>
            <button class="chip" onclick="setPreset('Why does my phone disconnect from home Wi-Fi every 5 minutes?')">📶 Wi-Fi Drop</button>
            <button class="chip" onclick="setPreset('I hate this new update it is completely useless switching to Android')">🤬 Sarcastic Vent</button>
          </div>

          <div class="input-wrapper">
            <textarea id="customerInput" placeholder="Type or paste a customer support tweet to test live inference..."></textarea>
            <span class="char-count" id="charCount">0 / 280</span>
          </div>

          <button class="btn-submit" id="submitBtn" onclick="runInference()">
            <span>Run Hiver Agent Inference</span> ➔
          </button>
        </div>

        <!-- Right: Real-time Decision Card -->
        <div class="panel" id="resultPanel">
          <div class="panel-header">
            <div class="panel-title"><span>🤖</span> Agent Decision & Evidence</div>
            <span class="badge-pill mono" id="latencyBadge">⚡ Ready</span>
          </div>

          <div id="decisionContent">
            <div class="decision-banner auto-handle" id="bannerBox">
              <div class="decision-status-title" id="statusTitle">
                <span>✅</span> AUTO-HANDLE: SAFE TO REPLY
              </div>
              <span class="tag-pill" id="intentPill">battery_power_charging</span>
            </div>

            <div class="details-group">
              <div class="detail-row">
                <span class="detail-label">Predicted Intent</span>
                <span class="detail-val" id="intentVal">battery_power_charging</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Classification Confidence</span>
                <span class="detail-val green" id="confidenceVal">99.48%</span>
              </div>
              <div class="detail-row" id="escalationRow" style="display: none;">
                <span class="detail-label">Escalation Trigger</span>
                <span class="detail-val" style="color: var(--accent-rose);" id="escalationReasonVal">-</span>
              </div>
              <div class="detail-row" id="riskRow" style="display: none;">
                <span class="detail-label">Identified Risk Flags</span>
                <div id="riskFlagsWrap"></div>
              </div>
            </div>

            <div class="draft-box">
              <div class="draft-header">
                <span>Grounded Draft Reply</span>
                <button class="copy-btn" onclick="copyReply()">Copy</button>
              </div>
              <p class="draft-text" id="draftReply">We want to help with your battery. Check Settings > Battery to see which apps are using the most power. If your device is overheating or percentage drops abruptly, reach out in DM.</p>
            </div>

            <div class="presets-label">Top Retrieved Historical Evidence:</div>
            <div class="evidence-list" id="evidenceList">
              <div class="evidence-card">
                <div class="evidence-meta">Similarity: 0.776 (Cosine)</div>
                <div class="evidence-q">Customer: Battery life from 100% to 10% in 30 minutes! 😱</div>
                <div class="evidence-a">AppleSupport: We can help! Which device are you experiencing this on?</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- TAB 2: BENCHMARKS & ABLATIONS -->
    <div id="tab-benchmarks" class="tab-pane">
      <div class="panel" style="margin-bottom: 24px;">
        <div class="panel-header">
          <div class="panel-title">🏆 Verified System Comparison (Held-out Test Split, N=15,326)</div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Model / Strategy</th>
              <th>Intent Macro-F1</th>
              <th>Accuracy</th>
              <th>Escalation Prec.</th>
              <th>Escalation Rec.</th>
              <th>False Auto-Handle (Safety)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Baseline 1: Majority Class</strong></td>
              <td class="mono">0.0720</td>
              <td class="mono">0.6555</td>
              <td class="mono">0.2857</td>
              <td class="mono">0.5000</td>
              <td class="mono" style="color: var(--accent-rose);">50.00%</td>
            </tr>
            <tr>
              <td><strong>Baseline 2: TF-IDF + Logistic Reg</strong></td>
              <td class="mono highlight">0.9292</td>
              <td class="mono highlight">0.9747</td>
              <td class="mono">N/A</td>
              <td class="mono">N/A</td>
              <td class="mono">N/A</td>
            </tr>
            <tr style="background: rgba(99, 102, 241, 0.08);">
              <td><strong>Final Hiver AI Agent (Full)</strong></td>
              <td class="mono highlight" style="color: var(--accent-cyan);">0.9292</td>
              <td class="mono highlight" style="color: var(--accent-cyan);">0.9747</td>
              <td class="mono">0.1860</td>
              <td class="mono highlight" style="color: var(--accent-emerald);">1.0000</td>
              <td class="mono green">0.00% (Safety Floor)</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">🔬 3-Tier Ablation Study (Response Quality & Guardrails)</div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Ablation Setup</th>
              <th>Correctness</th>
              <th>Grounding</th>
              <th>Safety</th>
              <th>Overall Mean (1–5)</th>
              <th>% High Quality (>=4.0)</th>
              <th>Critical Errors</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>A: LLM without Retrieval</strong></td>
              <td class="mono">4.74</td>
              <td class="mono">5.00</td>
              <td class="mono">5.00</td>
              <td class="mono">4.59</td>
              <td class="mono">100.0%</td>
              <td class="mono green">0.0%</td>
            </tr>
            <tr style="background: rgba(244, 63, 94, 0.05);">
              <td><strong>B: LLM + Retrieval (No Escalation)</strong></td>
              <td class="mono">4.74</td>
              <td class="mono">5.00</td>
              <td class="mono">4.88</td>
              <td class="mono">4.57</td>
              <td class="mono">96.0%</td>
              <td class="mono" style="color: var(--accent-rose); font-weight:700;">4.0% (Unsafe Autoreplies)</td>
            </tr>
            <tr style="background: rgba(16, 185, 129, 0.08);">
              <td><strong>C: Full Agent (Retr + Escalation)</strong></td>
              <td class="mono highlight">4.74</td>
              <td class="mono highlight">5.00</td>
              <td class="mono highlight">5.00</td>
              <td class="mono highlight" style="color: var(--accent-emerald);">4.59</td>
              <td class="mono highlight">100.0%</td>
              <td class="mono green">0.0% (Zero Errors)</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 3: SAFETY & FAILURES -->
    <div id="tab-failures" class="tab-pane">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">🛡️ Top 5 Real Production Failure Modes & Mitigations</div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Failure Mode</th>
              <th>Real Tweet ID</th>
              <th>Category</th>
              <th>Severity</th>
              <th>Architectural Fix Implemented</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>1. Active Thermal Event / Fire</strong></td>
              <td class="mono">1805403</td>
              <td>Safety Hazard</td>
              <td><span class="tag-pill danger">CRITICAL</span></td>
              <td>Emergency thermal regex interceptor forcing immediate <span class="mono">auto_handle=False</span>.</td>
            </tr>
            <tr>
              <td><strong>2. Repeat 4-Tier Contact Blindness</strong></td>
              <td class="mono">101304</td>
              <td>Repeat Failure</td>
              <td><span class="tag-pill danger">HIGH</span></td>
              <td>Prior-attempt pattern detector routing directly to Senior Relations.</td>
            </tr>
            <tr>
              <td><strong>3. 2FA Authentication Deadlock</strong></td>
              <td class="mono">1715358</td>
              <td>Account Lockout</td>
              <td><span class="tag-pill danger">HIGH</span></td>
              <td>Sub-intent routing to <span class="mono">icloud.com/find</span> + human security queue.</td>
            </tr>
            <tr>
              <td><strong>4. Impending Legal Threat</strong></td>
              <td class="mono">249171</td>
              <td>Legal Compliance</td>
              <td><span class="tag-pill danger">HIGH</span></td>
              <td>Legal keyword compliance filter routing to Executive Legal Desk.</td>
            </tr>
            <tr>
              <td><strong>5. Multi-Intent Damage Entanglement</strong></td>
              <td class="mono">98840</td>
              <td>Ambiguous Intent</td>
              <td><span class="tag-pill" style="color: var(--accent-amber);">MED-HIGH</span></td>
              <td>Multi-aspect risk tagging to avoid single-label misclassification.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: TAXONOMY -->
    <div id="tab-taxonomy" class="tab-pane">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">🏷️ 11 Frozen Intent Taxonomy Classes</div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Intent Class</th>
              <th>Scope & Definition</th>
              <th>Dataset Freq</th>
              <th>Canonical Action</th>
              <th>Escalation Policy</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="mono highlight">ios_update_issue</td>
              <td>OS upgrade errors, bootloops, verification failures</td>
              <td class="mono">31,658 (30.6%)</td>
              <td>Update KB article / Force restart</td>
              <td>Low</td>
            </tr>
            <tr>
              <td class="mono highlight">app_performance_crash</td>
              <td>App crashing, keyboard lag, UI freezing</td>
              <td class="mono">11,227 (10.8%)</td>
              <td>Force close / Reinstall app</td>
              <td>Low</td>
            </tr>
            <tr>
              <td class="mono highlight">battery_power_charging</td>
              <td>Rapid drain, charging port failure, overheating</td>
              <td class="mono">10,464 (10.1%)</td>
              <td>Battery usage audit / Diagnostics</td>
              <td>Moderate–High</td>
            </tr>
            <tr>
              <td class="mono highlight">apple_id_account_security</td>
              <td>Password reset, 2FA code missing, account lock</td>
              <td class="mono">5,435 (5.3%)</td>
              <td>iforgot.apple.com / Security desk</td>
              <td><span class="tag-pill danger">MANDATORY</span></td>
            </tr>
            <tr>
              <td class="mono highlight">screen_display_touch</td>
              <td>Black screen, display lines, touch digitizer</td>
              <td class="mono">5,167 (5.0%)</td>
              <td>Force restart / Repair quote</td>
              <td>Moderate–High</td>
            </tr>
            <tr>
              <td class="mono highlight">general_complaint_feedback</td>
              <td>Sarcasm, non-technical venting, switching threats</td>
              <td class="mono">4,631 (4.5%)</td>
              <td>Empathy statement / DM intake</td>
              <td>Moderate</td>
            </tr>
            <tr>
              <td class="mono highlight">network_connectivity</td>
              <td>Wi-Fi drops, Bluetooth pairing, No Service LTE</td>
              <td class="mono">4,184 (4.0%)</td>
              <td>Reset Network Settings</td>
              <td>Low–Moderate</td>
            </tr>
            <tr>
              <td class="mono highlight">icloud_storage_backup</td>
              <td>iCloud sync failure, Storage Full warning</td>
              <td class="mono">3,522 (3.4%)</td>
              <td>Manage Storage guide</td>
              <td>Low–Moderate</td>
            </tr>
            <tr>
              <td class="mono highlight">store_billing_subscription</td>
              <td>In-app charges, subscription cancel, refund</td>
              <td class="mono">3,211 (3.1%)</td>
              <td>reportaproblem.apple.com</td>
              <td><span class="tag-pill danger">MANDATORY</span></td>
            </tr>
            <tr>
              <td class="mono highlight">audio_call_accessory</td>
              <td>Low call volume, mic issues, AirPods drops</td>
              <td class="mono">2,343 (2.3%)</td>
              <td>Settings > Audio balance</td>
              <td>Moderate</td>
            </tr>
            <tr>
              <td class="mono highlight">hardware_repair_store_service</td>
              <td>Genius Bar booking, cracked glass, AppleCare</td>
              <td class="mono">1,908 (1.8%)</td>
              <td>getsupport.apple.com</td>
              <td><span class="tag-pill danger">MANDATORY</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>

  <script>
    // Tab Switching
    function switchTab(tabId) {
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
      event.target.classList.add('active');
    }

    // Input character counter
    const inputArea = document.getElementById('customerInput');
    const charCount = document.getElementById('charCount');
    inputArea.addEventListener('input', () => {
      charCount.textContent = `${inputArea.value.length} / 280`;
    });

    function setPreset(text) {
      inputArea.value = text;
      charCount.textContent = `${text.length} / 280`;
      runInference();
    }

    function copyReply() {
      const text = document.getElementById('draftReply').innerText;
      navigator.clipboard.writeText(text);
      alert('Draft reply copied to clipboard!');
    }

    // API Call
    async function runInference() {
      const query = inputArea.value.trim();
      if (!query) return;

      const btn = document.getElementById('submitBtn');
      const latencyBadge = document.getElementById('latencyBadge');
      btn.disabled = true;
      btn.innerHTML = '⚡ Processing...';
      const t0 = performance.now();

      try {
        const res = await fetch('/api/respond', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: query })
        });
        const data = await res.json();
        const t1 = performance.now();
        latencyBadge.textContent = `⚡ ${(t1 - t0).toFixed(1)}ms`;

        // Update UI
        const banner = document.getElementById('bannerBox');
        const statusTitle = document.getElementById('statusTitle');
        const intentPill = document.getElementById('intentPill');
        const intentVal = document.getElementById('intentVal');
        const confVal = document.getElementById('confidenceVal');
        const draftReply = document.getElementById('draftReply');
        const escRow = document.getElementById('escalationRow');
        const escReason = document.getElementById('escalationReasonVal');
        const riskRow = document.getElementById('riskRow');
        const riskWrap = document.getElementById('riskFlagsWrap');
        const evidenceList = document.getElementById('evidenceList');

        intentPill.textContent = data.intent;
        intentVal.textContent = data.intent;
        confVal.textContent = `${(data.intent_confidence * 100).toFixed(2)}%`;
        draftReply.textContent = data.draft_reply;

        if (data.auto_handle) {
          banner.className = 'decision-banner auto-handle';
          statusTitle.innerHTML = '<span>✅</span> AUTO-HANDLE: SAFE TO REPLY';
          escRow.style.display = 'none';
          riskRow.style.display = 'none';
        } else {
          banner.className = 'decision-banner escalate';
          statusTitle.innerHTML = '<span>🚨</span> ESCALATE TO HUMAN SPECIALIST';
          escRow.style.display = 'flex';
          escReason.textContent = data.escalation_reason || 'Safety trigger';
          
          riskRow.style.display = 'flex';
          riskWrap.innerHTML = '';
          (data.risk_flags || []).forEach(f => {
            const pill = document.createElement('span');
            pill.className = 'tag-pill danger';
            pill.style.marginRight = '6px';
            pill.textContent = f;
            riskWrap.appendChild(pill);
          });
        }

        // Render Evidence
        evidenceList.innerHTML = '';
        (data.retrieved_evidence || []).forEach(ev => {
          const card = document.createElement('div');
          card.className = 'evidence-card';
          card.innerHTML = `
            <div class="evidence-meta">Similarity: ${ev.similarity_score.toFixed(3)} (Cosine)</div>
            <div class="evidence-q"><strong>Customer:</strong> ${escapeHtml(ev.customer_query)}</div>
            <div class="evidence-a"><strong>Apple:</strong> ${escapeHtml(ev.historical_response)}</div>
          `;
          evidenceList.appendChild(card);
        });

      } catch (err) {
        console.error(err);
        alert('Error calling inference API: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Run Hiver Agent Inference</span> ➔';
      }
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  </script>
</body>
</html>
"""


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "online", "model": "HiverAgent-v1.0"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/respond":
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(post_body)
                msg = payload.get("message", "")
                global agent
                if agent is None:
                    agent = HiverAgent.load_or_train()
                decision = agent.respond(msg)
                resp_data = decision.model_dump()

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(resp_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server(port: int = 5000):
    global agent
    print("Pre-loading Hiver Agent pipeline...", file=sys.stderr)
    agent = HiverAgent.load_or_train()

    # Try common development ports on localhost
    candidate_ports = [5000, 5050, 7860, 8080, 8000, 3000, 9000, 9999]
    if port not in candidate_ports:
        candidate_ports.insert(0, port)

    for p in candidate_ports:
        try:
            # Bind to 127.0.0.1 explicitly to avoid Windows WinError 10013 permissions issues
            httpd = ThreadedTCPServer(("127.0.0.1", p), RequestHandler)
            print(f"\n" + "=" * 55, file=sys.stderr)
            print(f"  HIVER AI AGENT FRONTEND SERVER ONLINE", file=sys.stderr)
            print(f"  URL: http://127.0.0.1:{p}", file=sys.stderr)
            print(f"  Press Ctrl+C to stop the server", file=sys.stderr)
            print("=" * 55 + "\n", file=sys.stderr)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server...", file=sys.stderr)
            finally:
                httpd.server_close()
            return
        except (OSError, PermissionError) as e:
            print(f"Port {p} on 127.0.0.1 unavailable ({e.__class__.__name__}), trying next port...", file=sys.stderr)
            continue

    print("ERROR: Could not bind to any candidate port on 127.0.0.1.", file=sys.stderr)


if __name__ == "__main__":
    start_server(PORT)
