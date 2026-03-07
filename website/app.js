import React, { useEffect, useMemo, useRef, useState } from "https://esm.sh/react@18.3.1";
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client";
import htm from "https://esm.sh/htm@3.1.1";
import Chart from "https://esm.sh/chart.js@4.4.3/auto";
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import {
  createUserWithEmailAndPassword,
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";

const html = htm.bind(React.createElement);

const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const FIREBASE_CONFIG = window.__FIREBASE_CONFIG__ || {};
const HAS_FIREBASE_CONFIG = ["apiKey", "authDomain", "projectId", "appId"].every((key) => Boolean(FIREBASE_CONFIG[key]));

const firebaseApp = HAS_FIREBASE_CONFIG ? initializeApp(FIREBASE_CONFIG) : null;
const firebaseAuth = firebaseApp ? getAuth(firebaseApp) : null;
const googleProvider = firebaseAuth ? new GoogleAuthProvider() : null;

function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    const raw = localStorage.getItem(key);
    if (raw == null) return initialValue;
    try {
      return JSON.parse(raw);
    } catch {
      return raw;
    }
  });

  useEffect(() => {
    localStorage.setItem(key, typeof value === "string" ? value : JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}

function StatusChip({ ok, text }) {
  const style = useMemo(
    () => ({
      background: ok === null ? "var(--paper)" : ok ? "#def7eb" : "#ffe0dd",
      color: ok === null ? "var(--ink)" : "#162338",
      borderColor: ok === null ? "var(--line)" : ok ? "#9fdac3" : "#f5b3ac",
    }),
    [ok]
  );
  return html`<span className="status-chip" style=${style}>${text}</span>`;
}

function NavGlyph({ kind }) {
  const iconPaths = {
    soc: "M12 3l8 4v5c0 5.2-3.4 8.7-8 10-4.6-1.3-8-4.8-8-10V7l8-4z",
    investigator: "M11 4a7 7 0 105.3 11.6L21 20.3 19.6 22l-4.7-4.7A7 7 0 0011 4z",
    upload: "M12 3v12m0-12l-4 4m4-4l4 4M5 15v4h14v-4",
    model: "M4 17l4-4 3 3 5-6 4 3M4 6h16",
    executive: "M3 10l9-6 9 6M6 10v8m6-8v8m6-8v8M3 20h18",
    history: "M12 7v6l4 2M21 12a9 9 0 11-3-6.7",
  };
  return html`
    <span className="nav-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path d=${iconPaths[kind] || iconPaths.soc} />
      </svg>
    </span>
  `;
}

function App() {
  const [view, setView] = useState("soc");
  const [apiBase, setApiBase] = useLocalStorage("apiBase", DEFAULT_API_BASE);
  const [apiOk, setApiOk] = useState(null);
  const [history, setHistory] = useState([]);
  const [utcTime, setUtcTime] = useState(new Date().toISOString().slice(11, 19));
  const [refreshing, setRefreshing] = useState(false);
  const [authReady, setAuthReady] = useState(!HAS_FIREBASE_CONFIG);
  const [authUser, setAuthUser] = useState(null);
  const [authToken, setAuthToken] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  const [metrics, setMetrics] = useState({ total: 0, fraud: 0, rate: 0 });
  const [alerts, setAlerts] = useState([]);
  const [cases, setCases] = useState([]);
  const [severityFilter, setSeverityFilter] = useState("");
  const [detectStatus, setDetectStatus] = useState("");
  const [results, setResults] = useState([]);
  const [alertsQuery, setAlertsQuery] = useState("");
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [casesLoading, setCasesLoading] = useState(false);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [detectLoading, setDetectLoading] = useState(false);
  const [toast, setToast] = useState("");
  const [simThreshold, setSimThreshold] = useState(0.5);
  const [theme, setTheme] = useLocalStorage("theme", "dark");
  const [compactMode, setCompactMode] = useLocalStorage("compactMode", false);
  const [autoRefreshSec, setAutoRefreshSec] = useLocalStorage("autoRefreshSec", 0);
  const [reducedMotion, setReducedMotion] = useLocalStorage("reducedMotion", false);
  const [soundFx, setSoundFx] = useLocalStorage("soundFx", true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [assigneeName, setAssigneeName] = useState("analyst@riskatlas");
  const [caseStateMap, setCaseStateMap] = useLocalStorage("caseStateMap", {});
  const [caseNotesMap, setCaseNotesMap] = useLocalStorage("caseNotesMap", {});
  const [caseSlaMap, setCaseSlaMap] = useLocalStorage("caseSlaMap", {});
  const [caseNoteDrafts, setCaseNoteDrafts] = useState({});
  const [explainDrawer, setExplainDrawer] = useState(null);
  const [livePulse, setLivePulse] = useState([]);
  const [playbookLog, setPlaybookLog] = useState([]);
  const [onboardingTasks, setOnboardingTasks] = useLocalStorage("onboardingTasks", {
    signedIn: false,
    apiConfigured: false,
    firstDetectRun: false,
    firstCaseUpdated: false,
  });
  const fileInputRef = useRef(null);

  const dayChartRef = useRef(null);
  const severityChartRef = useRef(null);
  const trendChartRef = useRef(null);
  const mixChartRef = useRef(null);
  const dayChartCanvasRef = useRef(null);
  const severityChartCanvasRef = useRef(null);
  const trendChartCanvasRef = useRef(null);
  const mixChartCanvasRef = useRef(null);
  const audioCtxRef = useRef(null);

  function log(msg) {
    const entry = `${new Date().toLocaleTimeString()} - ${msg}`;
    setHistory((h) => [entry, ...h].slice(0, 30));
  }

  function notify(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 2200);
  }

  function playClickSound() {
    if (!soundFx) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      if (!audioCtxRef.current) audioCtxRef.current = new AC();
      const ctx = audioCtxRef.current;

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(740, now);
      osc.frequency.exponentialRampToValueAtTime(980, now + 0.05);
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.06, now + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.11);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.12);
    } catch {
      // no-op if audio fails
    }
  }

  function parseErrorText(value) {
    if (!value) return "Unknown error";
    if (typeof value === "string") return value;
    if (typeof value.detail === "string") return value.detail;
    return JSON.stringify(value);
  }

  async function fetchApi(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
    const doFetch = (base) => fetch(`${base}${path}`, { ...options, headers });
    const isLocalUi = ["127.0.0.1", "localhost"].includes(window.location.hostname);
    let res;

    try {
      res = await doFetch(apiBase);
    } catch (error) {
      const msg = String(error?.message || error || "");
      const networkError = error instanceof TypeError || /failed to fetch|networkerror|load failed/i.test(msg.toLowerCase());
      if (networkError && isLocalUi && apiBase !== DEFAULT_API_BASE) {
        setApiBase(DEFAULT_API_BASE);
        log(`Network error on ${apiBase}; retrying ${DEFAULT_API_BASE}`);
        res = await doFetch(DEFAULT_API_BASE);
      } else {
        throw error;
      }
    }

    if (!res.ok) {
      let errorBody = null;
      try {
        errorBody = await res.json();
      } catch {
        errorBody = { detail: await res.text() };
      }
      throw new Error(`${res.status} ${parseErrorText(errorBody)}`);
    }
    return res;
  }

  async function handleAuthAction(action) {
    if (!firebaseAuth) return;
    setAuthError("");
    setAuthBusy(true);
    try {
      await action();
    } catch (e) {
      setAuthError(e?.message || "Authentication failed");
    } finally {
      setAuthBusy(false);
    }
  }

  async function signInEmail() {
    await handleAuthAction(async () => {
      await signInWithEmailAndPassword(firebaseAuth, email.trim(), password);
    });
  }

  async function signUpEmail() {
    await handleAuthAction(async () => {
      await createUserWithEmailAndPassword(firebaseAuth, email.trim(), password);
    });
  }

  async function signInGoogle() {
    await handleAuthAction(async () => {
      await signInWithPopup(firebaseAuth, googleProvider);
    });
  }

  async function signOutNow() {
    await handleAuthAction(async () => {
      await signOut(firebaseAuth);
    });
  }

  async function checkHealth() {
    try {
      await fetchApi("/health");
      setApiOk(true);
      log("Health check passed");
    } catch (e) {
      setApiOk(false);
      log(`Health check failed: ${e.message}`);
    }
  }

  async function loadAnalytics() {
    setAnalyticsLoading(true);
    try {
      const res = await fetchApi("/analytics");
      const data = await res.json();

      const total = Number(data.total_transactions ?? 0);
      const fraud = Number(data.total_fraud ?? 0);
      const rate = Number(data.fraud_rate ?? 0);
      setMetrics({ total, fraud, rate });

      const byDay = data.fraud_by_day || {};
      const dayLabels = Object.keys(byDay);
      const dayValues = Object.values(byDay);
      const bySeverity = data.fraud_by_severity || {};
      const sevLabels = Object.keys(bySeverity);
      const sevValues = Object.values(bySeverity);
      const safeCount = Math.max(0, total - fraud);

      if (dayChartCanvasRef.current) {
        if (dayChartRef.current) dayChartRef.current.destroy();
        dayChartRef.current = new Chart(dayChartCanvasRef.current.getContext("2d"), {
          type: "bar",
          data: {
            labels: dayLabels,
            datasets: [
              {
                label: "Frauds by Day",
                data: dayValues,
                backgroundColor: "rgba(11, 59, 102, 0.75)",
                borderRadius: 6,
              },
            ],
          },
          options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
        });
      }

      if (severityChartCanvasRef.current) {
        if (severityChartRef.current) severityChartRef.current.destroy();
        severityChartRef.current = new Chart(severityChartCanvasRef.current.getContext("2d"), {
          type: "bar",
          data: {
            labels: sevLabels,
            datasets: [
              {
                label: "Frauds by Severity",
                data: sevValues,
                backgroundColor: "rgba(18, 128, 113, 0.75)",
                borderRadius: 6,
              },
            ],
          },
          options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
        });
      }

      if (trendChartCanvasRef.current) {
        if (trendChartRef.current) trendChartRef.current.destroy();
        trendChartRef.current = new Chart(trendChartCanvasRef.current.getContext("2d"), {
          type: "line",
          data: {
            labels: dayLabels,
            datasets: [
              {
                label: "Fraud Trend",
                data: dayValues,
                borderColor: "rgba(11, 59, 102, 0.95)",
                backgroundColor: "rgba(11, 59, 102, 0.2)",
                fill: true,
                tension: 0.32,
                pointRadius: 3,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } },
          },
        });
      }

      if (mixChartCanvasRef.current) {
        if (mixChartRef.current) mixChartRef.current.destroy();
        mixChartRef.current = new Chart(mixChartCanvasRef.current.getContext("2d"), {
          type: "doughnut",
          data: {
            labels: ["Fraud", "Safe"],
            datasets: [
              {
                data: [fraud, safeCount],
                backgroundColor: ["rgba(220, 38, 38, 0.8)", "rgba(18, 128, 113, 0.75)"],
                borderWidth: 1,
              },
            ],
          },
          options: { responsive: true, plugins: { legend: { position: "bottom" } } },
        });
      }
      log("Analytics refreshed");
    } catch (e) {
      log(`Analytics fetch failed: ${e.message}`);
    } finally {
      setAnalyticsLoading(false);
    }
  }

  async function loadAlerts() {
    setAlertsLoading(true);
    try {
      const qs = severityFilter ? `?severity=${encodeURIComponent(severityFilter)}` : "";
      const res = await fetchApi(`/alerts${qs}`);
      const data = await res.json();
      setAlerts(Array.isArray(data) ? data : []);
      log("Alerts refreshed");
    } catch (e) {
      setAlerts([]);
      log(`Alerts fetch failed: ${e.message}`);
    } finally {
      setAlertsLoading(false);
    }
  }

  async function loadCases() {
    setCasesLoading(true);
    try {
      const qs = severityFilter ? `?severity=${encodeURIComponent(severityFilter)}` : "";
      const res = await fetchApi(`/cases${qs}`);
      const data = await res.json();
      setCases(Array.isArray(data) ? data : []);
      log("Cases refreshed");
    } catch (e) {
      setCases([]);
      log(`Cases fetch failed: ${e.message}`);
    } finally {
      setCasesLoading(false);
    }
  }

  async function runDetect() {
    const fileEl = fileInputRef.current;
    if (!fileEl?.files?.length) {
      setDetectStatus("Choose a CSV file first.");
      return;
    }

    const fd = new FormData();
    fd.append("file", fileEl.files[0]);
    setDetectStatus("Running fraud detection...");
    setDetectLoading(true);

    try {
      const res = await fetchApi("/detect?lenient=1", { method: "POST", body: fd });
      const body = await res.json();
      setResults(body.results || []);
      const rowsProcessed = Number(body?.meta?.rows_processed ?? (body.results || []).length);
      const processingMs = Number(body?.meta?.processing_ms ?? 0);
      const durationText = processingMs > 0 ? ` in ${(processingMs / 1000).toFixed(2)}s` : "";
      setDetectStatus(`Done. ${rowsProcessed} rows processed${durationText}.`);
      setOnboardingTasks((prev) => ({ ...prev, firstDetectRun: true }));
      notify("Detection completed");
      log(`Processed upload: ${fileEl.files[0].name}`);
      await refreshAll();
    } catch (e) {
      const message = String(e?.message || "Unknown error");
      if (message.toLowerCase().includes("failed to fetch")) {
        const originLabel = window.location.origin === "null" ? "file:// or restricted preview" : window.location.origin;
        setDetectStatus(
          `Detection failed: cannot reach API from ${originLabel}. Use http://127.0.0.1:5500/website/ and API base http://127.0.0.1:8000.`
        );
      } else {
        setDetectStatus(`Detection failed: ${message}`);
      }
      log(`Detection failed: ${e.message}`);
    } finally {
      setDetectLoading(false);
    }
  }

  async function downloadFraudPdf() {
    try {
      const res = await fetchApi("/download/fraud-pdf");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "fraud-transactions-report.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      log("Fraud PDF downloaded");
      notify("Fraud PDF downloaded");
    } catch (e) {
      log(`PDF download failed: ${e.message}`);
      setDetectStatus(`PDF download failed: ${e.message}`);
    }
  }

  async function refreshAll() {
    setRefreshing(true);
    try {
      await Promise.all([checkHealth(), loadAnalytics(), loadAlerts(), loadCases()]);
      log("Manual refresh complete");
    } finally {
      setRefreshing(false);
    }
  }

  async function updateCaseStatus(alertId, status) {
    setCaseStateMap((prev) => ({ ...prev, [alertId]: { ...(prev[alertId] || {}), status } }));
    try {
      await fetchApi(`/cases/${encodeURIComponent(alertId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
    } catch {}
    setOnboardingTasks((prev) => ({ ...prev, firstCaseUpdated: true }));
    notify(`Case marked ${status}`);
  }

  async function assignCase(alertId) {
    const assignee = assigneeName.trim() || "unassigned";
    setCaseStateMap((prev) => ({
      ...prev,
      [alertId]: {
        ...(prev[alertId] || {}),
        assignee,
      },
    }));
    try {
      await fetchApi(`/cases/${encodeURIComponent(alertId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assignee }),
      });
    } catch {}
  }

  async function setCaseSla(alertId, slaAt) {
    setCaseSlaMap((prev) => ({ ...prev, [alertId]: slaAt || "" }));
    try {
      await fetchApi(`/cases/${encodeURIComponent(alertId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sla_due_at: slaAt || "" }),
      });
    } catch {}
    notify("SLA updated");
  }

  async function addCaseNote(alertId) {
    const note = String(caseNoteDrafts[alertId] || "").trim();
    if (!note) return;
    const entry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      text: note,
      at: new Date().toISOString(),
      by: assigneeName.trim() || "analyst",
    };
    setCaseNotesMap((prev) => ({
      ...prev,
      [alertId]: [entry, ...(prev[alertId] || [])].slice(0, 20),
    }));
    setCaseNoteDrafts((prev) => ({ ...prev, [alertId]: "" }));
    try {
      await fetchApi(`/cases/${encodeURIComponent(alertId)}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: note, author: assigneeName.trim() || "analyst" }),
      });
    } catch {}
    notify("Case note added");
  }

  function runPlaybook(name) {
    const entry = `${new Date().toLocaleTimeString()} - ${name} executed`;
    setPlaybookLog((prev) => [entry, ...prev].slice(0, 8));
    log(`Playbook run: ${name}`);
    notify(`${name} triggered`);
  }

  useEffect(() => {
    if (!firebaseAuth) return;
    const unsub = onAuthStateChanged(firebaseAuth, async (user) => {
      setAuthUser(user || null);
      if (user) setAuthToken(await user.getIdToken());
      else setAuthToken("");
      if (user) setOnboardingTasks((prev) => ({ ...prev, signedIn: true }));
      setAuthReady(true);
    });
    return () => unsub();
  }, []);

  useEffect(() => {
    const ticker = setInterval(() => setUtcTime(new Date().toISOString().slice(11, 19)), 1000);
    return () => clearInterval(ticker);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      if (!alerts.length) return;
      const item = alerts[Math.floor(Math.random() * alerts.length)];
      setLivePulse((prev) =>
        [{ id: `${Date.now()}`, text: `${item.transaction_id || "TXN"} ${String(item.severity || "low").toUpperCase()} signal` }, ...prev].slice(0, 6)
      );
    }, 4500);
    return () => clearInterval(timer);
  }, [alerts]);

  useEffect(() => {
    if (theme !== "dark") setTheme("dark");
    document.body.dataset.theme = "dark";
    document.body.classList.toggle("compact", Boolean(compactMode));
    document.body.classList.toggle("reduced-motion", Boolean(reducedMotion));
  }, [theme, compactMode]);

  useEffect(() => {
    const isDark = theme === "dark";
    Chart.defaults.color = isDark ? "#b7c8e3" : "#415070";
    Chart.defaults.borderColor = isDark ? "rgba(167, 193, 230, 0.25)" : "rgba(65, 80, 112, 0.18)";
    if (!authReady) return;
    if (HAS_FIREBASE_CONFIG && !authUser) return;
    loadAnalytics();
  }, [theme, authReady, authUser, authToken, apiBase]);

  useEffect(() => {
    if (!autoRefreshSec || Number(autoRefreshSec) <= 0) return;
    if (!authReady) return;
    if (HAS_FIREBASE_CONFIG && !authUser) return;
    const timer = setInterval(() => {
      refreshAll();
    }, Number(autoRefreshSec) * 1000);
    return () => clearInterval(timer);
  }, [autoRefreshSec, authReady, authUser, authToken, apiBase]);

  useEffect(() => {
    if (!authReady) return;
    if (HAS_FIREBASE_CONFIG && !authUser) return;
    checkHealth();
    loadAnalytics();
    loadAlerts();
    loadCases();
    setOnboardingTasks((prev) => ({
      ...prev,
      apiConfigured: Boolean(apiBase && !apiBase.includes("127.0.0.1")) || apiBase === "http://127.0.0.1:8000",
    }));
    log("Console initialized");
  }, [apiBase, authReady, authToken, authUser]);

  useEffect(() => {
    if (!authReady) return;
    if (HAS_FIREBASE_CONFIG && !authUser) return;
    loadAlerts();
    loadCases();
  }, [severityFilter, authReady, authUser, authToken]);

  useEffect(() => {
    return () => {
      if (dayChartRef.current) dayChartRef.current.destroy();
      if (severityChartRef.current) severityChartRef.current.destroy();
      if (trendChartRef.current) trendChartRef.current.destroy();
      if (mixChartRef.current) mixChartRef.current.destroy();
    };
  }, []);

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "/" && view === "investigator") {
        const input = document.getElementById("caseSearch");
        if (input) {
          event.preventDefault();
          input.focus();
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [view]);

  const apiText = apiOk === null ? "API Unknown" : apiOk ? "API Healthy" : "API Offline";
  const needsApiBase = (window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") && (apiBase.includes("127.0.0.1") || apiBase.includes("localhost"));

  const severityCounts = useMemo(() => {
    const out = { high: 0, medium: 0, low: 0 };
    for (const a of alerts) {
      const sev = String(a.severity || "").toLowerCase();
      if (out[sev] != null) out[sev] += 1;
    }
    return out;
  }, [alerts]);

  const threatLevel = useMemo(() => {
    const rate = Number(metrics.rate || 0);
    if (rate >= 0.3 || severityCounts.high > 0) return "Critical";
    if (rate >= 0.12 || severityCounts.medium > 0) return "Elevated";
    return "Stable";
  }, [metrics.rate, severityCounts.high, severityCounts.medium]);

  const threatClass = useMemo(() => {
    if (threatLevel === "Critical") return "threat-critical";
    if (threatLevel === "Elevated") return "threat-elevated";
    return "threat-stable";
  }, [threatLevel]);

  const threatScore = useMemo(() => {
    const rateScore = Math.min(80, Math.round((metrics.rate || 0) * 180));
    const alertScore = Math.min(20, severityCounts.high * 6 + severityCounts.medium * 2);
    return Math.min(100, rateScore + alertScore);
  }, [metrics.rate, severityCounts.high, severityCounts.medium]);

  const investigatorCases = useMemo(
    () => {
      const source = cases.length
        ? cases.map((caseItem, idx) => ({
            id: caseItem.case_id || caseItem.id || `case-${idx}`,
            transaction_id: caseItem.transaction_id || "N/A",
            reason: caseItem.reason || "Anomalous pattern detected",
            severity: caseItem.severity || "unknown",
            status: caseItem.status || "open",
            assignee: caseItem.assignee || "unassigned",
            sla_due_at: caseItem.sla_due_at || "",
            notes_count: Number(caseItem.notes_count || 0),
          }))
        : alerts.map((a, idx) => ({
            id: String(a.id || `${a.transaction_id || "txn"}-${idx}`),
            transaction_id: a.transaction_id || "N/A",
            reason: a.reason || "Anomalous pattern detected",
            severity: a.severity || "unknown",
            status: a.status || "open",
            assignee: "unassigned",
            sla_due_at: "",
            notes_count: 0,
          }));

      return source.map((a) => {
        const id = String(a.id);
        const local = caseStateMap[id] || {};
        return {
          id,
          transaction_id: a.transaction_id,
          reason: a.reason,
          severity: a.severity,
          status: local.status || a.status,
          assignee: local.assignee || a.assignee,
          sla_due_at: caseSlaMap[id] || a.sla_due_at || "",
          notes_count: (caseNotesMap[id] || []).length || a.notes_count,
        };
      });
    },
    [alerts, cases, caseStateMap, caseSlaMap, caseNotesMap]
  );

  const filteredCases = useMemo(() => {
    const q = alertsQuery.trim().toLowerCase();
    if (!q) return investigatorCases;
    return investigatorCases.filter((item) => {
      return (
        String(item.transaction_id).toLowerCase().includes(q) ||
        String(item.reason).toLowerCase().includes(q) ||
        String(item.assignee).toLowerCase().includes(q)
      );
    });
  }, [investigatorCases, alertsQuery]);

  const caseCounts = useMemo(() => {
    const out = { open: 0, investigating: 0, resolved: 0 };
    for (const c of investigatorCases) {
      const status = String(c.status || "").toLowerCase();
      if (out[status] != null) out[status] += 1;
    }
    return out;
  }, [investigatorCases]);

  const simulatedFraud = useMemo(() => {
    const data = results.map((r) => Number(r.probability || 0));
    if (!data.length) return Math.round(metrics.total * metrics.rate);
    return data.filter((p) => p >= simThreshold).length;
  }, [results, simThreshold, metrics.total, metrics.rate]);

  const modelGovernance = useMemo(() => {
    const probs = results.map((r) => Number(r.model_probability || 0)).filter((v) => !Number.isNaN(v));
    const avgProb = probs.length ? probs.reduce((sum, value) => sum + value, 0) / probs.length : 0;
    const fraudHitRate = results.length ? results.filter((r) => Boolean(r.predicted_fraud)).length / results.length : metrics.rate;
    const driftScore = Math.min(100, Math.round(Math.abs(fraudHitRate - metrics.rate) * 300));
    return {
      avgProb,
      fraudHitRate,
      driftScore,
      stability: driftScore >= 35 ? "Needs Review" : driftScore >= 18 ? "Watch" : "Stable",
    };
  }, [results, metrics.rate]);

  const onboardingProgress = useMemo(() => {
    const total = 4;
    const done = Object.values(onboardingTasks).filter(Boolean).length;
    return { done, total, pct: Math.round((done / total) * 100) };
  }, [onboardingTasks]);

  if (authReady && HAS_FIREBASE_CONFIG && !authUser) {
    return html`
      <div className="auth-shell" onClickCapture=${(e) => {
        const target = e.target?.closest?.("button, .btn, .nav-btn");
        if (target) playClickSound();
      }}>
        <div className="auth-card">
          <div className="brand auth-brand">
            <div className="brand-mark brand-mark-auth">
              <img src="assets/risk-atlas-icon.png?v=4" alt="Risk Atlas emblem" />
            </div>
            <div>
              <h1>Risk Atlas</h1>
              <p>Cyber Fraud Intelligence Console</p>
            </div>
          </div>
          <h2>Secure Access</h2>
          <p className="auth-sub">Sign in to access real-time fraud intelligence, investigation workflows, and executive risk reporting.</p>
          <div className="auth-highlights">
            <span><b>Zero Trust</b><small>Session-bound access control</small></span>
            <span><b>Live Signals</b><small>Streaming fraud telemetry</small></span>
            <span><b>Audit Trail</b><small>Case events + model evidence</small></span>
          </div>
          <input type="email" value=${email} onInput=${(e) => setEmail(e.target.value)} placeholder="Email" />
          <input type="password" value=${password} onInput=${(e) => setPassword(e.target.value)} placeholder="Password" />
          <div className="auth-actions">
            <button className="btn btn-primary" disabled=${authBusy || !HAS_FIREBASE_CONFIG} onClick=${signInEmail}>Sign In</button>
            <button className="btn btn-ghost" disabled=${authBusy || !HAS_FIREBASE_CONFIG} onClick=${signUpEmail}>Sign Up</button>
            <button className="btn btn-ghost" disabled=${authBusy || !HAS_FIREBASE_CONFIG} onClick=${signInGoogle}>Google</button>
          </div>
          ${authError ? html`<p className="auth-error">${authError}</p>` : null}
          <div className="auth-foot">
            <p>API Base</p>
            <input value=${apiBase} onInput=${(e) => setApiBase(e.target.value)} placeholder="https://your-api.onrender.com" />
          </div>
        </div>
      </div>
    `;
  }

  return html`
    <div onClickCapture=${(e) => {
      const target = e.target?.closest?.("button, .btn, .nav-btn");
      if (target) playClickSound();
    }}>
      ${toast ? html`<div className="toast">${toast}</div>` : null}
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark brand-mark-top">
            <img src="assets/risk-atlas-icon.png?v=4" alt="Risk Atlas emblem" />
          </div>
          <div>
            <h1>Risk Atlas</h1>
            <p>Cyber Fraud Intelligence Console</p>
          </div>
        </div>
        <div className="topbar-actions">
          <${StatusChip} ok=${apiOk} text=${apiText} />
          <span className="status-chip">UTC ${utcTime}</span>
          <span className=${`status-chip ${threatClass}`}>Threat ${threatLevel}</span>
          <button className="btn btn-ghost" onClick=${refreshAll} disabled=${refreshing}>${refreshing ? "Refreshing..." : "Refresh All"}</button>
          <button className="btn btn-ghost" onClick=${checkHealth}>Check Health</button>
          <button className="btn btn-ghost" onClick=${signOutNow}>Sign Out</button>
        </div>
      </header>

      <main className="layout">
        ${needsApiBase ? html`
          <div className="card" style=${{ borderColor: "#ffcfad", background: "#fff7ef" }}>
            <h3 style=${{ marginTop: 0 }}>API Base Not Set</h3>
            <p>This deployment still points to local API. Set your production Render URL.</p>
          </div>
        ` : null}

        <aside className="sidebar">
          <button className=${`nav-btn ${view === "soc" ? "active" : ""}`} onClick=${() => setView("soc")}><${NavGlyph} kind="soc" />SOC Dashboard</button>
          <button className=${`nav-btn ${view === "investigator" ? "active" : ""}`} onClick=${() => setView("investigator")}><${NavGlyph} kind="investigator" />Investigator</button>
          <button className=${`nav-btn ${view === "upload" ? "active" : ""}`} onClick=${() => setView("upload")}><${NavGlyph} kind="upload" />Upload + Detect</button>
          <button className=${`nav-btn ${view === "model" ? "active" : ""}`} onClick=${() => setView("model")}><${NavGlyph} kind="model" />Model Ops</button>
          <button className=${`nav-btn ${view === "executive" ? "active" : ""}`} onClick=${() => setView("executive")}><${NavGlyph} kind="executive" />Executive View</button>
          <button className=${`nav-btn ${view === "history" ? "active" : ""}`} onClick=${() => setView("history")}><${NavGlyph} kind="history" />Activity Log</button>

          <div className="sidebar-footer">
            <p>Signed in as</p>
            <p style=${{ marginTop: 0, fontSize: "0.8rem" }}>${authUser?.email || authUser?.uid || "unknown"}</p>
            <p>API Settings</p>
            <input value=${apiBase} onInput=${(e) => setApiBase(e.target.value)} placeholder="https://your-api.onrender.com" />
            <button className="btn btn-ghost" onClick=${() => setSettingsOpen((s) => !s)}>${settingsOpen ? "Hide Settings" : "Open Settings"}</button>
            ${settingsOpen ? html`
              <div className="settings-panel">
                <p className="settings-title">Appearance</p>
                <div className="status-chip">Theme: Dark</div>
                <label className="switch-row"><input type="checkbox" checked=${Boolean(compactMode)} onChange=${(e) => setCompactMode(e.target.checked)} />Compact UI</label>
                <label className="switch-row"><input type="checkbox" checked=${Boolean(reducedMotion)} onChange=${(e) => setReducedMotion(e.target.checked)} />Reduced motion</label>
                <label className="switch-row"><input type="checkbox" checked=${Boolean(soundFx)} onChange=${(e) => setSoundFx(e.target.checked)} />Sound FX</label>
                <p className="settings-title">Automation</p>
                <select value=${String(autoRefreshSec)} onChange=${(e) => setAutoRefreshSec(Number(e.target.value))}>
                  <option value="0">Auto refresh off</option>
                  <option value="30">Every 30 sec</option>
                  <option value="60">Every 1 min</option>
                  <option value="180">Every 3 min</option>
                </select>
              </div>
            ` : null}
          </div>
        </aside>

        <section className="content">
          <section className=${`view view-soc ${view === "soc" ? "active" : ""}`}>
            <div className="hero card hero-cyber">
              <div>
                <div className="hero-brand-emblem">
                  <img src="assets/risk-atlas-hero-3d.png" alt="Risk Atlas Emblem" />
                </div>
                <div className="hero-pill-row">
                  <span className="hero-pill">Threat Intelligence</span>
                  <span className="hero-pill">SOC Automation</span>
                  <span className="hero-pill">Compliance Ready</span>
                </div>
                <h2>Global Threat Intelligence, Local Precision</h2>
                <p>Detect fraud, manage risk, and orchestrate response with an executive-grade command experience.</p>
                <div className="hero-actions">
                  <a className="btn btn-primary" href="#" onClick=${(e) => (e.preventDefault(), setView("upload"))}>Run Detection</a>
                  <a className="btn btn-ghost" href="../sample_transactions.csv" download>Download CSV Template</a>
                  <button className="btn btn-ghost" onClick=${downloadFraudPdf}>Download Fraud PDF</button>
                </div>
              </div>
              <div className="hero-metrics">
                <div className="metric metric-cyber"><span>Total Txns</span><strong>${metrics.total}</strong></div>
                <div className="metric metric-cyber"><span>Fraud Cases</span><strong>${metrics.fraud}</strong></div>
                <div className="metric metric-cyber"><span>Fraud Rate</span><strong>${(metrics.rate * 100).toFixed(2)}%</strong></div>
              </div>
            </div>

            <div className="card posture-card">
              <h3 style=${{ marginTop: 0 }}>Threat Posture</h3>
              <p style=${{ marginBottom: "0.4rem" }}>Current state: <strong>${threatLevel}</strong>. Score blends fraud-rate and live severity mix.</p>
              <div className="posture-meter">
                <div className="posture-meter-fill" style=${{ width: `${threatScore}%` }}></div>
              </div>
              <small>Threat Score: ${threatScore}/100 | High: ${severityCounts.high} | Medium: ${severityCounts.medium} | Low: ${severityCounts.low}</small>
            </div>

            <div className="card">
              <h3 style=${{ marginTop: 0 }}>Onboarding Progress</h3>
              <div className="posture-meter">
                <div className="posture-meter-fill" style=${{ width: `${onboardingProgress.pct}%` }}></div>
              </div>
              <small>${onboardingProgress.done}/${onboardingProgress.total} setup actions completed</small>
              <ul className="task-list">
                <li className=${onboardingTasks.signedIn ? "done" : ""}>Signed in to workspace</li>
                <li className=${onboardingTasks.apiConfigured ? "done" : ""}>API base configured</li>
                <li className=${onboardingTasks.firstDetectRun ? "done" : ""}>First detection completed</li>
                <li className=${onboardingTasks.firstCaseUpdated ? "done" : ""}>First case status updated</li>
              </ul>
            </div>

            <div className="card">
              <h3>Live Alert Stream</h3>
              ${alertsLoading ? html`<p className="muted">Loading alerts...</p>` : null}
              <div className="alert-list">
                ${alerts.length === 0
                  ? html`<p>No alerts yet.</p>`
                  : alerts.slice(0, 8).map((a, idx) => html`
                      <div key=${a.id || idx} className="alert-item">
                        <strong>${a.transaction_id || "N/A"}</strong>
                        <p>${a.reason || "Anomalous pattern detected"}</p>
                        <small>Severity: ${a.severity || "unknown"} | Status: ${a.status || "open"}</small>
                      </div>
                    `)}
              </div>
            </div>

            <div className="card">
              <h3>Real-Time Event Pulse</h3>
              <p className="muted">Continuous stream simulation for SOC situational awareness.</p>
              <ul className="history-list">
                ${(livePulse.length ? livePulse : [{ id: "idle", text: "Waiting for incoming signals..." }]).map((item) =>
                  html`<li key=${item.id}>${item.text}</li>`
                )}
              </ul>
            </div>
          </section>

          <section className=${`view view-investigator ${view === "investigator" ? "active" : ""}`}>
            <div className="card">
              <h3>Investigator Workbench</h3>
              <p>Assign and track cases directly from alert stream.</p>
              <div className="filters">
                <input id="caseSearch" value=${alertsQuery} onInput=${(e) => setAlertsQuery(e.target.value)} placeholder="Search cases (/)" />
                <input value=${assigneeName} onInput=${(e) => setAssigneeName(e.target.value)} placeholder="assignee@riskatlas" />
                <select value=${severityFilter} onChange=${(e) => setSeverityFilter(e.target.value)}>
                  <option value="">All Severities</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <button className="btn btn-ghost" onClick=${loadAlerts}>Refresh Cases</button>
              </div>
              <div className="hero-metrics" style=${{ marginBottom: "0.8rem" }}>
                <div className="metric"><span>Open</span><strong>${caseCounts.open}</strong></div>
                <div className="metric"><span>Investigating</span><strong>${caseCounts.investigating}</strong></div>
                <div className="metric"><span>Resolved</span><strong>${caseCounts.resolved}</strong></div>
              </div>
              ${(alertsLoading || casesLoading) ? html`<p className="muted">Loading investigator queue...</p>` : null}
              <div className="alert-list">
                ${filteredCases.length === 0
                  ? html`<p>No cases available.</p>`
                  : filteredCases.map((c) => html`
                      <div key=${c.id} className="alert-item">
                        <strong>${c.transaction_id}</strong>
                        <p>${c.reason}</p>
                        <small>Severity: ${c.severity} | Assignee: ${c.assignee} | Notes: ${c.notes_count}</small>
                        <div className="filters" style=${{ marginTop: "0.6rem" }}>
                          <select value=${c.status} onChange=${(e) => updateCaseStatus(c.id, e.target.value)}>
                            <option value="open">open</option>
                            <option value="investigating">investigating</option>
                            <option value="resolved">resolved</option>
                          </select>
                          <button className="btn btn-ghost" onClick=${() => assignCase(c.id)}>Assign To Me</button>
                          <input
                            type="datetime-local"
                            value=${c.sla_due_at}
                            onInput=${(e) => setCaseSla(c.id, e.target.value)}
                            title="SLA due time"
                          />
                        </div>
                        <div className="filters" style=${{ marginTop: "0.35rem" }}>
                          <input
                            value=${caseNoteDrafts[c.id] || ""}
                            onInput=${(e) => setCaseNoteDrafts((prev) => ({ ...prev, [c.id]: e.target.value }))}
                            placeholder="Add investigation note"
                          />
                          <button className="btn btn-ghost" onClick=${() => addCaseNote(c.id)}>Add Note</button>
                        </div>
                        ${(caseNotesMap[c.id] || []).slice(0, 2).map((n) => html`<small key=${n.id}>${n.by}: ${n.text}</small>`)}
                      </div>
                    `)}
              </div>
            </div>
          </section>

          <section className=${`view view-upload ${view === "upload" ? "active" : ""}`}>
            <div className="card">
              <h3>Upload Transactions CSV</h3>
              <p>Tip: headers like <code>time</code> or <code>merchant</code> are auto-mapped where possible.</p>
              <div className="upload-row">
                <input ref=${fileInputRef} type="file" accept=".csv" />
                <button className="btn btn-primary" onClick=${runDetect} disabled=${detectLoading}>${detectLoading ? "Detecting..." : "Run Fraud Detection"}</button>
              </div>
              <div className="info">${detectStatus}</div>
            </div>

            <div className="card">
              <h3>Detection Results</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Transaction</th>
                      <th>Fraud</th>
                      <th>Hybrid Prob.</th>
                      <th>Model Prob.</th>
                      <th>Rule Prob.</th>
                      <th>Risk Band</th>
                      <th>Explanation</th>
                      <th>Stored</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${results.map((r) => html`
                      <tr key=${r.transaction_id}>
                        <td>${r.transaction_id}</td>
                        <td><span className=${`badge ${r.predicted_fraud ? "badge-fraud" : "badge-safe"}`}>${r.predicted_fraud ? "Fraud" : "Safe"}</span></td>
                        <td>${(Number(r.probability || 0) * 100).toFixed(2)}%</td>
                        <td>${(Number(r.model_probability || 0) * 100).toFixed(2)}%</td>
                        <td>${(Number(r.rules_probability || 0) * 100).toFixed(2)}%</td>
                        <td><span className=${`badge ${String(r.risk_band || "low") === "critical" || String(r.risk_band || "low") === "high" ? "badge-fraud" : "badge-safe"}`}>${r.risk_band || "-"}</span></td>
                        <td>
                          <div className="explain-cell">
                            <span>${String(r.explanation || "-").slice(0, 80)}${String(r.explanation || "").length > 80 ? "..." : ""}</span>
                            <button className="btn btn-ghost" onClick=${() => setExplainDrawer(r)}>View</button>
                          </div>
                        </td>
                        <td>${r.stored ? "Yes" : `No (${r.store_error || "error"})`}</td>
                      </tr>
                    `)}
                  </tbody>
                </table>
              </div>
            </div>
            ${explainDrawer
              ? html`
                  <div className="card explain-drawer">
                    <div className="drawer-head">
                      <h3>Explainability Detail - ${explainDrawer.transaction_id}</h3>
                      <button className="btn btn-ghost" onClick=${() => setExplainDrawer(null)}>Close</button>
                    </div>
                    <div className="kpi-grid">
                      <div className="kpi-card"><span>Hybrid Prob</span><strong>${(Number(explainDrawer.probability || 0) * 100).toFixed(2)}%</strong></div>
                      <div className="kpi-card"><span>Model Prob</span><strong>${(Number(explainDrawer.model_probability || 0) * 100).toFixed(2)}%</strong></div>
                      <div className="kpi-card"><span>Rule Prob</span><strong>${(Number(explainDrawer.rules_probability || 0) * 100).toFixed(2)}%</strong></div>
                    </div>
                    <p><strong>Risk Band:</strong> ${explainDrawer.risk_band || "-"}</p>
                    <p><strong>Explanation:</strong> ${explainDrawer.explanation || "-"}</p>
                    <p><strong>Signals:</strong> ${(explainDrawer.signals || []).join(" | ") || "-"}</p>
                  </div>
                `
              : null}
          </section>

          <section className=${`view view-model ${view === "model" ? "active" : ""}`}>
            <div className="card">
              <h3>Model Ops Dashboard</h3>
              ${analyticsLoading ? html`<p className="muted">Refreshing analytics...</p>` : null}
              <p>Tune decision threshold to simulate fraud hit-rate in current session results.</p>
              <div className="slider-wrap">
                <label>Simulation Threshold: <strong>${simThreshold.toFixed(2)}</strong></label>
                <input type="range" min="0.1" max="0.95" step="0.01" value=${simThreshold} onInput=${(e) => setSimThreshold(Number(e.target.value))} />
              </div>
              <div className="hero-metrics" style=${{ marginTop: "0.8rem" }}>
                <div className="metric"><span>Simulated Fraud Hits</span><strong>${simulatedFraud}</strong></div>
                <div className="metric"><span>Baseline Fraud</span><strong>${metrics.fraud}</strong></div>
                <div className="metric"><span>Current Threshold</span><strong>0.50</strong></div>
              </div>
            </div>
            <div className="card">
              <h3>Governance & Drift Monitor</h3>
              <div className="hero-metrics">
                <div className="metric"><span>Average Model Prob</span><strong>${(modelGovernance.avgProb * 100).toFixed(2)}%</strong></div>
                <div className="metric"><span>Session Fraud Hit-Rate</span><strong>${(modelGovernance.fraudHitRate * 100).toFixed(2)}%</strong></div>
                <div className="metric"><span>Drift Score</span><strong>${modelGovernance.driftScore}</strong></div>
              </div>
              <p style=${{ marginTop: "0.5rem" }}>Model Stability: <strong>${modelGovernance.stability}</strong></p>
            </div>
            <div className="card">
              <h3>Analytics Charts</h3>
              <div className="chart-grid">
                <div className="chart-box"><canvas ref=${dayChartCanvasRef}></canvas></div>
                <div className="chart-box"><canvas ref=${severityChartCanvasRef}></canvas></div>
              </div>
              <div style=${{ marginTop: "0.8rem" }}>
                <button className="btn btn-ghost" onClick=${loadAnalytics}>Refresh Analytics</button>
              </div>
            </div>
          </section>

          <section className=${`view view-executive ${view === "executive" ? "active" : ""}`}>
            <div className="card">
              <h3>Executive Dashboard</h3>
              <p>High-level performance and risk exposure for strategic reporting.</p>
              <div className="hero-metrics">
                <div className="metric"><span>Risk Posture</span><strong>${threatLevel}</strong></div>
                <div className="metric"><span>Threat Score</span><strong>${threatScore}</strong></div>
                <div className="metric"><span>Resolved Cases</span><strong>${caseCounts.resolved}</strong></div>
              </div>
              <div className="kpi-grid">
                <div className="kpi-card">
                  <span>Operational Signal</span>
                  <strong>${metrics.total > 0 ? "Active Monitoring" : "No Ingest Yet"}</strong>
                </div>
                <div className="kpi-card">
                  <span>Fraud Density</span>
                  <strong>${(metrics.rate * 100).toFixed(2)}%</strong>
                </div>
                <div className="kpi-card">
                  <span>Alert Pressure</span>
                  <strong>${alerts.length} alerts</strong>
                </div>
              </div>
              <div className="chart-grid" style=${{ marginTop: "0.9rem" }}>
                <div className="chart-box"><canvas ref=${trendChartCanvasRef}></canvas></div>
                <div className="chart-box"><canvas ref=${mixChartCanvasRef}></canvas></div>
              </div>
              <div className="card" style=${{ marginTop: "0.9rem" }}>
                <h3>Response Playbooks</h3>
                <div className="hero-actions">
                  <button className="btn btn-ghost" onClick=${() => runPlaybook("Freeze High-Risk Accounts")}>Freeze Accounts</button>
                  <button className="btn btn-ghost" onClick=${() => runPlaybook("Escalate to L2 SOC")}>Escalate L2</button>
                  <button className="btn btn-ghost" onClick=${() => runPlaybook("Request KYC Re-Verification")}>Request KYC</button>
                </div>
                <ul className="history-list" style=${{ marginTop: "0.6rem" }}>
                  ${(playbookLog.length ? playbookLog : ["No playbooks executed yet."]).map((item, i) => html`<li key=${i}>${item}</li>`)}
                </ul>
              </div>
            </div>
          </section>

          <section className=${`view view-history ${view === "history" ? "active" : ""}`}>
            <div className="card">
              <h3>Action History</h3>
              <ul className="history-list">
                ${history.map((h, i) => html`<li key=${i}>${h}</li>`)}
              </ul>
            </div>
          </section>
        </section>
      </main>
    </div>
  `;
}

createRoot(document.getElementById("root")).render(html`<${App} />`);
