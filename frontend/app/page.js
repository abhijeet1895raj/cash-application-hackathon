"use client";
import { useState, useRef, useEffect } from "react";

const AGENT_META = {
  BankStatementIntelligenceAgent: { label: "Bank Statement Parser", icon: "🏦", color: "#3b82f6", bg: "#eff6ff", model: "gpt-4o-mini", modelColor: "#059669" },
  ARLedgerAgent:                  { label: "Open AR Ledger",        icon: "📒", color: "#10b981", bg: "#f0fdf4", model: "gpt-4o-mini", modelColor: "#059669" },
  ReconciliationAgent:            { label: "Reconciliation Engine", icon: "⚖️",  color: "#f59e0b", bg: "#fffbeb", model: "gpt-4o + Code Interpreter", modelColor: "#2563eb" },
  MismatchReasoningAgent:         { label: "Mismatch Reasoning",   icon: "🧠", color: "#ef4444", bg: "#fef2f2", model: "gpt-4o",       modelColor: "#7c3aed" },
  CashPostingAgent:               { label: "Cash Posting",          icon: "✅", color: "#8b5cf6", bg: "#f5f3ff", model: "gpt-4o",       modelColor: "#2563eb" },
};

const AGENT_ORDER = Object.keys(AGENT_META);

// Maps agent-emitted flag codes (t.flags array) → display badge
const FLAG_BADGE = {
  MISSING_REMITTANCE:         { label: "No Remittance",      color: "#8b5cf6", group: "REMITTANCE" },
  NO_INVOICE:                 { label: "No Invoice Ref",     color: "#8b5cf6", group: "REMITTANCE" },
  LEGACY_INVOICE_REF:         { label: "Legacy Ref",         color: "#6366f1", group: "REMITTANCE" },
  EDI_PENDING:                { label: "EDI Pending",        color: "#8b5cf6", group: "REMITTANCE" },
  POSSIBLE_DUPLICATE:         { label: "Duplicate ⚠",        color: "#ef4444", group: "TIMING" },
  NSF:                        { label: "NSF Return ⚠",       color: "#dc2626", group: "TIMING" },
  POST_DATED_CHECK:           { label: "Post-Dated Chk",    color: "#b45309", group: "TIMING" },
  STALE_CHECK:                { label: "Stale Check ⚠",     color: "#dc2626", group: "TIMING" },
  PREPAYMENT:                 { label: "Prepayment",         color: "#0284c7", group: "TIMING" },
  FX_PAYMENT:                 { label: "FX / Multi-Currency",color: "#0ea5e9", group: "FX" },
  SWIFT_NAME_TRUNCATION:      { label: "SWIFT Name Trunc.", color: "#7c3aed", group: "IDENTITY" },
  DBA_NAME:                   { label: "DBA Name",           color: "#7c3aed", group: "IDENTITY" },
  POST_ACQUISITION_NAME:      { label: "Post-M&A Name",     color: "#7c3aed", group: "IDENTITY" },
  PARENT_SUBSIDIARY_PAYMENT:  { label: "Parent Pays Sub",   color: "#db2777", group: "ENTITY" },
  FACTORING_AGENT:            { label: "Factoring Agent",   color: "#db2777", group: "ENTITY" },
  THIRD_PARTY_PAYMENT:        { label: "Third-Party",       color: "#db2777", group: "ENTITY" },
  CROSS_BORDER_ENTITY:        { label: "Cross-Border",      color: "#db2777", group: "ENTITY" },
  INTERCOMPANY_NETTING:       { label: "Interco Net",       color: "#0891b2", group: "ENTITY" },
  LATE_DISCOUNT:              { label: "Late Discount ⚠",   color: "#ef4444", group: "AMOUNT" },
  LARGE_ROUND_NUMBER:         { label: "Large Round Amt",   color: "#f97316", group: "AMOUNT" },
  OFAC_SCREENING_TRIGGERED:   { label: "🔴 OFAC Hold",       color: "#dc2626", group: "COMPLIANCE" },
  SANCTIONS_HOLD:             { label: "🔴 Sanctions Hold",  color: "#dc2626", group: "COMPLIANCE" },
  WRONG_LEGAL_ENTITY:         { label: "Wrong Entity ⚠",    color: "#dc2626", group: "COMPLIANCE" },
  DISPUTED_INVOICE:           { label: "Disputed Inv ⚠",    color: "#b91c1c", group: "COMPLIANCE" },
};

function fmt(n) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(n);
}

