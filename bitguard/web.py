DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BitGuard Sentinel</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Material+Symbols+Outlined:wght@200..600&display=swap" rel="stylesheet">
  <style>
    :root {
      color-scheme: light;
      --ink: #20242a;
      --muted: #5c6670;
      --line: #d9e0e6;
      --paper: #f5f7f8;
      --panel: #ffffff;
      --soft: #eef3f5;
      --accent: #087f8c;
      --accent-dark: #06616b;
      --good: #197a4d;
      --bad: #b42318;
      --warn: #a15c00;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--paper);
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 20px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }
    h1 { margin: 0; font-size: 20px; letter-spacing: 0; }
    h2 { margin: 0; font-size: 14px; letter-spacing: 0; }
    main {
      display: grid;
      grid-template-columns: minmax(340px, 440px) minmax(0, 1fr);
      gap: 14px;
      padding: 14px;
      align-items: start;
    }
    section {
      min-width: 0;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .panel-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-height: 48px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
    }
    .status, .badge { color: var(--muted); font-size: 12px; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 0 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      white-space: nowrap;
    }
    .ok { color: var(--good); }
    .bad { color: var(--bad); }
    textarea {
      display: block;
      width: 100%;
      min-height: calc(100vh - 186px);
      padding: 14px;
      border: 0;
      resize: vertical;
      outline: none;
      color: var(--ink);
      font: 12px/1.5 "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 12px 14px;
      border-top: 1px solid var(--line);
    }
    button, .file-label {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
      padding: 0 11px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      cursor: pointer;
      font-size: 13px;
      white-space: nowrap;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      font-weight: 700;
    }
    button.primary:hover { background: var(--accent-dark); }
    input[type="file"] { display: none; }
    .workspace { overflow: hidden; }
    .tabs {
      display: flex;
      gap: 4px;
      padding: 8px;
      border-bottom: 1px solid var(--line);
      background: var(--soft);
      overflow-x: auto;
    }
    .tab-button {
      border-color: transparent;
      background: transparent;
      color: var(--muted);
      min-width: 92px;
    }
    .tab-button.active {
      background: var(--panel);
      border-color: var(--line);
      color: var(--ink);
      font-weight: 700;
    }
    .tab-panel { display: none; padding: 14px; }
    .tab-panel.active { display: block; }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(130px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }
    .metric {
      min-height: 76px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }
    .metric span { display: block; color: var(--muted); font-size: 12px; }
    .metric strong {
      display: block;
      margin-top: 6px;
      font-size: 20px;
      line-height: 1.2;
      letter-spacing: 0;
      word-break: break-word;
    }
    .split {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(240px, 320px);
      gap: 14px;
      align-items: start;
    }
    .findings, .stack { display: grid; gap: 8px; }
    .finding, .mini-panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
    }
    .finding strong, .mini-panel strong {
      display: block;
      font-size: 13px;
      margin-bottom: 4px;
    }
    .finding p, .mini-panel p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
      font-size: 13px;
    }
    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }
    th {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      background: #fbfcfd;
    }
    tr:last-child td { border-bottom: 0; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .positive { color: var(--good); font-weight: 700; }
    .negative { color: var(--bad); font-weight: 700; }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 0 7px;
      border-radius: 999px;
      background: var(--soft);
      color: var(--muted);
      font-size: 12px;
    }
    .raw-toolbar {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }
    .output {
      max-height: calc(100vh - 210px);
      overflow: auto;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      font: 12px/1.5 "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre-wrap;
    }
    @media (max-width: 1080px) {
      main { grid-template-columns: 1fr; }
      textarea { min-height: 340px; }
      .metric-grid { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
      .split { grid-template-columns: 1fr; }
    }
    @media (max-width: 560px) {
      header { align-items: flex-start; flex-direction: column; }
      .metric-grid { grid-template-columns: 1fr; }
      .tab-button { min-width: 84px; }
    }

    /* Stitch operational dashboard layer */
    :root {
      --ink: #191c1e;
      --muted: #3d4947;
      --line: #e2e8f0;
      --line-strong: #bcc9c6;
      --paper: #f7f9fb;
      --panel: #ffffff;
      --soft: #f2f4f6;
      --accent: #0d9488;
      --accent-dark: #00685f;
      --good: #10b981;
      --bad: #ef4444;
      --warn: #f59e0b;
      --info: #0ea5e9;
      --sidebar: 240px;
      --topbar: 64px;
    }
    body {
      height: 100vh;
      display: grid;
      grid-template-columns: var(--sidebar) minmax(0, 1fr);
      grid-template-rows: var(--topbar) minmax(0, 1fr);
      overflow: hidden;
      background: var(--paper);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 13px;
      line-height: 1.4;
    }
    header {
      grid-column: 2;
      grid-row: 1;
      height: var(--topbar);
      padding: 0 24px;
      background: rgba(255, 255, 255, 0.96);
      border-bottom: 1px solid var(--line-strong);
      z-index: 5;
    }
    header h1 {
      font-size: 16px;
      line-height: 20px;
      font-weight: 700;
    }
    header h1::after {
      content: "Network Status    Engine Logs    Risk Limits";
      margin-left: 22px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      white-space: pre;
    }
    #health {
      min-height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      border-color: var(--line);
      background: var(--panel);
      font-weight: 700;
    }
    #health::before {
      content: "";
      width: 8px;
      height: 8px;
      margin-right: 7px;
      border-radius: 999px;
      background: #94a3b8;
      display: inline-block;
    }
    #health.ok::before { background: var(--good); }
    #health.bad::before { background: var(--bad); }
    main {
      grid-column: 1 / 3;
      grid-row: 1 / 3;
      height: 100vh;
      display: grid;
      grid-template-columns: var(--sidebar) minmax(0, 1fr);
      grid-template-rows: var(--topbar) minmax(0, 1fr);
      gap: 0;
      padding: 0;
      align-items: stretch;
      background: var(--paper);
    }
    main > section:first-child {
      grid-column: 1;
      grid-row: 1 / 3;
      z-index: 6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      border: 0;
      border-right: 1px solid var(--line-strong);
      border-radius: 0;
      background: var(--panel);
      overflow: hidden;
    }
    main > section:first-child .panel-title {
      display: block;
      min-height: 0;
      padding: 16px 16px 10px;
      border-bottom: 1px solid var(--line);
    }
    main > section:first-child .panel-title::before {
      content: "BitGuard Sentinel";
      display: block;
      color: var(--accent-dark);
      font-size: 18px;
      line-height: 24px;
      font-weight: 700;
    }
    main > section:first-child .panel-title::after {
      content: "Audit agent trading behavior without sharing API keys.";
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
      line-height: 15px;
    }
    main > section:first-child .panel-title h2 {
      margin-top: 18px;
      color: var(--muted);
      font-size: 12px;
      line-height: 16px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    main > section:first-child .panel-title .status { display: none; }
    textarea {
      flex: 1;
      min-height: 260px;
      height: auto;
      margin: 16px;
      width: calc(100% - 32px);
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: var(--soft);
      font-size: 12px;
    }
    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.18);
      background: var(--panel);
    }
    .actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      padding: 0 16px 16px;
      border-top: 0;
    }
    .actions button:first-child,
    .actions .file-label {
      grid-column: 1 / -1;
    }
    button, .file-label {
      min-height: 36px;
      border-radius: 8px;
      border-color: var(--line);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
      transition: border-color 140ms ease, background-color 140ms ease, color 140ms ease, transform 80ms ease;
    }
    button:hover, .file-label:hover { border-color: #cbd5e1; }
    button:active, .file-label:active { transform: scale(0.985); }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }
    button.primary:hover { background: var(--accent-dark); border-color: var(--accent-dark); }
    .actions button::before,
    .file-label::before,
    .tab-button::before {
      font-family: "Material Symbols Outlined";
      font-size: 18px;
      line-height: 1;
      font-weight: normal;
      font-style: normal;
      font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 20;
      display: inline-block;
      margin-right: 7px;
      vertical-align: -3px;
    }
    .actions button:nth-child(1)::before { content: "play_arrow"; }
    .actions button:nth-child(2)::before { content: "science"; }
    .actions button:nth-child(3)::before { content: "shield"; }
    .file-label::before { content: "file_open"; }
    main > section:first-child::after {
      content: "Dashboard accepts exported logs only. API keys stay local.";
      margin: auto 16px 16px;
      color: var(--outline, #6d7a77);
      font-size: 11px;
      line-height: 15px;
      text-align: center;
    }
    .workspace {
      grid-column: 2;
      grid-row: 2;
      height: calc(100vh - var(--topbar));
      padding: 24px;
      border: 0;
      border-radius: 0;
      background: var(--paper);
      overflow-y: auto;
    }
    .workspace > .panel-title {
      min-height: 42px;
      padding: 0 0 14px;
      border-bottom: 0;
      background: transparent;
    }
    .workspace > .panel-title h2 {
      font-size: 18px;
      line-height: 24px;
      font-weight: 700;
    }
    #state {
      min-height: 26px;
      padding: 0 9px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--panel);
      font-weight: 700;
    }
    .tabs {
      gap: 2px;
      padding: 8px;
      margin-bottom: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }
    .tab-button {
      min-width: 0;
      min-height: 38px;
      border-radius: 6px;
      color: #505f76;
      justify-content: flex-start;
      padding: 0 10px;
      font-weight: 700;
    }
    #tab-overview::before { content: "dashboard"; }
    #tab-patterns::before { content: "schema"; }
    #tab-orders::before { content: "receipt_long"; }
    #tab-perception::before { content: "radar"; }
    #tab-exposure::before { content: "monitoring"; }
    #tab-connect::before { content: "hub"; }
    #tab-raw::before { content: "description"; }
    .tab-button.active {
      background: var(--soft);
      border-color: transparent;
      color: var(--accent-dark);
    }
    .tab-panel { padding: 0; }
    .metric-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .metric {
      min-height: 96px;
      padding: 14px;
      border-radius: 8px;
      border-color: var(--line);
    }
    .metric span {
      color: var(--muted);
      font-size: 11px;
      line-height: 14px;
      font-weight: 600;
    }
    .metric strong {
      margin-top: 10px;
      font-size: 22px;
      line-height: 28px;
      font-weight: 700;
    }
    .split { grid-template-columns: minmax(0, 1fr) minmax(280px, 380px); gap: 16px; }
    .panel-title {
      background: var(--soft);
      min-height: 42px;
      padding: 10px 12px;
    }
    .finding, .mini-panel, .table-wrap, .output {
      border-color: var(--line);
      border-radius: 8px;
    }
    .findings { gap: 0; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: var(--panel); }
    .finding {
      display: grid;
      grid-template-columns: minmax(130px, 0.35fr) minmax(0, 1fr);
      gap: 8px 12px;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      padding: 9px 12px;
    }
    .finding:last-child { border-bottom: 0; }
    .finding strong {
      margin: 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 18px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .finding p { font-size: 13px; color: var(--ink); }
    table { font-size: 13px; }
    th {
      background: #f1f5f9;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    th, td { padding: 9px 12px; border-color: var(--line); }
    tbody tr:hover { background: #f8fafc; }
    .pill {
      min-height: 22px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
    }
    .positive { color: var(--good); }
    .negative { color: var(--bad); }
    .output { min-height: 520px; background: var(--panel); }
    .pattern-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }
    .pattern-card {
      min-height: 220px;
      display: grid;
      gap: 12px;
      align-content: start;
    }
    .condition-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }    @media (max-width: 1120px) {
      .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .split { grid-template-columns: 1fr; }
    }
    @media (max-width: 900px) {
      body { display: block; height: auto; overflow: auto; }
      header { height: auto; min-height: var(--topbar); padding: 12px 16px; }
      header h1::after { display: none; }
      main { display: block; height: auto; }
      main > section:first-child { min-height: 0; border-right: 0; border-bottom: 1px solid var(--line-strong); }
      textarea { height: 260px; }
      main > section:first-child::after { margin-top: 0; }
      .workspace { height: auto; padding: 16px; overflow: visible; }
      .tabs { overflow-x: auto; }
      .tab-button { white-space: nowrap; }
    }
    @media (max-width: 560px) {
      header { align-items: flex-start; flex-direction: column; }
      .actions { grid-template-columns: 1fr; }
      .metric-grid { grid-template-columns: 1fr; }
      .finding { grid-template-columns: 1fr; }
    }

    /* Sidebar brand polish */
    .rail-brand {
      padding: 16px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    .rail-brand h1 {
      margin: 0;
      color: var(--accent-dark);
      font-size: 18px;
      line-height: 24px;
      font-weight: 700;
      letter-spacing: 0;
    }
    .rail-brand p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 15px;
    }
    main > section:first-child .panel-title::before,
    main > section:first-child .panel-title::after {
      content: none;
      display: none;
    }
    main > section:first-child .panel-title {
      padding: 14px 16px 0;
      border-bottom: 0;
    }
    main > section:first-child .panel-title h2 { margin-top: 0; }
    button:focus-visible,
    .file-label:focus-visible,
    textarea:focus-visible {
      outline: 2px solid rgba(13, 148, 136, 0.24);
      outline-offset: 2px;
    }

    /* Black and blue theme */
    :root {
      --ink: #f4f8ff;
      --muted: #a8b3c4;
      --line: #243244;
      --line-strong: #33445c;
      --paper: #05070b;
      --panel: #0b1018;
      --soft: #101823;
      --accent: #38bdf8;
      --accent-dark: #0ea5e9;
      --good: #34d399;
      --bad: #fb7185;
      --warn: #fbbf24;
      --info: #60a5fa;
      --outline: #718096;
    }
    body, main, .workspace {
      background: var(--paper);
      color: var(--ink);
    }
    header {
      background: rgba(5, 7, 11, 0.96);
      border-bottom-color: var(--line-strong);
    }
    header h1,
    .workspace > .panel-title h2,
    .panel-head h2,
    .rail-brand h1,
    h1, h2 {
      color: var(--ink);
    }
    header h1::after,
    .rail-brand p,
    .status,
    .badge,
    .metric span,
    .finding strong,
    th,
    .mini-panel p,
    .note-row span:first-child {
      color: var(--muted);
    }
    #health,
    #state,
    main > section:first-child,
    .workspace > .panel-title,
    .tabs,
    .metric,
    .finding,
    .mini-panel,
    .table-wrap,
    .output,
    button,
    .file-label,
    textarea,
    section,
    .panel {
      background: var(--panel);
      border-color: var(--line);
      color: var(--ink);
    }
    .rail-brand,
    main > section:first-child .panel-title,
    .panel-title,
    .panel-head,
    .raw-toolbar,
    th {
      background: var(--soft);
      border-color: var(--line);
    }
    .rail-brand h1,
    main > section:first-child .panel-title::before,
    .tab-button.active,
    .tab-button.active::before,
    .file-label::before,
    .actions button::before {
      color: var(--accent);
    }
    textarea {
      background: #080d14;
      color: var(--ink);
      scrollbar-color: #475569 transparent;
    }
    textarea:focus {
      background: #0b111b;
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.22);
    }
    button:hover,
    .file-label:hover,
    .metric:hover,
    .panel:hover {
      border-color: #3b82f6;
    }
    button.primary {
      background: var(--accent-dark);
      border-color: var(--accent-dark);
      color: #03111d;
    }
    button.primary:hover {
      background: var(--accent);
      border-color: var(--accent);
      color: #020617;
    }
    .tab-button {
      color: var(--muted);
      background: transparent;
    }
    .tab-button.active {
      background: rgba(56, 189, 248, 0.12);
      border-color: rgba(56, 189, 248, 0.36);
      box-shadow: inset 0 0 0 1px rgba(56, 189, 248, 0.12);
    }
    .count-badge,
    .pill {
      background: #111827;
      border: 1px solid var(--line);
      color: var(--muted);
    }
    .metric strong,
    .note-row span:last-child,
    td,
    .finding p {
      color: var(--ink);
    }
    tbody tr:hover { background: #0f172a; }
    .findings { background: var(--panel); border-color: var(--line); }
    .positive { color: var(--good); }
    .negative { color: var(--bad); }
    #health.ok { color: var(--good); }
    #health.bad { color: var(--bad); }
    #health.ok::before { background: var(--good); }
    #health.bad::before { background: var(--bad); }
    .alert {
      background: rgba(251, 191, 36, 0.12);
      border-color: rgba(251, 191, 36, 0.42);
      color: #fde68a;
    }
    .badge.info { background: rgba(96, 165, 250, 0.14); color: #93c5fd; }
    .badge.medium { background: rgba(251, 191, 36, 0.14); color: #fcd34d; }
    .badge.high, .badge.error { background: rgba(251, 113, 133, 0.14); color: #fda4af; }
    .badge.low, .badge.ok { background: rgba(52, 211, 153, 0.14); color: #6ee7b7; }
    .badge.neutral { background: #111827; color: var(--muted); }
    button:focus-visible,
    .file-label:focus-visible,
    textarea:focus-visible {
      outline-color: rgba(56, 189, 248, 0.42);
    }
    ::selection { background: rgba(56, 189, 248, 0.35); color: var(--ink); }

    /* Order audit verdict flow */
    .order-verdict {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: center;
      margin-bottom: 14px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.12), rgba(11, 16, 24, 0.88));
    }
    .order-verdict h3 {
      margin: 0 0 6px;
      font-size: 20px;
      line-height: 26px;
      color: var(--ink);
    }
    .order-verdict p { margin: 0; color: var(--muted); line-height: 1.5; }
    .verdict-score {
      min-width: 116px;
      padding: 12px;
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 8px;
      text-align: center;
      background: rgba(5, 7, 11, 0.58);
    }
    .verdict-score strong { display: block; font-size: 28px; line-height: 32px; color: var(--accent); }
    .verdict-score span { color: var(--muted); font-size: 12px; }
    .order-audit-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(260px, 0.75fr);
      gap: 14px;
      align-items: start;
    }
    .verdict-pass { border-color: rgba(52, 211, 153, 0.42); }
    .verdict-watch { border-color: rgba(96, 165, 250, 0.42); }
    .verdict-caution { border-color: rgba(251, 191, 36, 0.48); }
    .verdict-fail { border-color: rgba(251, 113, 133, 0.48); }
    @media (max-width: 900px) {
      .order-verdict,
      .order-audit-grid { grid-template-columns: 1fr; }
      .verdict-score { min-width: 0; }
    }

    /* Taste-guided command center redesign */
    :root {
      --ink: #f6fbff;
      --muted: #91a7bd;
      --line: #1b2a3d;
      --line-strong: #2b6f9f;
      --paper: #03070c;
      --panel: #07111c;
      --panel-2: #0b1623;
      --soft: #0d1b2b;
      --accent: #46c7ff;
      --accent-dark: #168bd1;
      --good: #38d996;
      --bad: #ff6b87;
      --warn: #f7c948;
      --info: #63a8ff;
      --sidebar: 336px;
      --topbar: 68px;
    }
    body {
      background:
        linear-gradient(180deg, #07111d 0%, #04080f 42%, #03070c 100%);
      color: var(--ink);
      letter-spacing: 0;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(70, 199, 255, 0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(70, 199, 255, 0.045) 1px, transparent 1px);
      background-size: 36px 36px;
      mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), transparent 78%);
    }
    header,
    main {
      position: relative;
      z-index: 1;
    }
    header {
      height: var(--topbar);
      padding: 0 28px;
      background: rgba(3, 7, 12, 0.84);
      border-bottom: 1px solid rgba(70, 199, 255, 0.18);
      backdrop-filter: blur(18px);
    }
    header h1 {
      color: var(--ink);
      font-size: 13px;
      line-height: 18px;
      letter-spacing: 0.13em;
      text-transform: uppercase;
    }
    header h1::after {
      content: "Audit / Perception / Intelligence";
      margin-left: 24px;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.11em;
      text-transform: uppercase;
      white-space: nowrap;
    }
    #health,
    #state {
      min-height: 30px;
      border-color: rgba(70, 199, 255, 0.26);
      background: rgba(7, 17, 28, 0.88);
      color: var(--muted);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }
    main {
      grid-template-columns: var(--sidebar) minmax(0, 1fr);
      grid-template-rows: var(--topbar) minmax(0, 1fr);
      background: transparent;
    }
    main > section:first-child {
      background:
        linear-gradient(180deg, rgba(9, 20, 33, 0.98), rgba(4, 9, 16, 0.98));
      border-right: 1px solid rgba(70, 199, 255, 0.18);
      box-shadow: 18px 0 60px rgba(0, 0, 0, 0.24);
    }
    .rail-brand {
      padding: 22px 20px 18px;
      background: transparent;
      border-bottom: 1px solid rgba(70, 199, 255, 0.14);
    }
    .rail-brand h1 {
      color: var(--ink);
      font-size: 22px;
      line-height: 28px;
    }
    .rail-brand p {
      max-width: 26ch;
      color: var(--muted);
      font-size: 12px;
      line-height: 17px;
    }
    main > section:first-child .panel-title {
      padding: 18px 20px 8px;
      background: transparent;
    }
    main > section:first-child .panel-title h2 {
      color: #d9efff;
      font-size: 12px;
      line-height: 16px;
      letter-spacing: 0.1em;
    }
    textarea {
      width: calc(100% - 40px);
      margin: 14px 20px;
      min-height: calc(100vh - 250px);
      color: #cfe7f8;
      background: #050b13;
      border: 1px solid rgba(70, 199, 255, 0.2);
      border-radius: 10px;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
      line-height: 1.55;
    }
    textarea:focus {
      border-color: rgba(70, 199, 255, 0.72);
      box-shadow: 0 0 0 3px rgba(70, 199, 255, 0.16);
    }
    .actions {
      padding: 2px 20px 20px;
      gap: 10px;
    }
    .token-panel {
      margin: 0 20px 14px;
      padding: 12px;
      border: 1px solid rgba(70, 199, 255, 0.16);
      border-radius: 10px;
      background: rgba(5, 11, 19, 0.72);
    }
    .token-panel label {
      display: block;
      margin-bottom: 7px;
      color: #8fa8bd;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .token-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
    }
    input[type="password"] {
      min-width: 0;
      min-height: 38px;
      padding: 0 10px;
      color: #cfe7f8;
      background: #050b13;
      border: 1px solid rgba(70, 199, 255, 0.2);
      border-radius: 10px;
      outline: none;
    }
    input[type="password"]:focus {
      border-color: rgba(70, 199, 255, 0.72);
      box-shadow: 0 0 0 3px rgba(70, 199, 255, 0.16);
    }
    .code-snippet {
      margin: 8px 0 0;
      padding: 10px;
      overflow-x: auto;
      border: 1px solid rgba(70, 199, 255, 0.14);
      border-radius: 10px;
      background: #050b13;
      color: #cfe7f8;
      font: 11px/1.5 "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre-wrap;
    }
    button,
    .file-label {
      min-height: 38px;
      border-radius: 10px;
      border-color: rgba(70, 199, 255, 0.2);
      background: rgba(13, 27, 43, 0.9);
      color: #d9efff;
      font-weight: 700;
      letter-spacing: 0;
    }
    button:hover,
    .file-label:hover {
      border-color: rgba(70, 199, 255, 0.56);
      background: rgba(18, 41, 64, 0.95);
    }
    button.primary {
      color: #02111d;
      background: linear-gradient(180deg, #65d4ff, #1d9add);
      border-color: #78dcff;
      box-shadow: 0 12px 28px rgba(29, 154, 221, 0.24);
    }
    button.primary:hover {
      background: linear-gradient(180deg, #7bddff, #2aa8e8);
      border-color: #8ee3ff;
    }
    main > section:first-child::after {
      margin: auto 20px 18px;
      padding: 10px 12px;
      border: 1px solid rgba(70, 199, 255, 0.14);
      border-radius: 10px;
      background: rgba(5, 11, 19, 0.68);
      color: var(--muted);
    }
    .workspace {
      padding: 24px 30px 30px;
      background: transparent;
    }
    .workspace > .panel-title {
      min-height: 48px;
      margin-bottom: 14px;
      padding: 0 0 16px;
      border-bottom: 1px solid rgba(70, 199, 255, 0.16);
    }
    .workspace > .panel-title h2 {
      color: var(--ink);
      font-size: 26px;
      line-height: 32px;
      letter-spacing: 0;
    }
    .tabs {
      display: flex;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 4;
      gap: 4px;
      padding: 6px;
      margin-bottom: 18px;
      border: 1px solid rgba(70, 199, 255, 0.16);
      border-radius: 12px;
      background: rgba(5, 11, 19, 0.88);
      backdrop-filter: blur(16px);
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
      overflow-x: auto;
      scrollbar-width: thin;
      scrollbar-color: rgba(70, 199, 255, 0.36) transparent;
    }
    .tab-button {
      flex: 0 0 auto;
      justify-content: center;
      min-width: 124px;
      min-height: 42px;
      padding: 0 14px;
      border-radius: 9px;
      color: var(--muted);
      background: transparent;
      border-color: transparent;
      white-space: nowrap;
    }
    .tab-button.active {
      color: #eefaff;
      background: linear-gradient(180deg, rgba(34, 73, 108, 0.82), rgba(13, 31, 50, 0.92));
      border-color: rgba(70, 199, 255, 0.26);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }
    .tab-panel {
      animation: panelIn 180ms ease-out;
    }
    @keyframes panelIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @media (prefers-reduced-motion: reduce) {
      .tab-panel { animation: none; }
    }
    .metric-grid {
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .metric {
      min-height: 94px;
      padding: 14px;
      border: 1px solid rgba(70, 199, 255, 0.16);
      border-radius: 12px;
      background:
        linear-gradient(180deg, rgba(11, 26, 42, 0.96), rgba(7, 16, 27, 0.96));
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
    }
    .metric span {
      color: #8fa8bd;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .metric strong {
      color: #f6fbff;
      font-size: 24px;
      line-height: 30px;
    }
    .metric.metric-good {
      border-color: rgba(56, 217, 150, 0.42);
      background: linear-gradient(180deg, rgba(16, 64, 52, 0.52), rgba(7, 17, 28, 0.96));
    }
    .metric.metric-good span { color: #9af2c7; }
    .metric.metric-good strong { color: var(--good); }
    .metric.metric-bad {
      border-color: rgba(255, 107, 135, 0.48);
      background: linear-gradient(180deg, rgba(74, 23, 38, 0.58), rgba(7, 17, 28, 0.96));
    }
    .metric.metric-bad span { color: #ffb4c2; }
    .metric.metric-bad strong { color: var(--bad); }
    .metric.metric-warn {
      border-color: rgba(247, 201, 72, 0.48);
      background: linear-gradient(180deg, rgba(75, 61, 25, 0.48), rgba(7, 17, 28, 0.96));
    }
    .metric.metric-warn span { color: #ffe28a; }
    .metric.metric-warn strong { color: var(--warn); }
    .metric.metric-info {
      border-color: rgba(70, 199, 255, 0.42);
      background: linear-gradient(180deg, rgba(19, 57, 84, 0.5), rgba(7, 17, 28, 0.96));
    }
    .metric.metric-info span { color: #bfeeff; }
    .metric.metric-info strong { color: var(--accent); }
    .metric.metric-muted { opacity: 0.82; }
    .split,
    .order-audit-grid {
      grid-template-columns: minmax(0, 1.42fr) minmax(300px, 0.58fr);
      gap: 16px;
    }
    .panel-title {
      background: transparent;
      border-color: rgba(70, 199, 255, 0.14);
    }
    .panel-title h2 {
      color: #dcefff;
      font-size: 14px;
      line-height: 18px;
    }
    .findings,
    .table-wrap,
    .output,
    .mini-panel {
      border-color: rgba(70, 199, 255, 0.16);
      border-radius: 12px;
      background: rgba(7, 17, 28, 0.92);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
    }
    .finding {
      grid-template-columns: minmax(150px, 0.32fr) minmax(0, 1fr);
      gap: 10px 14px;
      border-color: rgba(70, 199, 255, 0.12);
      background: rgba(7, 17, 28, 0.92);
    }
    .finding strong,
    .mini-panel strong {
      color: #d9efff;
      font-size: 12px;
      line-height: 17px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .finding p,
    .mini-panel p,
    .mini-panel li {
      color: #a9bdd0;
      font-size: 13px;
      line-height: 1.5;
    }
    .mini-panel {
      padding: 12px;
    }
    .mini-panel ul {
      margin: 6px 0 0;
      padding-left: 18px;
    }
    .order-verdict {
      min-height: 134px;
      margin-bottom: 16px;
      padding: 18px;
      border: 1px solid rgba(70, 199, 255, 0.22);
      border-radius: 14px;
      background:
        linear-gradient(135deg, rgba(34, 119, 180, 0.24), rgba(7, 17, 28, 0.96) 54%),
        #07111c;
      box-shadow: 0 20px 70px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }
    .order-verdict h3 {
      font-size: 22px;
      line-height: 28px;
    }
    .order-verdict p {
      color: #a9bdd0;
      max-width: 82ch;
    }
    .verdict-score {
      min-width: 128px;
      border-radius: 12px;
      border-color: rgba(70, 199, 255, 0.28);
      background: rgba(3, 7, 12, 0.72);
    }
    .verdict-score strong {
      color: var(--accent);
      font-size: 34px;
      line-height: 38px;
    }
    .pill,
    .badge {
      border: 1px solid rgba(70, 199, 255, 0.18);
      border-radius: 999px;
      background: rgba(70, 199, 255, 0.08);
      color: #bfeeff;
      letter-spacing: 0.03em;
    }
    .verdict-fail { border-color: rgba(255, 107, 135, 0.42); }
    .verdict-caution { border-color: rgba(247, 201, 72, 0.42); }
    .verdict-watch { border-color: rgba(99, 168, 255, 0.42); }
    .verdict-pass { border-color: rgba(56, 217, 150, 0.42); }
    th {
      position: sticky;
      top: 0;
      z-index: 1;
      color: #8fa8bd;
      background: #0b1623;
      border-color: rgba(70, 199, 255, 0.12);
    }
    td {
      color: #d8e8f4;
      border-color: rgba(70, 199, 255, 0.1);
    }
    tbody tr:hover { background: rgba(70, 199, 255, 0.055); }
    .output {
      min-height: 560px;
      color: #cfe7f8;
      background: #050b13;
    }
    #intelligenceBrief {
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }
    #intelligenceBrief .mini-panel:first-child {
      grid-column: 1 / -1;
      background: linear-gradient(135deg, rgba(70, 199, 255, 0.14), rgba(7, 17, 28, 0.96));
    }
    .pattern-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }
    .pattern-card {
      min-height: 220px;
      display: grid;
      gap: 12px;
      align-content: start;
    }
    .condition-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }    @media (max-width: 1120px) {
      :root { --sidebar: 310px; }
      .split,
      .order-audit-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 900px) {
      header { padding: 12px 16px; }
      main > section:first-child { box-shadow: none; }
      textarea { width: calc(100% - 32px); margin: 12px 16px; min-height: 300px; }
      .workspace { padding: 18px 16px 24px; }
      .tabs { position: static; }
      .order-verdict { grid-template-columns: 1fr; }
      .verdict-score { min-width: 0; }
      header h1::after { display: none; }
    }
    @media (max-width: 560px) {
      .actions { grid-template-columns: 1fr; }
      .metric-grid { grid-template-columns: 1fr; }
      .finding { grid-template-columns: 1fr; }
      .workspace > .panel-title h2 { font-size: 22px; line-height: 28px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Agent Risk Console</h1>
    <span id="health" class="badge">checking</span>
  </header>
  <main>
    <section>
      <div class="rail-brand">
        <h1>BitGuard Sentinel</h1>
        <p>Audit order logs, whale pings, and AI briefs without uploading API keys.</p>
      </div>
      <div class="panel-title">
        <h2>Evidence Bundle</h2>
        <span class="status">POST /api/audit + /api/intelligence</span>
      </div>
      <textarea id="bundle"></textarea>
      <div class="token-panel">
        <label for="apiToken">API token</label>
        <div class="token-row">
          <input id="apiToken" type="password" placeholder="Bearer token for hosted API">
          <button onclick="saveApiToken()">Save</button>
        </div>
      </div>
      <div class="actions">
        <button class="primary" onclick="auditBundle()">Run Audit</button>
        <button onclick="loadSample()">Load Demo</button>
        <button onclick="redactBundle()">Redact</button>
        <label class="file-label" for="fileInput">Open JSON</label>
        <input id="fileInput" type="file" accept="application/json,.json" onchange="loadFile(event)">
      </div>
    </section>
    <section class="workspace">
      <div class="panel-title">
        <h2>Risk Command Center</h2>
        <span id="state" class="status">idle</span>
      </div>
      <div class="tabs" role="tablist">
        <button id="tab-overview" class="tab-button active" onclick="showTab('overview')">Overview</button>
        <button id="tab-patterns" class="tab-button" onclick="showTab('patterns')">Patterns</button>
        <button id="tab-orders" class="tab-button" onclick="showTab('orders')">Trade Review</button>
        <button id="tab-perception" class="tab-button" onclick="showTab('perception')">Whale Pings</button>
        <button id="tab-exposure" class="tab-button" onclick="showTab('exposure')">Exposure</button>
        <button id="tab-connect" class="tab-button" onclick="showTab('connect')">Connect</button>
        <button id="tab-raw" class="tab-button" onclick="showTab('raw')">Raw Report</button>
      </div>
      <div id="panel-overview" class="tab-panel active">
        <div id="metrics" class="metric-grid"></div>
        <div class="split">
          <div>
            <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
              <h2>Findings</h2>
              <span id="mode" class="status">none</span>
            </div>
            <div id="findings" class="findings"></div>
          </div>
          <div id="healthNotes" class="stack"></div>
        </div>
      </div>
      <div id="panel-patterns" class="tab-panel">
        <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
          <h2>Pattern Library</h2>
          <span id="patternCount" class="status">0 patterns</span>
        </div>
        <div id="patternStats" class="metric-grid"></div>
        <div id="patternNarrative" class="mini-panel" style="margin-bottom:14px;"></div>
        <div id="patternGrid" class="pattern-grid"></div>
      </div>
      <div id="panel-orders" class="tab-panel">
        <div id="orderVerdict" class="order-verdict"></div>
        <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;margin-top:14px;">
          <h2>Market Replay</h2>
          <span id="marketReplayCount" class="status">0 trades</span>
        </div>
        <div id="marketReplay" class="findings"></div>
        <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;margin-top:14px;">
          <h2>AI Replay Coach</h2>
          <button onclick="generateIntelligence()">Generate Brief</button>
        </div>
        <div id="intelligenceBrief" class="stack"></div>
        <div class="order-audit-grid" style="margin-top:14px;">
          <div>
            <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
              <h2>Audit Evidence</h2>
              <span id="evidenceCount" class="status">0 signals</span>
            </div>
            <div id="orderEvidence" class="findings"></div>
          </div>
          <div>
            <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
              <h2>Recommendations</h2>
              <span id="recommendationCount" class="status">0 actions</span>
            </div>
            <div id="orderRecommendations" class="stack"></div>
          </div>
        </div>
        <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;margin-top:14px;">
          <h2>Trade Pairing Detail</h2>
          <span id="tradeCount" class="status">0 trades</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Direction</th>
                <th>Entry</th>
                <th>Exit</th>
                <th class="num">Qty</th>
                <th class="num">Fees</th>
                <th class="num">PnL</th>
                <th class="num">Return</th>
                <th>Outcome</th>
              </tr>
            </thead>
            <tbody id="tradesBody"></tbody>
          </table>
        </div>
      </div>
      <div id="panel-perception" class="tab-panel">
        <div id="perceptionVerdict" class="order-verdict"></div>
        <div class="order-audit-grid">
          <div>
            <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
              <h2>Skill Hub Signals</h2>
              <span id="signalCount" class="status">0 signals</span>
            </div>
            <div id="perceptionSignals" class="findings"></div>
          </div>
          <div>
            <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
              <h2>Copy/Whale Pings</h2>
              <span id="pingCount" class="status">0 pings</span>
            </div>
            <div id="whalePings" class="stack"></div>
          </div>
        </div>
        <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;margin-top:14px;">
          <h2>Perception Actions</h2>
          <span id="perceptionActionCount" class="status">0 actions</span>
        </div>
        <div id="perceptionRecommendations" class="stack"></div>

      </div>
      <div id="panel-exposure" class="tab-panel">
        <div class="split">
          <div>
            <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
              <h2>Position Concentration</h2>
              <span id="positionCount" class="status">0 positions</span>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th class="num">Notional</th>
                    <th class="num">Share</th>
                  </tr>
                </thead>
                <tbody id="exposureBody"></tbody>
              </table>
            </div>
          </div>
          <div>
            <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
              <h2>Funding</h2>
              <span id="fundingCount" class="status">0 events</span>
            </div>
            <div id="fundingList" class="stack"></div>
          </div>
        </div>
      </div>
      <div id="panel-connect" class="tab-panel">
        <div class="panel-title" style="padding-left:0;padding-right:0;border-bottom:0;">
          <h2>Connect Agent</h2>
          <span class="status">CLI / HTTP / local collector</span>
        </div>
        <div class="pattern-grid">
          <div class="mini-panel">
            <strong>CLI Mode</strong>
            <p>Use when an agent writes an evidence bundle to disk and wants a local verdict artifact.</p>
            <pre class="code-snippet">bitguard audit exports/agent-log-bundle.json --out outputs/audit_report.json
bitguard intelligence exports/agent-log-bundle.json --out outputs/intelligence_report.json</pre>
          </div>
          <div class="mini-panel">
            <strong>HTTP API Mode</strong>
            <p>Use for deployed Railway demos or agents that can POST JSON after each run.</p>
            <pre class="code-snippet">curl -X POST $BITGUARD_URL/api/audit \
  -H "Authorization: Bearer $BITGUARD_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @exports/agent-log-bundle.json</pre>
          </div>
          <div class="mini-panel">
            <strong>Local Bitget Collector</strong>
            <p>Use when the trader wants private Bitget reads to happen locally before sending summaries for audit.</p>
            <pre class="code-snippet">bitguard collect-bitget --agent-id my-agent --out exports/bitget-log-bundle.json
bitguard audit exports/bitget-log-bundle.json --out outputs/audit_report.json</pre>
          </div>
          <div class="mini-panel">
            <strong>Minimum Bundle</strong>
            <p>agent_id, run_id, fills[].symbol, fills[].side, fills[].price, fills[].quantity, fills[].timestamp.</p>
            <pre class="code-snippet">{
  "agent_id": "my-agent",
  "run_id": "run-001",
  "fills": [{"symbol":"BTCUSDT","side":"buy","price":65000,"quantity":0.01,"timestamp":"2026-06-24T10:00:00Z"}]
}</pre>
          </div>
        </div>
      </div>      <div id="panel-raw" class="tab-panel">
        <div class="raw-toolbar">
          <span id="rawState" class="status">no report loaded</span>
          <button onclick="loadUsage()">Usage Records</button>
        </div>
        <pre id="output" class="output"></pre>
      </div>
    </section>
  </main>
  <script>
    const sampleBundle = {
      source: "demo-agent-log-schema",
      demo_only: true,
      agent_id: "sentinel-demo-agent",
      run_id: "demo-run-001",
      exported_at: "2026-06-23T09:00:00Z",
      orders: [
        { order_id: "ord-1001", symbol: "BTCUSDT", side: "buy", order_type: "market", price: 65000, quantity: 0.03, status: "filled", created_at: "2026-06-22T09:00:00Z" },
        { order_id: "ord-1002", symbol: "BTCUSDT", side: "sell", order_type: "market", price: 65750, quantity: 0.03, status: "filled", created_at: "2026-06-22T15:00:00Z" },
        { order_id: "ord-1003", symbol: "ETHUSDT", side: "buy", order_type: "market", price: 3520, quantity: 0.8, status: "filled", created_at: "2026-06-22T16:00:00Z" },
        { order_id: "ord-1004", symbol: "ETHUSDT", side: "sell", order_type: "market", price: 3460, quantity: 0.8, status: "filled", created_at: "2026-06-23T02:00:00Z" }
      ],
      fills: [
        { fill_id: "fill-1", order_id: "ord-1001", symbol: "BTCUSDT", side: "buy", price: 65000, quantity: 0.03, fee_usdt: 1.17, timestamp: "2026-06-22T09:00:05Z" },
        { fill_id: "fill-2", order_id: "ord-1002", symbol: "BTCUSDT", side: "sell", price: 65750, quantity: 0.03, fee_usdt: 1.18, timestamp: "2026-06-22T15:00:05Z" },
        { fill_id: "fill-3", order_id: "ord-1003", symbol: "ETHUSDT", side: "buy", price: 3520, quantity: 0.8, fee_usdt: 1.69, timestamp: "2026-06-22T16:00:05Z" },
        { fill_id: "fill-4", order_id: "ord-1004", symbol: "ETHUSDT", side: "sell", price: 3460, quantity: 0.8, fee_usdt: 1.66, timestamp: "2026-06-23T02:00:05Z" }
      ],
      positions: [
        { position_id: "pos-1", symbol: "BTCUSDT", side: "long", notional_usdt: 4200, leverage: 4, unrealized_pnl: -35, margin: 1050, timestamp: "2026-06-23T09:00:00Z" },
        { position_id: "pos-2", symbol: "ETHUSDT", side: "long", notional_usdt: 1300, leverage: 2, unrealized_pnl: 12, margin: 650, timestamp: "2026-06-23T09:00:00Z" }
      ],
      funding_payments: [
        { symbol: "BTCUSDT", amount_usdt: -4.2, rate: 0.00031, timestamp: "2026-06-22T16:00:00Z" },
        { symbol: "ETHUSDT", amount_usdt: -1.1, rate: 0.00019, timestamp: "2026-06-23T00:00:00Z" }
      ],
      market_context: {
        source: "demo-supplied-candles",
        fetch_status: "supplied",
        product_type: "USDT-FUTURES",
        market_type: "futures",
        candles: {
          BTCUSDT: [
            { timestamp: "2026-06-22T09:00:00Z", open: 64900, high: 65200, low: 64800, close: 65000, volume: 1200 },
            { timestamp: "2026-06-22T12:00:00Z", open: 65000, high: 66000, low: 64950, close: 65600, volume: 1550 },
            { timestamp: "2026-06-22T15:00:00Z", open: 65600, high: 65800, low: 65400, close: 65720, volume: 980 }
          ],
          ETHUSDT: [
            { timestamp: "2026-06-22T16:00:00Z", open: 3515, high: 3540, low: 3480, close: 3520, volume: 8700 },
            { timestamp: "2026-06-22T20:00:00Z", open: 3520, high: 3530, low: 3440, close: 3465, volume: 9200 },
            { timestamp: "2026-06-23T02:00:00Z", open: 3465, high: 3480, low: 3430, close: 3460, volume: 6100 }
          ]
        }
      },
      account_snapshots: [
        { timestamp: "2026-06-23T09:00:00Z", equity_usdt: 7200, available_usdt: 2680 }
      ],
      agent_decisions: [
        { decision_id: "dec-1", symbol: "BTCUSDT", action: "buy", confidence: 0.76, stop_loss: 63700, take_profit: 67600, rationale: "Trend continuation", timestamp: "2026-06-22T08:59:00Z" },
        { decision_id: "dec-2", symbol: "ETHUSDT", action: "buy", confidence: 0.69, stop_loss: 0, take_profit: 3670, rationale: "Mean reversion", timestamp: "2026-06-22T15:59:00Z" }
      ],
      skill_hub: {
        macro_analyst: { stance: "mixed headwind", summary: "Macro backdrop is mixed: risk assets have support, but dollar strength and event risk keep BTC from a clean risk-on setup." },
        market_intel: { stance: "whale accumulation bullish", summary: "Top-trader and market-structure proxies show BTC accumulation, but the signal needs confirmation from derivatives positioning." },
        news_briefing: { stance: "event risk", summary: "Fresh market headlines point to catalyst risk around upcoming policy and liquidity events." },
        sentiment_analyst: { stance: "crowded longs funding elevated", summary: "Long exposure is crowded and funding is elevated, increasing long-squeeze risk if price stalls." },
        technical_analysis: { stance: "bullish trend near resistance", summary: "Trend remains constructive, but price is close to resistance and needs breakout confirmation." }
      },
      copy_trading_pings: [
        { source: "copy_trading", symbol: "BTCUSDT", direction: "long", notional_usdt: 4200, followers: 1860, leader_drawdown_pct: 12.4, summary: "A highly followed copy-trading leader is net long BTC, but the follower crowd is large and the leader has meaningful drawdown." }
      ]
    };
    let currentReport = null;
    const money = value => `${Number(value || 0).toFixed(2)} USDT`;
    const pct = value => `${Number(value || 0).toFixed(2)}%`;
    function setState(text) { document.getElementById("state").textContent = text; }
    function pretty(data) { document.getElementById("output").textContent = JSON.stringify(data, null, 2); }
    function showTab(name) {
      for (const key of ["overview", "patterns", "orders", "perception", "exposure", "connect", "raw"]) {
        document.getElementById(`tab-${key}`).classList.toggle("active", key === name);
        document.getElementById(`panel-${key}`).classList.toggle("active", key === name);
      }
    }
    function loadSample() { document.getElementById("bundle").value = JSON.stringify(sampleBundle, null, 2); }
    function metricClass(state) {
      return state ? ` metric-${state}` : "";
    }
    function riskMetricState(value) {
      const number = Number(value);
      if (!Number.isFinite(number)) return "muted";
      if (number >= 65) return "bad";
      if (number >= 40) return "warn";
      return "good";
    }
    function signedMetricState(value) {
      const number = Number(value);
      if (!Number.isFinite(number) || number === 0) return "muted";
      return number > 0 ? "good" : "bad";
    }
    function thresholdMetricState(value, warnAt, badAt) {
      const number = Number(value);
      if (!Number.isFinite(number) || number === 0) return "good";
      if (number >= badAt) return "bad";
      if (number >= warnAt) return "warn";
      return "good";
    }
    function statusMetricState(value) {
      const text = String(value || "").toLowerCase();
      if (["pass", "opportunity", "available", "healthy", "aligned_win", "verified"].includes(text)) return "good";
      if (["watch", "caution", "partial", "review", "mixed", "observed"].includes(text)) return "warn";
      if (["fail", "avoid", "error", "fetch_failed", "missing_candles", "no_completed_trades", "not_supplied", "risk"].includes(text)) return "bad";
      return text ? "info" : "muted";
    }
    function cards(report) {
      const summary = report.summary || {};
      const pnl = report.metrics?.pnl || {};
      const exposure = report.metrics?.exposure || {};
      const items = [
        { label: "Risk", value: summary.risk_score ?? "-", state: riskMetricState(summary.risk_score) },
        { label: "Market", value: summary.product_type || summary.market_type || "-", state: "info" },
        { label: "Replay", value: summary.market_context_status || "-", state: statusMetricState(summary.market_context_status) },
        { label: "Patterns", value: summary.patterns ?? "-", state: Number(summary.verified_patterns || 0) > 0 ? "good" : Number(summary.patterns || 0) > 0 ? "warn" : "muted" },
        { label: "Perception", value: summary.perception_verdict ?? "-", state: statusMetricState(summary.perception_verdict) },
        { label: "PnL", value: money(pnl.total_realized_pnl_usdt), state: signedMetricState(pnl.total_realized_pnl_usdt) },
        { label: "Drawdown", value: pct(pnl.max_drawdown_pct), state: thresholdMetricState(pnl.max_drawdown_pct, 1, 5) },
        { label: "Leverage", value: `${Number(exposure.max_leverage || 0).toFixed(1)}x`, state: thresholdMetricState(exposure.max_leverage, 2, 3) },
        { label: "Concentration", value: pct(exposure.largest_position_concentration_pct), state: thresholdMetricState(exposure.largest_position_concentration_pct, 50, 65) },
        { label: "Funding", value: money(pnl.funding_pnl_usdt), state: signedMetricState(pnl.funding_pnl_usdt) },
        { label: "Trades", value: summary.completed_trades ?? 0, state: Number(summary.completed_trades || 0) > 0 ? "good" : "muted" }
      ];
      document.getElementById("metrics").innerHTML = items.map(item => `<div class="metric${metricClass(item.state)}"><span>${item.label}</span><strong>${item.value}</strong></div>`).join("");
    }
    function renderFindings(report) {
      const rows = report.findings || [];
      document.getElementById("findings").innerHTML = rows.map(item => `<div class="finding"><strong>${item.severity.toUpperCase()} / ${item.code}</strong><p>${item.message}</p></div>`).join("") || `<div class="finding"><strong>OK</strong><p>No findings.</p></div>`;
    }
    function renderHealthNotes(report) {
      const metrics = report.metrics || {};
      const behavior = metrics.behavior || {};
      const exposure = metrics.exposure || {};
      const pnl = metrics.pnl || {};
      const replay = report.market_replay || {};
      const replaySource = replay.source || "none";
      const replayStatus = replay.fetch_status || report.summary?.market_context_status || "not loaded";
      const replaySymbols = (replay.symbols || []).join(", ") || "none";
      const notes = [
        ["Run", `${report.agent_id || "unknown"} / ${report.run_id || "unknown"}`],
        ["Behavior", `${behavior.fill_count || 0} fills across ${behavior.active_trading_days || 0} active days`],
        ["Exposure", `${money(exposure.total_notional_usdt)} open notional at ${Number(exposure.weighted_leverage || 0).toFixed(1)}x weighted leverage`],
        ["Costs", `${money(pnl.fees_usdt)} fees and ${money(pnl.funding_pnl_usdt)} funding`],
        ["Market", `${(report.summary?.product_type || "UNKNOWN")} / replay ${(report.summary?.market_context_status || "not loaded")}`],
        ["Replay Source", `${replaySource} / ${replayStatus} / ${replaySymbols}`]
      ];
      document.getElementById("healthNotes").innerHTML = notes.map(([title, body]) => `<div class="mini-panel"><strong>${title}</strong><p>${body}</p></div>`).join("");
    }
    function severityClass(severity) {
      const value = String(severity || "info").toLowerCase();
      if (value === "high" || value === "fail") return "negative";
      if (value === "medium" || value === "caution" || value === "watch") return "";
      return "positive";
    }
    function renderMarketReplay(report) {
      const replay = report.market_replay || {};
      const rows = replay.trade_replays || [];
      const count = rows.filter(item => item.status === "available").length;
      document.getElementById("marketReplayCount").textContent = `${count}/${rows.length || 0} trades`;
      if (!rows.length) {
        const recs = replay.recommendations || [];
        document.getElementById("marketReplay").innerHTML = `<div class="finding"><strong>${String(replay.status || "WAITING").toUpperCase()}</strong><p>${replay.summary || "No chart replay has been generated yet."}</p></div>` + recs.map(item => `<div class="finding"><strong>NEXT CHECK</strong><p>${item}</p></div>`).join("");
        return;
      }
      document.getElementById("marketReplay").innerHTML = rows.map(item => {
        const cls = item.status === "available" && !String(item.classification || "").includes("loss") ? "positive" : severityClass(item.status === "available" ? "medium" : "high");
        const label = `${item.symbol || "UNKNOWN"} / ${String(item.product_type || replay.product_type || "UNKNOWN").toUpperCase()} / ${String(item.classification || item.status || "not scored").replaceAll("_", " ").toUpperCase()}`;
        if (item.status !== "available") {
          return `<div class="finding"><strong class="${cls}">${label}</strong><p>${item.summary || "No matching candles for this trade window."}</p></div>`;
        }
        return `<div class="finding"><strong class="${cls}">${label}</strong><p>${item.summary || ""}</p><p style="margin-top:6px;">Entry: ${item.entry_quality || "n/a"} / Exit: ${item.exit_quality || "n/a"} / Candles: ${item.candles || 0}</p></div>`;
      }).join("");
    }
    function renderPatterns(report) {
      const library = report.pattern_library || {};
      const summary = library.summary || {};
      const rows = library.patterns || [];
      document.getElementById("patternCount").textContent = `${rows.length} patterns`;
      const stats = [
        { label: "Total", value: summary.total_patterns ?? 0, state: Number(summary.total_patterns || 0) > 0 ? "warn" : "muted" },
        { label: "Verified", value: summary.verified_patterns ?? 0, state: Number(summary.verified_patterns || 0) > 0 ? "good" : "muted" },
        { label: "Observed", value: summary.observed_patterns ?? 0, state: Number(summary.observed_patterns || 0) > 0 ? "warn" : "muted" },
        { label: "Risk", value: summary.risk_patterns ?? 0, state: Number(summary.risk_patterns || 0) > 0 ? "bad" : "muted" },
        { label: "Avg Win", value: pct(summary.avg_win_rate_pct), state: thresholdMetricState(100 - Number(summary.avg_win_rate_pct || 0), 35, 50) }
      ];
      document.getElementById("patternStats").innerHTML = stats.map(item => `<div class="metric${metricClass(item.state)}"><span>${item.label}</span><strong>${item.value}</strong></div>`).join("");
      document.getElementById("patternNarrative").innerHTML = `<strong>Agent-readable market intelligence</strong><p>${library.narrative || "Upload completed logs to turn replay evidence into reusable agent patterns."}</p>`;
      document.getElementById("patternGrid").innerHTML = rows.map(item => {
        const state = statusMetricState(item.status);
        const titleClass = state === "bad" ? "negative" : state === "good" ? "positive" : "";
        const conditions = (item.conditions || []).map(value => `<span class="pill">${value}</span>`).join("");
        const symbols = (item.symbols || []).map(value => `<span class="pill">${value}</span>`).join("");
        return `<div class="mini-panel pattern-card">
          <div><strong class="${titleClass}">${String(item.status || "observed").toUpperCase()} / ${item.title || "Pattern"}</strong><p>${item.description || "No description supplied."}</p></div>
          <div class="condition-row">${conditions || "<span class='pill'>no conditions</span>"}</div>
          <div class="condition-row">${symbols || "<span class='pill'>UNKNOWN</span>"}</div>
          <p>Win rate ${pct(item.win_rate_pct)} / sample ${item.sample_size || 0} / avg PnL <span class="${Number(item.avg_pnl_usdt || 0) >= 0 ? "positive" : "negative"}">${money(item.avg_pnl_usdt)}</span></p>
          <p>${item.action || "Retest this pattern with more completed runs."}</p>
        </div>`;
      }).join("") || `<div class="mini-panel"><strong>No patterns yet</strong><p>Run an audit with completed trades and replay candles to build the pattern library.</p></div>`;
    }
    function renderOrderAudit(report) {
      const audit = report.order_audit || {};
      const basis = audit.basis || {};
      const verdict = audit.verdict || "pending";
      const label = audit.label || "No trade review loaded";
      const score = audit.score ?? "-";
      const confidence = audit.confidence || "unknown";
      const summary = audit.summary || "Run an audit to review completed order logs, replay market context, and generate agent feedback.";
      const verdictNode = document.getElementById("orderVerdict");
      verdictNode.className = `order-verdict verdict-${verdict}`;
      verdictNode.innerHTML = `<div>
        <span class="pill">${String(verdict).toUpperCase()} / ${String(confidence).toUpperCase()} CONFIDENCE</span>
        <h3>${label}</h3>
        <p>${summary}</p>
        <p style="margin-top:8px;">Basis: ${basis.orders_analyzed || 0} orders, ${basis.fills_analyzed || 0} fills, ${basis.completed_trades || 0} completed trades / ${basis.pairing_method || "not available"}</p>
      </div>
      <div class="verdict-score"><strong>${score}</strong><span>review score</span></div>`;

      const evidence = audit.evidence || [];
      document.getElementById("evidenceCount").textContent = `${evidence.length} signals`;
      document.getElementById("orderEvidence").innerHTML = evidence.map(item => {
        const cls = severityClass(item.severity);
        return `<div class="finding"><strong class="${cls}">${String(item.severity || "info").toUpperCase()} / ${item.signal || "Signal"}</strong><p>${item.message || ""}</p></div>`;
      }).join("") || `<div class="finding"><strong>WAITING</strong><p>No order audit evidence yet.</p></div>`;

      const recommendations = audit.recommendations || [];
      document.getElementById("recommendationCount").textContent = `${recommendations.length} actions`;
      document.getElementById("orderRecommendations").innerHTML = recommendations.map((item, index) => `<div class="mini-panel"><strong>Action ${index + 1}</strong><p>${item}</p></div>`).join("") || `<div class="mini-panel"><strong>No actions</strong><p>No recommendations yet.</p></div>`;
    }
    function renderPerception(report) {
      const layer = report.perception_layer || {};
      const basis = layer.basis || {};
      const verdict = layer.verdict || "pending";
      const label = layer.label || "No perception layer loaded";
      const score = layer.score ?? "-";
      const confidence = layer.confidence || "unknown";
      const summary = layer.summary || "Run an audit with Skill Hub snapshots or copy-trading pings to score market context.";
      const node = document.getElementById("perceptionVerdict");
      node.className = `order-verdict verdict-${verdict === "avoid" ? "fail" : verdict}`;
      node.innerHTML = `<div>
        <span class="pill">${String(verdict).toUpperCase()} / ${String(confidence).toUpperCase()} CONFIDENCE</span>
        <h3>${label}</h3>
        <p>${summary}</p>
        <p style="margin-top:8px;">Basis: ${basis.skill_hub_signals || 0} Skill Hub signals, ${basis.whale_pings || 0} pings / ${basis.method || "not available"}</p>
      </div>
      <div class="verdict-score"><strong>${score}</strong><span>ping score</span></div>`;

      const signals = layer.signals || [];
      document.getElementById("signalCount").textContent = `${signals.length} signals`;
      document.getElementById("perceptionSignals").innerHTML = signals.map(item => `<div class="finding"><strong>${String(item.skill || "skill").toUpperCase()} / ${item.stance || "observed"}</strong><p>${item.summary || ""}</p></div>`).join("") || `<div class="finding"><strong>WAITING</strong><p>No Skill Hub snapshots supplied yet.</p></div>`;

      const pings = layer.whale_pings || [];
      document.getElementById("pingCount").textContent = `${pings.length} pings`;
      document.getElementById("whalePings").innerHTML = pings.map(item => `<div class="mini-panel"><strong>${item.symbol || "UNKNOWN"} / ${String(item.direction || "unknown").toUpperCase()} / ${String(item.verdict || "watch").toUpperCase()}</strong><p>${money(item.notional_usdt)} copied notional / ${item.followers || 0} followers / ${pct(item.leader_drawdown_pct)} leader drawdown</p><p>${item.summary || ""}</p></div>`).join("") || `<div class="mini-panel"><strong>No pings</strong><p>No copy-trading or whale observations supplied yet.</p></div>`;

      const recommendations = layer.recommendations || [];
      document.getElementById("perceptionActionCount").textContent = `${recommendations.length} actions`;
      document.getElementById("perceptionRecommendations").innerHTML = recommendations.map((item, index) => `<div class="mini-panel"><strong>Action ${index + 1}</strong><p>${item}</p></div>`).join("") || `<div class="mini-panel"><strong>No actions</strong><p>No perception actions yet.</p></div>`;
    }
    function renderIntelligenceBrief(result) {
      const node = document.getElementById("intelligenceBrief");
      if (!result || !result.brief) {
        node.innerHTML = `<div class="mini-panel"><strong>Ready</strong><p>Generate a post-trade replay brief from the candle audit, TrueNorth context, and OpenRouter synthesis.</p></div>`;
        return;
      }
      const brief = result.brief || {};
      const analysis = brief.analysis || {};
      const truenorth = result.truenorth || {};
      const array = value => Array.isArray(value) ? value : (value ? [value] : []);
      const list = value => array(value).map(item => `<li>${item}</li>`).join("");
      node.innerHTML = `<div class="mini-panel"><strong>${analysis.headline || "AI replay brief"}</strong><p>${analysis.thesis || "No thesis returned."}</p></div>
        <div class="mini-panel"><strong>Replay Coach</strong><ul>${list(analysis.replay_notes) || "<li>No replay notes supplied.</li>"}</ul></div>
        <div class="mini-panel"><strong>What Could Improve</strong><ul>${list(analysis.what_could_be_better) || "<li>No improvement loop supplied.</li>"}</ul></div>
        <div class="mini-panel"><strong>Execution Posture</strong><p>${analysis.execution_posture || "watch"} / ${brief.provider || "deterministic"} / ${brief.status || "unknown"}</p></div>
        <div class="mini-panel"><strong>TrueNorth</strong><p>${truenorth.status || "unknown"}${truenorth.summary ? ` / ${truenorth.summary}` : ""}</p></div>
        <div class="mini-panel"><strong>Contradictions</strong><ul>${list(analysis.contradictions) || "<li>None supplied.</li>"}</ul></div>
        <div class="mini-panel"><strong>Invalidation Triggers</strong><ul>${list(analysis.invalidation_triggers) || "<li>None supplied.</li>"}</ul></div>
        <div class="mini-panel"><strong>Next Checks</strong><ul>${list(analysis.next_checks) || "<li>None supplied.</li>"}</ul></div>`;
    }

    async function generateIntelligence() {
      const payload = JSON.parse(document.getElementById("bundle").value);
      const data = await post("/api/intelligence", payload);
      renderReport(data.audit);
      renderIntelligenceBrief(data);
      pretty(data);
      showTab("orders");
    }
    function renderTrades(report) {
      const trades = report.trades || [];
      document.getElementById("tradeCount").textContent = `${trades.length} trades`;
      document.getElementById("tradesBody").innerHTML = trades.map(trade => {
        const pnlClass = trade.realized_pnl_usdt >= 0 ? "positive" : "negative";
        return `<tr>
          <td>${trade.symbol}</td>
          <td><span class="pill">${trade.direction}</span></td>
          <td>${trade.entry_time}<br>${money(trade.entry_price).replace(" USDT", "")}</td>
          <td>${trade.exit_time}<br>${money(trade.exit_price).replace(" USDT", "")}</td>
          <td class="num">${Number(trade.quantity || 0).toFixed(6)}</td>
          <td class="num">${money(trade.fees_usdt)}</td>
          <td class="num ${pnlClass}">${money(trade.realized_pnl_usdt)}</td>
          <td class="num ${pnlClass}">${pct(trade.return_pct)}</td>
          <td><span class="pill">${trade.outcome}</span></td>
        </tr>`;
      }).join("") || `<tr><td colspan="9">No reconstructed trades.</td></tr>`;
    }
    function renderExposure(report) {
      const exposure = report.metrics?.exposure || {};
      const rows = exposure.by_symbol || [];
      document.getElementById("positionCount").textContent = `${exposure.open_position_count || 0} positions`;
      document.getElementById("exposureBody").innerHTML = rows.map(row => `<tr><td>${row.symbol}</td><td class="num">${money(row.notional_usdt)}</td><td class="num">${pct(row.share_pct)}</td></tr>`).join("") || `<tr><td colspan="3">No open exposure.</td></tr>`;
      const funding = report.normalized_preview?.funding_payments || [];
      document.getElementById("fundingCount").textContent = `${funding.length} events`;
      document.getElementById("fundingList").innerHTML = funding.map(item => {
        const cls = item.amount_usdt >= 0 ? "positive" : "negative";
        return `<div class="mini-panel"><strong>${item.symbol} / ${item.timestamp}</strong><p><span class="${cls}">${money(item.amount_usdt)}</span> at rate ${Number(item.rate || 0).toFixed(5)}</p></div>`;
      }).join("") || `<div class="mini-panel"><strong>No funding</strong><p>No funding events in this bundle.</p></div>`;
    }
    function renderReport(report) {
      currentReport = report;
      document.getElementById("mode").textContent = report.mode || "audit";
      document.getElementById("rawState").textContent = report.mode || "audit";
      cards(report);
      renderFindings(report);
      renderHealthNotes(report);
      renderPatterns(report);
      renderOrderAudit(report);
      renderMarketReplay(report);
      renderPerception(report);
      renderIntelligenceBrief(null);
      renderTrades(report);
      renderExposure(report);
      pretty(report);
    }
    function loadApiToken() {
      const token = localStorage.getItem("bitguard_api_token") || "";
      document.getElementById("apiToken").value = token;
    }
    function saveApiToken() {
      const token = document.getElementById("apiToken").value.trim();
      if (token) localStorage.setItem("bitguard_api_token", token);
      else localStorage.removeItem("bitguard_api_token");
      setState(token ? "token saved" : "token cleared");
    }
    function authHeaders(includeJson = true) {
      const headers = includeJson ? {"content-type": "application/json"} : {};
      const token = localStorage.getItem("bitguard_api_token") || document.getElementById("apiToken")?.value.trim() || "";
      if (token) headers.Authorization = `Bearer ${token}`;
      return headers;
    }
    async function post(path, payload) {
      setState("running");
      const response = await fetch(path, { method: "POST", headers: authHeaders(true), body: JSON.stringify(payload) });
      const data = await response.json();
      setState(response.ok ? "complete" : "error");
      if (!response.ok) {
        pretty(data);
        showTab("raw");
        throw new Error(data.error?.message || "Request failed");
      }
      return data;
    }
    async function auditBundle() {
      const payload = JSON.parse(document.getElementById("bundle").value);
      const data = await post("/api/audit", payload);
      renderReport(data);
      showTab(data.pattern_library?.patterns?.length ? "patterns" : data.market_replay?.trade_replays?.length || data.order_audit ? "orders" : "perception");
    }
    async function redactBundle() {
      const payload = JSON.parse(document.getElementById("bundle").value);
      const data = await post("/api/redact", payload);
      document.getElementById("rawState").textContent = "redacted";
      pretty(data);
      showTab("raw");
    }
    async function loadUsage() {
      setState("loading");
      const response = await fetch("/api/usage?limit=20", { headers: authHeaders(false) });
      pretty(await response.json());
      document.getElementById("rawState").textContent = "usage records";
      setState("complete");
      showTab("raw");
    }
    function loadFile(event) {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => { document.getElementById("bundle").value = reader.result; };
      reader.readAsText(file);
    }
    async function boot() {
      loadApiToken();
      loadSample();
      const response = await fetch("/api/health");
      const data = await response.json();
      const health = document.getElementById("health");
      health.textContent = data.ok ? "healthy" : "offline";
      health.className = data.ok ? "badge ok" : "badge bad";
      cards({summary: {}, metrics: {pnl: {}, exposure: {}}});
      renderFindings({findings: []});
      renderHealthNotes({metrics: {behavior: {}, exposure: {}, pnl: {}}});
      renderPatterns({pattern_library: {summary: {}, patterns: []}});
      renderOrderAudit({order_audit: {}});
      renderMarketReplay({market_replay: {}});
      renderPerception({perception_layer: {}});
      renderIntelligenceBrief(null);
      renderTrades({trades: []});
      renderExposure({metrics: {exposure: {}}, normalized_preview: {funding_payments: []}});
    }
    boot();
  </script>
</body>
</html>
"""