function AgentPipeline({ agentStates }) {
  return (
    <div className="flex flex-col gap-2">
      {AGENT_ORDER.map((key, i) => {
        const meta = AGENT_META[key];
        const state = agentStates[key] || {};
        const status = state.status || "idle";
        const tokens = state.tokens || 0;
        const isActive = status === "streaming";
        const isDone = status === "done";

        return (
          <div
            key={key}
            style={{
              background: isDone ? meta.bg : isActive ? meta.bg : "#fff",
              border: `1.5px solid ${isActive || isDone ? meta.color : "#e2e8f0"}`,
              borderRadius: 10,
              padding: "10px 14px",
              transition: "all 0.3s",
              boxShadow: isActive ? `0 0 0 3px ${meta.color}22` : "none",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 18 }}>{meta.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: "#1e293b" }}>
                  {i + 1}. {meta.label}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                  <span style={{ background: meta.modelColor + "18", color: meta.modelColor, borderRadius: 4, padding: "1px 6px", fontSize: 10, fontWeight: 700 }}>
                    {meta.model}
                  </span>
                  <span style={{ fontSize: 10, color: "#94a3b8" }}>{key}</span>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                {status === "idle" && <span style={{ fontSize: 11, color: "#94a3b8" }}>Waiting</span>}
                {isActive && (
                  <span style={{ fontSize: 11, color: meta.color, fontWeight: 600, animation: "pulse 1s infinite" }}>
                    ● Streaming
                  </span>
                )}
                {isDone && (
                  <span style={{ fontSize: 11, color: meta.color, fontWeight: 600 }}>
                    ✓ Done
                  </span>
                )}
                {tokens > 0 && (
                  <div
                    style={{
                      fontSize: 10,
                      background: meta.color + "22",
                      color: meta.color,
                      borderRadius: 4,
                      padding: "1px 5px",
                      marginTop: 2,
                      fontWeight: 600,
                    }}
                  >
                    ~{tokens.toLocaleString()} tok
                  </div>
                )}
              </div>
            </div>
            {isActive && state.partialText && (
              <div
                style={{
                  marginTop: 8,
                  fontSize: 11,
                  color: "#475569",
                  background: "#f8fafc",
                  borderRadius: 6,
                  padding: "6px 8px",
                  fontFamily: "monospace",
                  maxHeight: 80,
                  overflow: "hidden",
                  borderLeft: `3px solid ${meta.color}`,
                }}
              >
                {state.partialText.slice(-400)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function LiveLog({ lines }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);

  return (
    <div
      ref={ref}
      style={{
        background: "#0f172a",
        borderRadius: 10,
        padding: "12px 14px",
        height: 260,
        overflowY: "auto",
        fontFamily: "monospace",
        fontSize: 11,
        color: "#94a3b8",
        marginTop: 16,
      }}
    >
      <div style={{ color: "#4ade80", marginBottom: 6, fontSize: 10 }}>
        ● LIVE LOG - Azure AI Foundry
      </div>
      {lines.map((l, i) => (
        <div key={i} style={{ color: l.color || "#94a3b8", lineHeight: "1.6" }}>
          {l.text}
        </div>
      ))}
      {lines.length === 0 && (
        <div style={{ color: "#475569" }}>Awaiting analysis run...</div>
      )}
    </div>
  );
}

const CATEGORY_META = {
  AMOUNT:      { label: "Amount Mismatches",      color: "#10b981", icon: "💰" },
  IDENTITY:    { label: "Identity & Name",         color: "#7c3aed", icon: "🏷" },
  ENTITY:      { label: "Multi-Entity",            color: "#db2777", icon: "🏢" },
  TIMING:      { label: "Timing & Sequencing",     color: "#b45309", icon: "⏱" },
  REMITTANCE:  { label: "Remittance & Reference",  color: "#8b5cf6", icon: "📋" },
  FX:          { label: "FX & International",      color: "#0ea5e9", icon: "💱" },
  COMPLIANCE:  { label: "Compliance & Legal",      color: "#dc2626", icon: "🔴" },
};

function EdgeCategoryLegend({ transactions }) {
  const counts = {};
  for (const t of (transactions || [])) {
    for (const flag of (t.flags || [])) {
      const badge = FLAG_BADGE[flag];
      if (badge?.group) counts[badge.group] = (counts[badge.group] || 0) + 1;
    }
  }

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 14 }}>
      {Object.entries(CATEGORY_META).map(([key, meta]) => (
        <div key={key} style={{ display: "flex", alignItems: "center", gap: 5, background: meta.color + "10", border: `1px solid ${meta.color}33`, borderRadius: 8, padding: "5px 10px" }}>
          <span style={{ fontSize: 14 }}>{meta.icon}</span>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: meta.color }}>{meta.label}</div>
            <div style={{ fontSize: 11, color: "#64748b" }}>{counts[key] || 0} transactions</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function BankStatementTable({ transactions }) {
  if (!transactions?.length) return null;
  return (
    <div>
      <EdgeCategoryLegend transactions={transactions} />
      <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ background: "#f1f5f9" }}>
            {["Txn ID", "Date", "Amount", "Type", "Payer", "Remittance", "Edge Case"].map((h) => (
              <th key={h} style={{ padding: "8px 10px", textAlign: "left", fontWeight: 600, color: "#475569", whiteSpace: "nowrap", borderBottom: "1px solid #e2e8f0" }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {transactions.map((t, i) => {
            const badges = (t.flags || []).map(f => FLAG_BADGE[f]).filter(Boolean);
            return (
              <tr key={t.txn_id} style={{ background: i % 2 === 0 ? "#fff" : "#f8fafc", borderBottom: "1px solid #f1f5f9" }}>
                <td style={{ padding: "7px 10px", fontFamily: "monospace", color: "#3b82f6", fontWeight: 600 }}>{t.txn_id}</td>
                <td style={{ padding: "7px 10px", color: "#475569" }}>{t.date}</td>
                <td style={{ padding: "7px 10px", fontWeight: 600, color: t.amount < 0 ? "#ef4444" : "#1e293b" }}>
                  {t.currency !== "USD" ? `${t.currency} ${t.amount.toLocaleString()}` : fmt(t.amount)}
                </td>
                <td style={{ padding: "7px 10px" }}>
                  <span style={{ background: "#f1f5f9", padding: "2px 6px", borderRadius: 4, fontSize: 10, color: "#64748b", fontWeight: 600 }}>
                    {t.payment_type}
                  </span>
                </td>
                <td style={{ padding: "7px 10px", color: "#1e293b", maxWidth: 160, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {t.payer_raw}
                </td>
                <td style={{ padding: "7px 10px", color: "#64748b", maxWidth: 180, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {t.remittance_text || <span style={{ color: "#cbd5e1" }}>-</span>}
                </td>
                <td style={{ padding: "7px 10px", minWidth: 120 }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                    {badges.length > 0 ? badges.map((badge, bi) => (
                      <span key={bi} style={{ background: badge.color + "18", color: badge.color, borderRadius: 4, padding: "2px 6px", fontSize: 9, fontWeight: 700, whiteSpace: "nowrap" }}>
                        {badge.label}
                      </span>
                    )) : <span style={{ color: "#cbd5e1", fontSize: 10 }}>-</span>}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
    </div>
  );
}

const MATCH_STATUS_COLOR = {
  MATCHED: "#10b981", ALIAS_MATCH: "#10b981", LEGACY_REF: "#10b981",
  DISCOUNT: "#06b6d4", MULTI_INVOICE: "#3b82f6", FIFO: "#8b5cf6",
  BANK_FEE_WRITEOFF: "#64748b", OVERPAYMENT: "#f97316", DUPLICATE_PAYMENT: "#ef4444",
  INSTALLMENT: "#a855f7", LATE_DISCOUNT: "#ef4444", PARENT_SUBSIDIARY: "#db2777",
  THIRD_PARTY_FACTORING: "#db2777", INTERCOMPANY_NET: "#0891b2",
  COMPLIANCE_HOLD: "#dc2626", WRONG_ENTITY: "#dc2626", DISPUTED_INVOICE_HOLD: "#b91c1c",
  POST_DATED_HOLD: "#b45309", STALE_CHECK_RETURN: "#dc2626",
  SUSPENSE_PREPAYMENT: "#0284c7", HOLD_EDI_PENDING: "#8b5cf6", UNMATCHED: "#94a3b8",
};

function ReconciliationResults({ data }) {
  if (!data) return null;
  // Agent returns: data.matches (array), data.reconciliation_summary
  const matches = data.matches || data.reconciliation_results || data.matched_payments || [];
  const summary = data.reconciliation_summary || data.summary || {};
  if (!matches.length) return null;

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Received", value: fmt(summary.total_cash_received || 0), color: "#3b82f6" },
          { label: "Exact Matches", value: summary.matched_exact || 0, color: "#10b981" },
          { label: "Exceptions", value: summary.matched_with_exceptions || 0, color: "#ef4444" },
          { label: "Compliance Holds", value: summary.compliance_holds || 0, color: "#dc2626" },
        ].map((s) => (
          <div key={s.label} style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, padding: 16, textAlign: "center" }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#f1f5f9" }}>
              {["Txn ID", "Amount", "Tier", "Invoices Matched", "Applied", "Δ Delta", "Confidence", "Status"].map((h) => (
                <th key={h} style={{ padding: "8px 10px", textAlign: "left", fontWeight: 600, color: "#475569", whiteSpace: "nowrap", borderBottom: "1px solid #e2e8f0" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matches.map((m, i) => {
              const confPct = m.confidence_pct || (m.confidence || 0) * 100;
              const confColor = confPct >= 95 ? "#10b981" : confPct >= 80 ? "#f59e0b" : "#ef4444";
              const status = m.match_status || m.status || "-";
              const statusColor = MATCH_STATUS_COLOR[status] || "#64748b";
              const invoiceIds = (m.matched_invoices || []).map(inv =>
                typeof inv === "string" ? inv : inv.invoice_id
              );
              const delta = m.delta || 0;
              const isException = m.exception || false;
              return (
                <tr key={i} style={{ background: isException ? "#fef2f2" : i % 2 === 0 ? "#fff" : "#f8fafc", borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "7px 10px", fontFamily: "monospace", color: "#3b82f6", fontWeight: 600 }}>{m.txn_id}</td>
                  <td style={{ padding: "7px 10px", fontWeight: 600, color: "#1e293b" }}>{fmt(m.transaction_amount || m.payment_amount || 0)}</td>
                  <td style={{ padding: "7px 10px" }}>
                    <span style={{ background: "#f1f5f9", padding: "2px 6px", borderRadius: 4, fontSize: 10, color: "#475569", fontWeight: 600 }}>
                      {m.match_tier != null ? `T${m.match_tier}` : "-"}
                    </span>
                  </td>
                  <td style={{ padding: "7px 10px", color: "#475569", fontSize: 11, maxWidth: 160, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {invoiceIds.slice(0, 3).join(", ") || <span style={{ color: "#cbd5e1" }}>-</span>}
                  </td>
                  <td style={{ padding: "7px 10px", fontWeight: 600, color: "#1e293b" }}>{fmt(m.total_applied || 0)}</td>
                  <td style={{ padding: "7px 10px", fontWeight: 600, color: delta !== 0 ? "#ef4444" : "#10b981" }}>
                    {delta !== 0 ? `(${fmt(Math.abs(delta))})` : "-"}
                  </td>
                  <td style={{ padding: "7px 10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <div style={{ flex: 1, background: "#e2e8f0", borderRadius: 4, height: 6, minWidth: 40 }}>
                        <div style={{ width: `${confPct}%`, background: confColor, borderRadius: 4, height: 6 }} />
                      </div>
                      <span style={{ fontSize: 10, color: confColor, fontWeight: 600 }}>{confPct.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td style={{ padding: "7px 10px" }}>
                    <span style={{ background: statusColor + "18", color: statusColor, borderRadius: 4, padding: "2px 7px", fontSize: 10, fontWeight: 700, whiteSpace: "nowrap" }}>{status}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ExceptionAnalysis({ data }) {
  const exceptions = data?.exception_analysis || data?.exceptions || [];
  if (!exceptions.length) return null;

  const [expanded, setExpanded] = useState(null);

  const RISK_COLOR = { CRITICAL: "#dc2626", HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#3b82f6" };
  const GROUP_COLOR = { AMOUNT: "#10b981", IDENTITY: "#7c3aed", ENTITY: "#db2777", TIMING: "#b45309", REMITTANCE: "#8b5cf6", FX: "#0ea5e9", COMPLIANCE: "#dc2626" };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {exceptions.map((ex, i) => {
        const isOpen = expanded === i;
        const risk = ex.risk_tier || ex.severity || "MEDIUM";
        const sev = risk;
        const sevColor = RISK_COLOR[sev] || "#f59e0b";
        return (
          <div key={i} style={{ border: `1px solid ${sevColor}33`, borderRadius: 10, overflow: "hidden" }}>
            <button
              onClick={() => setExpanded(isOpen ? null : i)}
              style={{
                width: "100%", display: "flex", alignItems: "center", gap: 10,
                padding: "12px 14px", background: isOpen ? sevColor + "0a" : "#fff",
                border: "none", cursor: "pointer", textAlign: "left",
              }}
            >
              <span style={{ background: sevColor + "20", color: sevColor, borderRadius: 4, padding: "2px 8px", fontSize: 10, fontWeight: 700, minWidth: 70, textAlign: "center" }}>{sev}</span>
              {ex.exception_category_group && <span style={{ background: (GROUP_COLOR[ex.exception_category_group] || "#64748b") + "15", color: GROUP_COLOR[ex.exception_category_group] || "#64748b", borderRadius: 4, padding: "2px 6px", fontSize: 9, fontWeight: 700 }}>{ex.exception_category_group}</span>}
              <span style={{ fontFamily: "monospace", color: "#3b82f6", fontWeight: 600, fontSize: 12 }}>{ex.txn_id}</span>
              <span style={{ flex: 1, color: "#1e293b", fontWeight: 500, fontSize: 13 }}>{ex.exception_type || ex.type || ex.description}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: "#1e293b" }}>{ex.payment_amount ? fmt(ex.payment_amount) : ""}</span>
              <span style={{ color: "#94a3b8", fontSize: 14 }}>{isOpen ? "▲" : "▼"}</span>
            </button>
            {isOpen && (
              <div style={{ padding: "14px 16px", background: "#fafafa", borderTop: `1px solid ${sevColor}20` }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 10, color: "#94a3b8", fontWeight: 600, marginBottom: 4 }}>AI REASONING</div>
                    <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.6 }}>{ex.reasoning || ex.ai_reasoning || "-"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: "#94a3b8", fontWeight: 600, marginBottom: 4 }}>RECOMMENDED ACTION</div>
                    <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.6 }}>{ex.recommended_action || ex.action || "-"}</div>
                    {(ex.gl_code || ex.suggested_gl_code) && (
                      <div style={{ marginTop: 8, background: "#f1f5f9", borderRadius: 6, padding: "6px 10px", fontSize: 11, fontFamily: "monospace", color: "#64748b" }}>
                        GL: {ex.gl_code || ex.suggested_gl_code} - {ex.gl_description || ex.gl_desc || ""}
                      </div>
                    )}
                    <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {(ex.escalation_contact || ex.notify_team) && (
                        <span style={{ background: "#fef3c7", color: "#92400e", borderRadius: 4, padding: "2px 7px", fontSize: 10, fontWeight: 600 }}>
                          → {ex.escalation_contact || ex.notify_team}
                        </span>
                      )}
                      {ex.sla_hours && (
                        <span style={{ background: sevColor + "15", color: sevColor, borderRadius: 4, padding: "2px 7px", fontSize: 10, fontWeight: 600 }}>
                          SLA: {ex.sla_hours}h
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                {ex.deduction_amount && (
                  <div style={{ background: sevColor + "08", border: `1px solid ${sevColor}20`, borderRadius: 6, padding: "8px 12px", fontSize: 11, color: "#475569" }}>
                    Deduction Amount: <strong>{fmt(ex.deduction_amount)}</strong>
                    {ex.deduction_reason && ` - ${ex.deduction_reason}`}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function WorkQueue({ data, wqStatus, onStatusChange }) {
  const items = data?.workqueue_items || data?.work_queue || [];
  if (!items.length) return null;

  const TEAM_COLOR = {
    AR_ANALYST: "#3b82f6", DEDUCTIONS_TEAM: "#f59e0b", CREDIT_MANAGER: "#8b5cf6",
    COMPLIANCE_OFFICER: "#dc2626", TREASURY: "#0891b2", LEGAL: "#7c3aed",
    "AR Team": "#3b82f6", "Deductions Team": "#f59e0b", "Credit Team": "#8b5cf6",
  };

  const approved = items.filter((it) => wqStatus?.[it.txn_id] === "approved").length;
  const rejected = items.filter((it) => wqStatus?.[it.txn_id] === "rejected").length;
  const pending  = items.length - approved - rejected;

  const criticalItems = items.filter((it) => (it.risk_tier === "CRITICAL" || it.priority === 1));
  const otherItems = items.filter((it) => it.risk_tier !== "CRITICAL" && it.priority !== 1);

  return (
    <div>
      {/* Action summary bar */}
      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
        <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>Workqueue Actions:</div>
        <span style={{ background: "#f0fdf4", color: "#15803d", borderRadius: 6, padding: "3px 10px", fontSize: 11, fontWeight: 700 }}>✓ {approved} Approved</span>
        <span style={{ background: "#fef2f2", color: "#dc2626", borderRadius: 6, padding: "3px 10px", fontSize: 11, fontWeight: 700 }}>✗ {rejected} Rejected</span>
        <span style={{ background: "#f1f5f9", color: "#64748b", borderRadius: 6, padding: "3px 10px", fontSize: 11, fontWeight: 700 }}>⏳ {pending} Pending</span>
      </div>

      {criticalItems.length > 0 && (
        <div style={{ background: "#fef2f2", border: "1.5px solid #fca5a5", borderRadius: 10, padding: "10px 14px", marginBottom: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#dc2626", marginBottom: 8 }}>🔴 CRITICAL - Same-Day Escalation Required</div>
          {criticalItems.map((item, i) => (
            <WQItem key={i} item={item} TEAM_COLOR={TEAM_COLOR} status={wqStatus?.[item.txn_id]} onApprove={() => onStatusChange(item.txn_id, "approved")} onReject={() => onStatusChange(item.txn_id, "rejected")} />
          ))}
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {otherItems.map((item, i) => (
          <WQItem key={i} item={item} TEAM_COLOR={TEAM_COLOR} status={wqStatus?.[item.txn_id]} onApprove={() => onStatusChange(item.txn_id, "approved")} onReject={() => onStatusChange(item.txn_id, "rejected")} />
        ))}
      </div>
    </div>
  );
}

function WQItem({ item, TEAM_COLOR, status, onApprove, onReject }) {
  const team = item.team || item.assigned_team || "AR_ANALYST";
  const teamColor = TEAM_COLOR[team] || "#64748b";
  const risk = item.risk_tier || "MEDIUM";
  const priNum = item.priority;
  const priColor = risk === "CRITICAL" || priNum === 1 ? "#dc2626" : risk === "HIGH" || priNum === 2 ? "#ef4444" : risk === "MEDIUM" || priNum === 3 ? "#f59e0b" : "#3b82f6";
  const dueLabel = item.due_by || (priNum === 1 ? "Same Day" : priNum === 2 ? "24 Hours" : priNum === 3 ? "3 Days" : "5 Days");

  const isApproved = status === "approved";
  const isRejected = status === "rejected";
  const bgColor = isApproved ? "#f0fdf4" : isRejected ? "#fef2f2" : "#fff";
  const borderColor = isApproved ? "#bbf7d0" : isRejected ? "#fecaca" : `${priColor}22`;

  return (
    <div style={{ background: bgColor, border: `1px solid ${borderColor}`, borderRadius: 10, padding: "12px 14px", display: "flex", alignItems: "flex-start", gap: 12, transition: "all 0.2s" }}>
      <div style={{ background: priColor + "15", color: priColor, borderRadius: 6, padding: "4px 8px", fontSize: 10, fontWeight: 700, whiteSpace: "nowrap", minWidth: 28, textAlign: "center" }}>
        {risk || `P${priNum}`}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 13, color: "#1e293b", textDecoration: isRejected ? "line-through" : "none", opacity: isRejected ? 0.6 : 1 }}>
          {item.description || item.action_required || item.task}
        </div>
        <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
          {item.txn_id && <span style={{ fontFamily: "monospace", color: "#3b82f6" }}>{item.txn_id} · </span>}
          {item.erp_action || item.action || ""}
        </div>
        {item.escalation_note && (
          <div style={{ fontSize: 10, color: "#92400e", background: "#fef3c7", borderRadius: 4, padding: "2px 6px", marginTop: 4, display: "inline-block" }}>
            ⚠ {item.escalation_note}
          </div>
        )}
        {/* Action buttons */}
        {!isApproved && !isRejected && (
          <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
            <button
              onClick={onApprove}
              style={{ background: "#16a34a", color: "#fff", border: "none", borderRadius: 6, padding: "4px 12px", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
            >
              ✓ Approve
            </button>
            <button
              onClick={onReject}
              style={{ background: "#fff", color: "#dc2626", border: "1px solid #fca5a5", borderRadius: 6, padding: "4px 12px", fontSize: 11, fontWeight: 700, cursor: "pointer" }}
            >
              ✗ Reject
            </button>
          </div>
        )}
        {isApproved && (
          <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ background: "#dcfce7", color: "#15803d", borderRadius: 6, padding: "3px 10px", fontSize: 11, fontWeight: 700 }}>✓ Approved</span>
            <button onClick={() => onReject()} style={{ fontSize: 10, color: "#94a3b8", background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>undo</button>
          </div>
        )}
        {isRejected && (
          <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ background: "#fee2e2", color: "#dc2626", borderRadius: 6, padding: "3px 10px", fontSize: 11, fontWeight: 700 }}>✗ Rejected</span>
            <button onClick={() => onApprove()} style={{ fontSize: 10, color: "#94a3b8", background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>undo</button>
          </div>
        )}
      </div>
      <div style={{ textAlign: "right", minWidth: 90 }}>
        {item.amount && <div style={{ fontWeight: 600, fontSize: 13, color: "#1e293b" }}>{fmt(item.amount)}</div>}
        <div style={{ background: teamColor + "15", color: teamColor, borderRadius: 4, padding: "2px 6px", fontSize: 10, fontWeight: 600, marginTop: 2 }}>{team}</div>
        <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 2 }}>⏱ {dueLabel}</div>
      </div>
    </div>
  );
}

const ACTION_COLOR = {
  POST_FULL: "#10b981", POST_PARTIAL: "#06b6d4", POST_WITH_WRITEOFF: "#64748b",
  HOLD_UNAPPLIED: "#f59e0b", RETURN_TO_SENDER: "#ef4444", ENTITY_TRANSFER: "#ef4444",
  REVERSE_DUPLICATE: "#ef4444", DEDUCTION_WORKITEM: "#f97316",
  HOLD_EDI_PENDING: "#8b5cf6", HOLD_CHECK_DATE: "#b45309",
  RETURN_STALE_CHECK: "#dc2626", FREEZE_PENDING_COMPLIANCE: "#dc2626",
  HOLD_LEGAL_REVIEW: "#b91c1c", SUSPENSE_PREPAYMENT: "#0284c7",
  INTERCO_JOURNAL: "#0891b2", POST_FACTORING: "#db2777", POST_PARENT_SUBSIDIARY: "#db2777",
};

function PostingInstructions({ data }) {
  const instructions = data?.posting_instructions || [];
  if (!instructions.length) return null;

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ background: "#f1f5f9" }}>
            {["Txn ID", "Action", "Invoice(s)", "Debit", "Credit", "Amount", "Priority", "Notes"].map((h) => (
              <th key={h} style={{ padding: "8px 10px", textAlign: "left", fontWeight: 600, color: "#475569", borderBottom: "1px solid #e2e8f0", whiteSpace: "nowrap" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {instructions.map((p, i) => {
            // Extract from gl_entries
            const glEntries = p.gl_entries || [];
            const debitEntry = glEntries.find(e => e.debit > 0) || {};
            const creditEntry = glEntries.find(e => e.credit > 0) || {};
            const amount = glEntries.reduce((s, e) => s + (e.debit || 0), 0) ||
                           (p.invoice_applications || []).reduce((s, ia) => s + (ia.amount || 0), 0) ||
                           p.amount || 0;
            const invoiceIds = (p.invoice_applications || []).map(ia => ia.invoice_id);
            const action = p.action || "-";
            const actionColor = ACTION_COLOR[action] || "#64748b";
            const priColor = p.priority === "IMMEDIATE" ? "#dc2626" : p.priority === "TODAY" ? "#f59e0b" : "#64748b";
            return (
              <tr key={i} style={{ background: i % 2 === 0 ? "#fff" : "#f8fafc", borderBottom: "1px solid #f1f5f9" }}>
                <td style={{ padding: "7px 10px", fontFamily: "monospace", color: "#3b82f6", fontWeight: 600 }}>{p.txn_id}</td>
                <td style={{ padding: "7px 10px" }}>
                  <span style={{ background: actionColor + "18", color: actionColor, borderRadius: 4, padding: "2px 6px", fontSize: 9, fontWeight: 700, whiteSpace: "nowrap" }}>{action}</span>
                </td>
                <td style={{ padding: "7px 10px", color: "#475569", fontSize: 11, maxWidth: 140, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {invoiceIds.join(", ") || <span style={{ color: "#cbd5e1" }}>-</span>}
                </td>
                <td style={{ padding: "7px 10px", fontFamily: "monospace", fontSize: 10, color: "#1e293b" }}>{debitEntry.account || "-"}</td>
                <td style={{ padding: "7px 10px", fontFamily: "monospace", fontSize: 10, color: "#1e293b" }}>{creditEntry.account || "-"}</td>
                <td style={{ padding: "7px 10px", fontWeight: 600, color: "#1e293b" }}>{amount > 0 ? fmt(amount) : "-"}</td>
                <td style={{ padding: "7px 10px" }}>
                  <span style={{ color: priColor, fontWeight: 700, fontSize: 10 }}>{p.priority || "-"}</span>
                </td>
                <td style={{ padding: "7px 10px", color: "#64748b", fontSize: 11, maxWidth: 200, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{p.notes || p.erp_action || "-"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AgentOutputSection({ agentKey, agentResults, bankData }) {
  const meta = AGENT_META[agentKey];
  const result = agentResults[agentKey];
  if (!result) return null;

  return (
    <div
      style={{
        background: "#fff",
        border: `1px solid ${meta.color}33`,
        borderRadius: 12,
        overflow: "hidden",
        marginBottom: 20,
      }}
    >
      <div style={{ background: meta.color + "12", padding: "12px 18px", borderBottom: `1px solid ${meta.color}22`, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 20 }}>{meta.icon}</span>
        <div>
          <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 15 }}>{meta.label}</div>
          <div style={{ fontSize: 11, color: "#64748b" }}>{agentKey}</div>
        </div>
        <span style={{ marginLeft: "auto", background: meta.color, color: "#fff", borderRadius: 6, padding: "2px 10px", fontSize: 11, fontWeight: 700 }}>Complete</span>
      </div>
      <div style={{ padding: "16px 18px" }}>
        {agentKey === "BankStatementIntelligenceAgent" && (
          <BankStatementTable transactions={bankData?.transactions} />
        )}
        {agentKey === "ARLedgerAgent" && (
          <ARLedgerSummary data={result} />
        )}
        {agentKey === "ReconciliationAgent" && (
          <ReconciliationResults data={result} />
        )}
        {agentKey === "MismatchReasoningAgent" && (
          <ExceptionAnalysis data={result} />
        )}
        {agentKey === "CashPostingAgent" && (
          <>
            <WorkQueue data={result} wqStatus={wqStatus} onStatusChange={handleWqAction} />
            <div style={{ marginTop: 20 }}>
              <div style={{ fontWeight: 600, color: "#1e293b", marginBottom: 10, fontSize: 13 }}>GL Posting Journal</div>
              <PostingInstructions data={result} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ARLedgerSummary({ data }) {
  // data is ARLedgerAgent result: has ar_summary, customer_index, invoices
  const stats = data?.ar_summary || data?.ledger_summary || data?.summary || {};
  const customerIndex = data?.customer_index || {};
  const customers = Object.entries(customerIndex).map(([id, c]) => ({ id, ...c }));
  const aliasCount = Object.keys(data?.payer_alias_registry || {}).length;
  const legacyCount = Object.keys(data?.legacy_invoice_map || {}).length;

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 16 }}>
        {[
          { label: "Total Open AR", value: fmt(stats.total_open_amount || stats.total_open_ar || 0) },
          { label: "Open Invoices", value: stats.total_invoices || stats.total_open_invoices || "-" },
          { label: "Customers", value: customers.length || "-" },
          { label: "Disputed / Hold", value: (stats.disputed_count || 0) + (stats.legal_hold_count || 0) },
        ].map((s) => (
          <div key={s.label} style={{ background: "#f8fafc", borderRadius: 8, padding: 12, textAlign: "center" }}>
            <div style={{ fontWeight: 700, fontSize: 18, color: "#1e293b" }}>{s.value}</div>
            <div style={{ fontSize: 11, color: "#64748b" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {(aliasCount > 0 || legacyCount > 0) && (
        <div style={{ display: "flex", gap: 8, marginBottom: 14, flexWrap: "wrap" }}>
          {aliasCount > 0 && (
            <div style={{ background: "#f5f3ff", border: "1px solid #ddd6fe", borderRadius: 8, padding: "6px 12px", fontSize: 11 }}>
              <span style={{ color: "#7c3aed", fontWeight: 700 }}>🏷 {aliasCount} payer aliases</span>
              <span style={{ color: "#64748b" }}> - DBA, SWIFT truncation, M&A names</span>
            </div>
          )}
          {legacyCount > 0 && (
            <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, padding: "6px 12px", fontSize: 11 }}>
              <span style={{ color: "#3b82f6", fontWeight: 700 }}>🔗 {legacyCount} legacy invoice maps</span>
              <span style={{ color: "#64748b" }}> - old ERP cross-references</span>
            </div>
          )}
        </div>
      )}

      {customers.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#f1f5f9" }}>
              {["Customer", "Invoices", "Total Open", "Has Aliases", "Disputes"].map((h) => (
                <th key={h} style={{ padding: "7px 10px", textAlign: "left", fontWeight: 600, color: "#475569", borderBottom: "1px solid #e2e8f0" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {customers.slice(0, 12).map((c, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? "#fff" : "#f8fafc", borderBottom: "1px solid #f1f5f9" }}>
                <td style={{ padding: "7px 10px", fontWeight: 500, color: "#1e293b" }}>{c.name || c.customer_name}</td>
                <td style={{ padding: "7px 10px", color: "#475569" }}>{c.invoice_count || "-"}</td>
                <td style={{ padding: "7px 10px", fontWeight: 600, color: "#1e293b" }}>{fmt(c.total_open || 0)}</td>
                <td style={{ padding: "7px 10px" }}>
                  {(c.aliases?.length > 0) && <span style={{ background: "#f5f3ff", color: "#7c3aed", borderRadius: 4, padding: "1px 6px", fontSize: 10 }}>{c.aliases.length}</span>}
                </td>
                <td style={{ padding: "7px 10px" }}>
                  {c.has_disputes && <span style={{ background: "#fef2f2", color: "#dc2626", borderRadius: 4, padding: "1px 6px", fontSize: 10, fontWeight: 700 }}>⚠ Hold</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function CashAppSummaryBanner({ data }) {
  if (!data) return null;
  // data is the full CashPostingAgent result object
  const s = data.cash_application_summary || data;
  const totalReceived = s.total_received_usd || s.total_received || 0;
  const autoPct = s.auto_posted_pct || 0;
  const heldUsd = (s.held_unapplied_usd || 0) + (s.compliance_holds_usd || s.held_compliance_usd || 0);
  const exceptions = s.exceptions_requiring_action || s.exception_count || 0;
  const wqCount = (data.workqueue_items || []).length || s.workqueue_count || 0;
  const critEsc = s.critical_escalations || s.compliance_escalations || 0;

  return (
    <div style={{ background: "linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%)", borderRadius: 14, padding: "24px 28px", color: "#fff", marginBottom: 24 }}>
      <div style={{ fontSize: 12, color: "#94a3b8", letterSpacing: 1, marginBottom: 6, textTransform: "uppercase" }}>Cash Application Complete</div>
      <div style={{ fontSize: 26, fontWeight: 800, marginBottom: 16 }}>
        {fmt(totalReceived)} Processed · {autoPct}% Auto-Posted
      </div>
      {critEsc > 0 && (
        <div style={{ background: "#dc2626", borderRadius: 8, padding: "8px 14px", marginBottom: 14, fontSize: 12, fontWeight: 700 }}>
          🔴 {critEsc} CRITICAL compliance escalation{critEsc > 1 ? "s" : ""} - same-day action required
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 }}>
        {[
          { label: "Auto-Posted", value: `${autoPct}%`, sub: fmt(s.auto_posted_usd || 0) },
          { label: "Held / Suspense", value: fmt(heldUsd), sub: `${exceptions} exception${exceptions !== 1 ? "s" : ""}` },
          { label: "Deductions", value: fmt(s.deductions_usd || 0), sub: fmt(s.writeoffs_usd || s.auto_writeoffs_usd || 0) + " write-offs" },
          { label: "Workqueue", value: wqCount, sub: `${critEsc} critical` },
        ].map((stat) => (
          <div key={stat.label} style={{ background: "rgba(255,255,255,0.08)", borderRadius: 8, padding: "10px 12px" }}>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{stat.value}</div>
            <div style={{ fontSize: 11, color: "#93c5fd", fontWeight: 600 }}>{stat.label}</div>
            <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>{stat.sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const [bankData, setBankData] = useState(null);
  const [arData, setArData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [agentStates, setAgentStates] = useState({});
  const [agentResults, setAgentResults] = useState({});
  const [logLines, setLogLines] = useState([]);
  const [finalResult, setFinalResult] = useState(null);
  const [activeTab, setActiveTab] = useState("pipeline");
  const [dataLoaded, setDataLoaded] = useState(false);
  const [wqStatus, setWqStatus] = useState({});
  const [selectedSample, setSelectedSample] = useState("01");
  const [sampleList, setSampleList] = useState([]);

  useEffect(() => {
    fetch("/api/samples").then(r => r.json()).then(d => setSampleList(d.samples || [])).catch(() => {});
  }, []);

  function handleWqAction(txn_id, action) {
    setWqStatus((prev) => ({ ...prev, [txn_id]: action }));
  }

  const addLog = (text, color) =>
    setLogLines((prev) => [...prev, { text: `${new Date().toLocaleTimeString()} - ${text}`, color }]);

  async function loadDemoData(sampleId) {
    const id = sampleId || selectedSample;
    const res = await fetch(`/api/demo-data?sample=${id}`);
    const d = await res.json();
    setBankData(d.bank_statement);
    setArData(d.open_ar);
    setDataLoaded(true);
    const meta = sampleList.find(s => s.sample_id === id);
    const label = meta ? meta.label : `Sample ${id}`;
    addLog(`Loaded: ${label} - ${d.bank_statement?.transactions?.length} transactions, ${d.open_ar?.invoices?.length} invoices`, "#4ade80");
  }

  async function runAnalysis() {
    if (!bankData || !arData) return;
    setLoading(true);
    setAgentStates({});
    setAgentResults({});
    setLogLines([]);
    setFinalResult(null);

    addLog("Starting Azure AI Foundry pipeline...", "#60a5fa");

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bank_data: bankData, ar_data: arData }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();

        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          const raw = part.slice(6).trim();
          if (raw === "[DONE]") {
            addLog("All agents complete", "#4ade80");
            setLoading(false);
            break;
          }
          try {
            const ev = JSON.parse(raw);
            handleEvent(ev);
          } catch (_) {}
        }
      }
    } catch (e) {
      addLog(`Error: ${e.message}`, "#ef4444");
    } finally {
      setLoading(false);
    }
  }

  function handleEvent(ev) {
    // Backend uses: ev.event (type), ev.agent, ev.token (content), ev.result
    const type = ev.type || ev.event;
    const agent = ev.agent;
    const content = ev.content || ev.token;
    const result = ev.result;

    if (type === "agent_start") {
      addLog(`${AGENT_META[agent]?.icon || "▶"} ${AGENT_META[agent]?.label || agent} starting...`, AGENT_META[agent]?.color);
      setAgentStates((prev) => ({ ...prev, [agent]: { status: "streaming", tokens: 0, partialText: "" } }));
    }

    if (type === "agent_token" || type === "token") {
      setAgentStates((prev) => {
        const cur = prev[agent] || { status: "streaming", tokens: 0, partialText: "" };
        const newText = (cur.partialText || "") + (content || "");
        return {
          ...prev,
          [agent]: {
            ...cur,
            tokens: cur.tokens + Math.ceil((content?.length || 0) / 4),
            partialText: newText.slice(-600),
          },
        };
      });
    }

    if (type === "agent_complete") {
      addLog(`✓ ${AGENT_META[agent]?.label || agent} complete`, "#4ade80");
      setAgentStates((prev) => ({
        ...prev,
        [agent]: { ...prev[agent], status: "done" },
      }));
      if (result) {
        setAgentResults((prev) => ({ ...prev, [agent]: result }));
        if (agent === "CashPostingAgent") {
          setFinalResult(result);
          setActiveTab("results");
        }
      }
    }

    if (type === "swarm_complete") {
      const allResults = ev.results || {};
      setAgentResults(allResults);
      if (allResults["CashPostingAgent"]) {
        setFinalResult(allResults["CashPostingAgent"]);
        setActiveTab("results");
      }
      addLog("Swarm complete - all agents finished", "#4ade80");
    }

    if (type === "log") {
      addLog(content, "#94a3b8");
    }

    if (type === "error") {
      addLog(`Error: ${content}`, "#ef4444");
    }
  }

  const totalTokens = Object.values(agentStates).reduce((s, a) => s + (a.tokens || 0), 0);

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      {/* Header */}
      <div style={{ background: "linear-gradient(135deg,#1e3a8a 0%,#3730a3 50%,#4f46e5 100%)", padding: "0 0 60px" }}>
        <div style={{ maxWidth: 1300, margin: "0 auto", padding: "0 24px" }}>
          {/* Nav */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "18px 0", borderBottom: "1px solid rgba(255,255,255,0.1)", marginBottom: 40 }}>
            <div style={{ width: 34, height: 34, background: "rgba(255,255,255,0.15)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>💸</div>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: 16 }}>Cash Application Foundry</div>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
              {["Azure AI Foundry", "Assistants API", "Code Interpreter"].map((tag) => (
                <span key={tag} style={{ background: "rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.9)", borderRadius: 6, padding: "3px 10px", fontSize: 11, fontWeight: 500 }}>{tag}</span>
              ))}
            </div>
          </div>

          {/* Hero */}
          <div style={{ textAlign: "center", color: "#fff" }}>
            <div style={{ fontSize: 11, letterSpacing: 2, color: "#93c5fd", textTransform: "uppercase", marginBottom: 10 }}>Azure AI Foundry · 5-Agent Cash Application Pipeline</div>
            <h1 style={{ fontSize: 42, fontWeight: 800, lineHeight: 1.15, marginBottom: 12 }}>
              Intelligent Cash Application
              <br />
              <span style={{ color: "#a5b4fc" }}>Powered by Azure AI Foundry</span>
            </h1>
            <p style={{ fontSize: 16, color: "#c7d2fe", maxWidth: 600, margin: "0 auto" }}>
              5 specialized AI agents reconcile bank payments to open invoices - handling every edge case from early-pay discounts to FX settlements to NSF returns.
            </p>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, marginTop: 24 }}>
              {/* Sample picker */}
              <div style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(255,255,255,0.1)", borderRadius: 10, padding: "8px 14px" }}>
                <span style={{ fontSize: 12, color: "#c7d2fe", fontWeight: 600, whiteSpace: "nowrap" }}>Dataset:</span>
                <select
                  value={selectedSample}
                  onChange={e => {
                    setSelectedSample(e.target.value);
                    if (dataLoaded) {
                      setAgentStates({}); setAgentResults({}); setLogLines([]); setFinalResult(null); setWqStatus({}); setActiveTab("pipeline");
                      loadDemoData(e.target.value);
                    }
                  }}
                  style={{ background: "rgba(255,255,255,0.95)", color: "#1e3a8a", border: "none", borderRadius: 6, padding: "6px 10px", fontWeight: 600, fontSize: 12, cursor: "pointer", maxWidth: 320 }}
                >
                  {sampleList.length > 0 ? sampleList.map(s => (
                    <option key={s.sample_id} value={s.sample_id}>
                      {s.sample_id}. {s.label} ({s.transactions} txns)
                    </option>
                  )) : (
                    <>
                      <option value="01">01. Clean Batch - Exact and Near-Exact Matches</option>
                      <option value="02">02. Deductions Heavy - Freight, Damage, Unauthorized</option>
                      <option value="03">03. Compliance and Legal Risk</option>
                      <option value="04">04. Multi-Entity - Parent/Subsidiary, Factoring</option>
                      <option value="05">05. International FX - EUR, GBP, CAD Payments</option>
                      <option value="06">06. Timing Issues - Post-Dated, Stale, NSF</option>
                      <option value="07">07. Remittance Problems - Missing, Vague, EDI</option>
                      <option value="08">08. Overpayments and Credit Memos</option>
                      <option value="09">09. Identity and Name Issues - SWIFT, DBA, Alias</option>
                      <option value="10">10. Enterprise Mixed Batch - All Exception Types</option>
                    </>
                  )}
                </select>
              </div>
              {/* Action buttons */}
              <div style={{ display: "flex", gap: 12 }}>
                {!dataLoaded ? (
                  <button onClick={() => loadDemoData()} style={{ background: "#fff", color: "#1e3a8a", border: "none", borderRadius: 8, padding: "11px 28px", fontWeight: 700, fontSize: 14, cursor: "pointer" }}>
                    Load Dataset
                  </button>
                ) : (
                  <button
                    onClick={runAnalysis}
                    disabled={loading}
                    style={{
                      background: loading ? "rgba(255,255,255,0.3)" : "#fff",
                      color: loading ? "#fff" : "#1e3a8a",
                      border: "none", borderRadius: 8, padding: "11px 28px",
                      fontWeight: 700, fontSize: 14, cursor: loading ? "not-allowed" : "pointer",
                    }}
                  >
                    {loading ? "⏳ Agents Running..." : "▶ Run Cash Application"}
                  </button>
                )}
                {dataLoaded && !loading && (
                  <button
                    onClick={() => { setAgentStates({}); setAgentResults({}); setLogLines([]); setFinalResult(null); setWqStatus({}); setActiveTab("pipeline"); setDataLoaded(false); }}
                    style={{ background: "transparent", color: "#c7d2fe", border: "1px solid rgba(255,255,255,0.3)", borderRadius: 8, padding: "11px 20px", fontWeight: 600, fontSize: 14, cursor: "pointer" }}
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ maxWidth: 1300, margin: "-30px auto 40px", padding: "0 24px" }}>
        {!dataLoaded ? (
          <HowItWorks />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 20, alignItems: "start" }}>
            {/* Left: pipeline */}
            <div>
              <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 14, marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  Agent Pipeline
                  {totalTokens > 0 && (
                    <span style={{ fontSize: 11, background: "#eff6ff", color: "#3b82f6", borderRadius: 4, padding: "2px 8px", fontWeight: 600 }}>
                      ~{totalTokens.toLocaleString()} total tok
                    </span>
                  )}
                </div>
                <AgentPipeline agentStates={agentStates} />
                <LiveLog lines={logLines} />

                {/* Data loaded summary */}
                {dataLoaded && (
                  <div style={{ marginTop: 12, background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "10px 12px" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#15803d", marginBottom: 4 }}>✓ Data Ready</div>
                    <div style={{ fontSize: 11, color: "#475569" }}>{bankData?.transactions?.length} bank txns · {arData?.invoices?.length + (arData?.credit_memos?.length || 0)} AR records</div>
                    <div style={{ fontSize: 11, color: "#475569" }}>{bankData?.bank} · {bankData?.company}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Right: results */}
            <div>
              {/* Tab bar */}
              <div style={{ display: "flex", gap: 2, marginBottom: 16, background: "#fff", borderRadius: 10, padding: 4, border: "1px solid #e2e8f0", width: "fit-content" }}>
                {["pipeline", "bank", "results", "exceptions", "posting"].map((tab) => {
                  const labels = { pipeline: "Overview", bank: "Bank Statement", results: "Reconciliation", exceptions: "Exceptions", posting: "Cash Posting" };
                  const isActive = activeTab === tab;
                  return (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      style={{
                        padding: "7px 14px", borderRadius: 7, border: "none", cursor: "pointer", fontSize: 12, fontWeight: isActive ? 700 : 500,
                        background: isActive ? "#1e3a8a" : "transparent",
                        color: isActive ? "#fff" : "#64748b",
                        transition: "all 0.15s",
                      }}
                    >
                      {labels[tab]}
                    </button>
                  );
                })}
              </div>

              {/* Bank statement tab */}
              {activeTab === "bank" && (
                <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                  <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 15, marginBottom: 4 }}>Bank Statement - {bankData?.bank}</div>
                  <div style={{ fontSize: 12, color: "#64748b", marginBottom: 14 }}>{bankData?.company} · Account {bankData?.account} · {bankData?.statement_date}</div>
                  <BankStatementTable transactions={bankData?.transactions} />
                </div>
              )}

              {/* Pipeline / overview tab */}
              {activeTab === "pipeline" && (
                <div>
                  {finalResult && <CashAppSummaryBanner data={finalResult} />}
                  {AGENT_ORDER.filter((k) => agentResults[k]).map((k) => (
                    <AgentOutputSection key={k} agentKey={k} agentResults={agentResults} bankData={bankData} />
                  ))}
                  {!finalResult && !loading && Object.keys(agentResults).length === 0 && (
                    <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "40px", textAlign: "center", color: "#94a3b8" }}>
                      <div style={{ fontSize: 40, marginBottom: 12 }}>⚖️</div>
                      <div style={{ fontWeight: 600, color: "#64748b" }}>Ready to run cash application</div>
                      <div style={{ fontSize: 13, marginTop: 6 }}>Click "Run Cash Application" to start the 5-agent reconciliation</div>
                    </div>
                  )}
                </div>
              )}

              {/* Reconciliation tab */}
              {activeTab === "results" && (
                <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                  <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 15, marginBottom: 14 }}>Reconciliation Results</div>
                  {agentResults["ReconciliationAgent"] ? (
                    <ReconciliationResults data={agentResults["ReconciliationAgent"]} />
                  ) : (
                    <div style={{ color: "#94a3b8", textAlign: "center", padding: 40 }}>Run analysis to see reconciliation results</div>
                  )}
                </div>
              )}

              {/* Exceptions tab */}
              {activeTab === "exceptions" && (
                <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                  <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 15, marginBottom: 14 }}>Exception Analysis</div>
                  {agentResults["MismatchReasoningAgent"] ? (
                    <ExceptionAnalysis data={agentResults["MismatchReasoningAgent"]} />
                  ) : (
                    <div style={{ color: "#94a3b8", textAlign: "center", padding: 40 }}>Run analysis to see exception reasoning</div>
                  )}
                </div>
              )}

              {/* Cash posting tab */}
              {activeTab === "posting" && (
                <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                  <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 15, marginBottom: 14 }}>Cash Posting & Workqueue</div>
                  {agentResults["CashPostingAgent"] ? (
                    <>
                      {finalResult && <CashAppSummaryBanner data={finalResult} />}
                      <div style={{ fontWeight: 600, color: "#1e293b", fontSize: 13, marginBottom: 10 }}>Workqueue Items</div>
                      <WorkQueue data={agentResults["CashPostingAgent"]} wqStatus={wqStatus} onStatusChange={handleWqAction} />
                      <div style={{ fontWeight: 600, color: "#1e293b", fontSize: 13, marginTop: 20, marginBottom: 10 }}>GL Journal Entries</div>
                      <PostingInstructions data={agentResults["CashPostingAgent"]} />
                    </>
                  ) : (
                    <div style={{ color: "#94a3b8", textAlign: "center", padding: 40 }}>Run analysis to see posting instructions</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        button:hover { opacity: 0.9; }
      `}</style>
    </div>
  );
}

function HowItWorks() {
  const [expandedAgent, setExpandedAgent] = useState(null);
  const [expandedTech, setExpandedTech] = useState(null);

  const agentDetails = [
    {
      key: "BankStatementIntelligenceAgent",
      input: "Raw bank statement JSON (35 transactions, payer names, remittance text)",
      output: "Structured payment records with normalized customer names, detected edge case flags",
      why: "Isolates the noisy normalization work - fuzzy matching payer strings, detecting NSF returns, parsing remittance hints - before any invoice matching begins.",
    },
    {
      key: "ARLedgerAgent",
      input: "Open AR JSON (38 invoices, credit memos, partial balances, installment plans)",
      output: "Customer index keyed by normalized name, invoice lookup map, credit memo register",
      why: "Builds the lookup structures needed by ReconciliationAgent. Separating this allows the reconciliation step to run pure matching logic without re-reading raw data.",
    },
    {
      key: "ReconciliationAgent",
      input: "Normalized payments + AR customer index",
      output: "Match tier, confidence score, and matched invoice IDs for every transaction",
      why: "Uses the Assistants API with Code Interpreter to write and execute real Python for exact amount arithmetic - verifying multi-invoice sums, discount calculations, FX conversions.",
    },
    {
      key: "MismatchReasoningAgent",
      input: "All 24 exception transactions with match context",
      output: "AI reasoning text, GL code, severity level, deduction type, and recommended action per exception",
      why: "Focused purely on the hard cases - short pays, damage claims, unauthorized deductions - where LLM reasoning about business rules and contract terms adds the most value.",
    },
    {
      key: "CashPostingAgent",
      input: "Full reconciliation results + exception reasoning",
      output: "GL journal entries, workqueue items by team (AR/Deductions/Credit), cash application summary",
      why: "Final agent converts analysis into ERP-ready posting instructions and creates actionable workqueue items, separating the 'think' phase from the 'act' phase.",
    },
  ];

  const techStack = [
    {
      name: "Azure AI Foundry",
      icon: "🤖",
      desc: "Native managed agent runtime. Each agent is a first-class Azure resource with its own thread context, tools, and lifecycle. No framework wrappers - direct SDK calls to `AIProjectClient`.",
    },
    {
      name: "Code Interpreter (Assistants API)",
      icon: "🐍",
      desc: "Built-in AI Foundry tool that lets ReconciliationAgent write Python and execute it in a sandboxed environment. Used for exact arithmetic: multi-invoice sum verification, 2% discount calculations, FX rate conversions.",
    },
    {
      name: "Shared Thread Architecture",
      icon: "🧵",
      desc: "All 5 agents share a single Azure Thread. Each agent appends its structured JSON output as an assistant message. The next agent reads the full thread history - no custom message passing needed.",
    },
    {
      name: "ConnectedAgentTool",
      icon: "🔗",
      desc: "AI Foundry native tool that lets one agent call another as a sub-agent. ReconciliationAgent can delegate FX calculations or installment math to a specialized sub-agent without leaving the thread.",
    },
    {
      name: "SSE Token Streaming",
      icon: "⚡",
      desc: "FastAPI `StreamingResponse` with `create_stream()` from the AI Foundry SDK. Every token the agent generates fires a `MessageDeltaChunk` event, sent immediately to the UI via server-sent events.",
    },
  ];

  return (
    <div style={{ marginTop: 20 }}>
      {/* Agent flow */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "24px 28px", marginBottom: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 17, marginBottom: 6 }}>How the 5-Agent Swarm Works</div>
        <div style={{ fontSize: 13, color: "#64748b", marginBottom: 20 }}>Each agent is a focused specialist. Click any agent to see its role in detail.</div>

        <div style={{ display: "flex", alignItems: "stretch", gap: 0, overflowX: "auto", paddingBottom: 8 }}>
          {agentDetails.map((a, i) => {
            const meta = AGENT_META[a.key];
            const isOpen = expandedAgent === i;
            return (
              <div key={a.key} style={{ display: "flex", alignItems: "center" }}>
                <button
                  onClick={() => setExpandedAgent(isOpen ? null : i)}
                  style={{
                    border: `2px solid ${isOpen ? meta.color : "#e2e8f0"}`,
                    borderRadius: 10, padding: "12px 14px", minWidth: 130,
                    background: isOpen ? meta.color + "12" : "#fff",
                    cursor: "pointer", textAlign: "center",
                    transition: "all 0.2s",
                  }}
                >
                  <div style={{ fontSize: 22, marginBottom: 4 }}>{meta.icon}</div>
                  <div style={{ fontWeight: 600, fontSize: 11, color: "#1e293b", lineHeight: 1.3 }}>{meta.label}</div>
                  <div style={{ fontSize: 9, color: "#94a3b8", marginTop: 2 }}>Agent {i + 1}</div>
                </button>
                {i < agentDetails.length - 1 && (
                  <div style={{ color: "#cbd5e1", fontSize: 18, padding: "0 6px", fontWeight: 300 }}>→</div>
                )}
              </div>
            );
          })}
        </div>

        {expandedAgent !== null && (
          <div
            style={{
              marginTop: 16, background: "#f8fafc", borderRadius: 10, padding: "16px 18px",
              border: `1px solid ${AGENT_META[agentDetails[expandedAgent].key].color}33`,
            }}
          >
            {(() => {
              const a = agentDetails[expandedAgent];
              const meta = AGENT_META[a.key];
              return (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 10, color: "#94a3b8", fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>INPUT</div>
                    <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.6 }}>{a.input}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: "#94a3b8", fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>OUTPUT (JSON)</div>
                    <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.6 }}>{a.output}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: meta.color, fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>WHY SEPARATE?</div>
                    <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.6 }}>{a.why}</div>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* Shared thread explanation */}
        <div style={{ marginTop: 16, background: "#eff6ff", borderRadius: 10, padding: "14px 16px", border: "1px solid #bfdbfe" }}>
          <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
            <span style={{ fontSize: 16 }}>🧵</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 12, color: "#1e40af", marginBottom: 4 }}>Shared Azure Thread - How Agents Communicate</div>
              <div style={{ fontSize: 12, color: "#1e3a8a", lineHeight: 1.6 }}>
                All 5 agents share one Azure AI Foundry <strong>Thread</strong>. Each agent appends its complete JSON output as an assistant message. When the next agent runs, it reads the entire thread history - so Agent 3 can see Agent 1 and 2's exact outputs without any custom message passing. After Agent 2, the original raw data is replaced with a compact summary to stay within context limits.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 7 Edge Case Categories */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "24px 28px", marginBottom: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 17, marginBottom: 6 }}>35 Edge Cases - 7 Categories</div>
        <div style={{ fontSize: 13, color: "#64748b", marginBottom: 16 }}>Every edge case that occurs in real-world AR cash application, now handled by the AI agent swarm.</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
          {[
            { key: "AMOUNT", cases: ["Exact match", "Multi-invoice", "Early-pay discount", "Unauthorized short pay", "Freight deduction", "Damage claim", "Overpayment", "Credit memo net", "Wire fee auto write-off", "Late discount taken"] },
            { key: "IDENTITY", cases: ["SWIFT 35-char name truncation", "DBA (doing business as) name", "Post-acquisition name change", "Fuzzy name alias matching"] },
            { key: "ENTITY", cases: ["Parent entity pays for subsidiary", "Third-party factoring agent", "Intercompany netting (bilateral AP/AR)", "Wrong legal entity redirect"] },
            { key: "TIMING", cases: ["Duplicate payment detection", "Installment / partial payment", "NSF return & reversal", "Post-dated check hold", "Stale check return (>180 days)", "Prepayment / advance deposit"] },
            { key: "REMITTANCE", cases: ["No remittance → FIFO match", "Vague remittance → amount matching", "PO number reference", "Legacy ERP invoice number", "EDI 820 remittance pending (hold)"] },
            { key: "FX", cases: ["Foreign currency (EUR/SWIFT) payment", "FX rate verification via Code Interpreter"] },
            { key: "COMPLIANCE", cases: ["OFAC/sanctions screening hold", "Disputed invoice payment block", "Legal hold escalation"] },
          ].map(({ key, cases }) => {
            const meta = CATEGORY_META[key];
            return (
              <div key={key} style={{ border: `1px solid ${meta.color}22`, borderRadius: 10, padding: "12px 14px", background: meta.color + "05" }}>
                <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 16 }}>{meta.icon}</span>
                  <div style={{ fontWeight: 700, fontSize: 12, color: meta.color }}>{meta.label}</div>
                  <span style={{ marginLeft: "auto", background: meta.color + "20", color: meta.color, borderRadius: 4, padding: "1px 6px", fontSize: 10, fontWeight: 700 }}>{cases.length}</span>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {cases.map((c) => (
                    <span key={c} style={{ background: "#f1f5f9", color: "#475569", borderRadius: 4, padding: "2px 6px", fontSize: 10 }}>{c}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tech stack */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "24px 28px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <div style={{ fontWeight: 700, color: "#1e293b", fontSize: 17, marginBottom: 16 }}>Microsoft Azure Tech Stack</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {techStack.map((t, i) => {
            const isOpen = expandedTech === i;
            return (
              <div key={t.name} style={{ border: "1px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
                <button
                  onClick={() => setExpandedTech(isOpen ? null : i)}
                  style={{
                    width: "100%", display: "flex", alignItems: "center", gap: 10,
                    padding: "12px 14px", background: isOpen ? "#f8fafc" : "#fff",
                    border: "none", cursor: "pointer", textAlign: "left",
                  }}
                >
                  <span style={{ fontSize: 18 }}>{t.icon}</span>
                  <span style={{ fontWeight: 600, fontSize: 13, color: "#1e293b", flex: 1 }}>{t.name}</span>
                  <span style={{ color: "#94a3b8" }}>{isOpen ? "▲" : "▼"}</span>
                </button>
                {isOpen && (
                  <div style={{ padding: "10px 16px 14px 46px", background: "#f8fafc", borderTop: "1px solid #f1f5f9" }}>
                    <div style={{ fontSize: 13, color: "#374151", lineHeight: 1.7 }}>{t.desc}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
