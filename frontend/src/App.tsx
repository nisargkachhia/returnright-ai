import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { mcpClient } from './mcp/client'
import { clearWorkflow, loadWorkflow, saveWorkflow } from './workflow/persistence'
import { initialWorkflowState } from './workflow/types'
import type {
  CaseDetail,
  OrderDetail,
  OrderSummary,
  PolicyResult,
  PrepareResult,
  WorkflowState,
} from './workflow/types'
import './App.css'

const DEMO_USER = 'demo-user-1'
const STEPS = ['connect', 'search', 'select', 'evaluate', 'case', 'prepare', 'confirm', 'done'] as const

function money(cents: number, currency: string): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(cents / 100)
}

export default function App() {
  const [state, setState] = useState<WorkflowState>(() => loadWorkflow())
  const [busy, setBusy] = useState(false)
  const demoMode = (import.meta.env.VITE_DEMO_MODE ?? 'true') === 'true'

  useEffect(() => {
    saveWorkflow(state)
  }, [state])

  const stepIndex = STEPS.indexOf(state.step)

  const logTool = (tool: string, ok: boolean, summary: string) => {
    setState((s) => ({
      ...s,
      toolLog: [{ tool, at: new Date().toISOString(), ok, summary }, ...s.toolLog].slice(0, 40),
    }))
  }

  const run = async (fn: () => Promise<void>) => {
    setBusy(true)
    setState((s) => ({ ...s, error: null }))
    try {
      await fn()
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setState((s) => ({ ...s, error: message }))
    } finally {
      setBusy(false)
    }
  }

  const connect = () =>
    run(async () => {
      const info = await mcpClient.connect()
      const tools = await mcpClient.listTools()
      logTool('initialize+tools/list', true, `${tools.length} tools · ${info.protocolVersion ?? 'n/a'}`)
      setState((s) => ({
        ...s,
        step: s.caseDetail ? 'case' : 'search',
        protocolVersion: info.protocolVersion ?? null,
      }))
    })

  const search = (e: FormEvent) => {
    e.preventDefault()
    run(async () => {
      const result = await mcpClient.callTool<{
        results: OrderSummary[]
        error?: string
      }>('search_orders', { query: state.query, user_id: DEMO_USER })
      if (result.error) throw new Error(result.error)
      logTool('search_orders', true, `${result.results.length} matches`)
      setState((s) => ({ ...s, orders: result.results, step: 'select' }))
    })
  }

  const selectOrder = (orderId: string) =>
    run(async () => {
      const order = await mcpClient.callTool<OrderDetail & { error?: string }>('get_order', {
        order_id: orderId,
        user_id: DEMO_USER,
      })
      if (order.error) throw new Error(order.error)
      logTool('get_order', true, order.order_number)
      setState((s) => ({
        ...s,
        selectedOrder: order,
        selectedItemId: order.items[0]?.id ?? null,
        step: 'evaluate',
      }))
    })

  const evaluate = (e: FormEvent) => {
    e.preventDefault()
    if (!state.selectedItemId) return
    run(async () => {
      const policy = await mcpClient.callTool<PolicyResult & { error?: string }>('evaluate_policy', {
        order_item_id: state.selectedItemId,
        issue_type: state.issueType,
        issue_description: state.issueDescription,
        user_id: DEMO_USER,
      })
      if (policy.error) throw new Error(policy.error)
      logTool('evaluate_policy', true, policy.outcome)
      setState((s) => ({ ...s, policy, step: 'case' }))
    })
  }

  const createCase = () =>
    run(async () => {
      if (!state.selectedOrder || !state.selectedItemId || !state.policy) return
      const created = await mcpClient.callTool<CaseDetail & { error?: string }>('create_case', {
        order_id: state.selectedOrder.id,
        order_item_id: state.selectedItemId,
        issue_type: state.issueType,
        issue_description: state.issueDescription || 'No description provided',
        eligibility_outcome: state.policy.outcome,
        policy_rule_id: state.policy.evidence[0]?.rule_id ?? '',
        user_id: DEMO_USER,
      })
      if (created.error) throw new Error(created.error)
      logTool('create_case', true, created.id)
      setState((s) => ({ ...s, caseDetail: created, step: 'prepare' }))
    })

  const prepare = () =>
    run(async () => {
      if (!state.caseDetail) return
      const actionType =
        state.issueType === 'defective' || state.issueType === 'malfunction'
          ? 'warranty_claim'
          : 'return_request'
      const prepared = await mcpClient.callTool<PrepareResult & { error?: string }>(
        'prepare_resolution_action',
        {
          case_id: state.caseDetail.id,
          action_type: actionType,
          user_id: DEMO_USER,
        },
      )
      if (prepared.error) throw new Error(prepared.error)
      logTool('prepare_resolution_action', true, prepared.action_id)
      setState((s) => ({ ...s, prepared, step: 'confirm' }))
    })

  const confirm = () =>
    run(async () => {
      if (!state.caseDetail || !state.prepared) return
      const result = await mcpClient.callTool<{
        submission_status?: string
        error?: string
        code?: string
      }>('confirm_resolution_action', {
        case_id: state.caseDetail.id,
        action_id: state.prepared.action_id,
        confirmation_token: state.prepared.confirmation_token,
        user_confirmed: true,
        user_id: DEMO_USER,
      })
      if (result.error) throw new Error(result.error)
      const refreshed = await mcpClient.callTool<CaseDetail>('get_case', {
        case_id: state.caseDetail.id,
        user_id: DEMO_USER,
      })
      logTool('confirm_resolution_action', true, result.submission_status ?? 'demo_only')
      setState((s) => ({ ...s, caseDetail: refreshed, step: 'done' }))
    })

  const simulateFailure = () =>
    run(async () => {
      if (!state.caseDetail) return
      const before = state.caseDetail.status
      const result = await mcpClient.callTool<{
        case_status: string
        message: string
        error?: string
      }>('simulate_failure', { case_id: state.caseDetail.id, user_id: DEMO_USER })
      if (result.error) throw new Error(result.error)
      const refreshed = await mcpClient.callTool<CaseDetail>('get_case', {
        case_id: state.caseDetail.id,
        user_id: DEMO_USER,
      })
      logTool('simulate_failure', true, `status still ${result.case_status} (was ${before})`)
      setState((s) => ({ ...s, caseDetail: refreshed }))
    })

  const reset = () => {
    clearWorkflow()
    setState(initialWorkflowState())
  }

  const outcomeClass = useMemo(() => {
    const o = state.policy?.outcome
    if (!o) return ''
    if (o === 'ELIGIBLE' || o === 'return_eligible' || o === 'warranty_guidance') return 'ok'
    if (o === 'NEEDS_INFORMATION' || o === 'NEEDS_REVIEW' || o === 'insufficient_information') return 'warn'
    return 'bad'
  }, [state.policy])

  return (
    <div className="app">
      {demoMode && (
        <div className="demo-banner" role="status">
          DEMO MODE — synthetic purchases and policies only. No Alexa+ private tools. No real retailer
          submissions.
        </div>
      )}

      <header className="hero">
        <p className="eyebrow">Amazon Developer Hackathon 2026 · Alexa+ track</p>
        <h1>ReturnRight AI</h1>
        <p className="lede">
          Resolve returns and warranties with documented policies, explicit confirmation, and a real MCP
          client workflow.
        </p>
      </header>

      <ol className="steps" aria-label="Workflow steps">
        {STEPS.map((step, idx) => (
          <li key={step} className={idx <= stepIndex ? 'active' : ''}>
            {step}
          </li>
        ))}
      </ol>

      {state.error && <div className="error">{state.error}</div>}

      <main className="grid">
        <section className="panel">
          <h2>Agentic workflow</h2>
          {state.step === 'connect' && (
            <div className="stack">
              <p>Connect to the self-hosted MCP Streamable HTTP server to begin.</p>
              <button disabled={busy} onClick={connect}>
                Connect MCP
              </button>
            </div>
          )}

          {state.step !== 'connect' && (
            <form className="stack" onSubmit={search}>
              <label>
                Search purchases
                <input
                  value={state.query}
                  onChange={(e) => setState((s) => ({ ...s, query: e.target.value }))}
                  placeholder="product, order ID, or merchant"
                />
              </label>
              <button disabled={busy} type="submit">
                search_orders
              </button>
            </form>
          )}

          {state.orders.length > 0 && (
            <ul className="order-list">
              {state.orders.map((o) => (
                <li key={o.id}>
                  <button className="order" type="button" disabled={busy} onClick={() => selectOrder(o.id)}>
                    <strong>{o.order_number}</strong>
                    <span>
                      {o.merchant_name} · {money(o.total_cents, o.currency)}
                    </span>
                    <em>{o.data_provenance}</em>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {state.selectedOrder && (
            <form className="stack" onSubmit={evaluate}>
              <h3>{state.selectedOrder.order_number}</h3>
              <label>
                Item
                <select
                  value={state.selectedItemId ?? ''}
                  onChange={(e) => setState((s) => ({ ...s, selectedItemId: e.target.value }))}
                >
                  {state.selectedOrder.items.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.product_name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Issue type
                <select
                  value={state.issueType}
                  onChange={(e) => setState((s) => ({ ...s, issueType: e.target.value }))}
                >
                  <option value="unwanted">unwanted</option>
                  <option value="change_of_mind">change_of_mind</option>
                  <option value="defective">defective</option>
                  <option value="malfunction">malfunction</option>
                </select>
              </label>
              <label>
                Description
                <textarea
                  value={state.issueDescription}
                  onChange={(e) => setState((s) => ({ ...s, issueDescription: e.target.value }))}
                  rows={3}
                  placeholder="Describe the issue (required for defects)"
                />
              </label>
              <button disabled={busy} type="submit">
                evaluate_policy
              </button>
            </form>
          )}

          {state.policy && (
            <div className={`outcome ${outcomeClass}`}>
              <h3>Outcome: {state.policy.outcome}</h3>
              <ul>
                {state.policy.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
              {state.policy.evidence.map((ev) => (
                <blockquote key={ev.rule_id}>
                  <strong>{ev.rule_code}</strong> · {ev.policy_title} v{ev.policy_version}
                  <p>{ev.excerpt}</p>
                </blockquote>
              ))}
              <p className="muted">{state.policy.disclaimer}</p>
              {!state.caseDetail && (
                <button disabled={busy} onClick={createCase}>
                  create_case
                </button>
              )}
            </div>
          )}

          {state.caseDetail && (
            <div className="stack">
              <h3>Case {state.caseDetail.id}</h3>
              <p>
                Status: <strong>{state.caseDetail.status}</strong>
              </p>
              {!state.prepared && state.step !== 'done' && (
                <button disabled={busy} onClick={prepare}>
                  prepare_resolution_action
                </button>
              )}
              {state.prepared && state.step === 'confirm' && (
                <div className="confirm-box">
                  <p>{state.prepared.draft_summary}</p>
                  <p className="warn-text">{state.prepared.warning}</p>
                  <button disabled={busy} onClick={confirm}>
                    I confirm — confirm_resolution_action
                  </button>
                </div>
              )}
              <button className="secondary" disabled={busy} onClick={simulateFailure}>
                simulate_failure
              </button>
            </div>
          )}

          <div className="footer-actions">
            <button className="secondary" type="button" onClick={reset}>
              Reset workflow
            </button>
            {state.protocolVersion && (
              <span className="muted">MCP protocol {state.protocolVersion}</span>
            )}
          </div>
        </section>

        <aside className="panel side">
          <h2>Persistent context</h2>
          <p className="muted">Case history and tool log survive refresh via sessionStorage + SQLite.</p>
          {state.caseDetail ? (
            <>
              <h3>Events</h3>
              <ul className="log">
                {state.caseDetail.events.map((e) => (
                  <li key={e.id}>
                    <strong>{e.event_type}</strong>
                    <span>{e.message}</span>
                  </li>
                ))}
              </ul>
              <h3>Follow-ups</h3>
              <ul className="log">
                {state.caseDetail.follow_ups.map((t) => (
                  <li key={t.id}>
                    <strong>{t.title}</strong>
                    <span>
                      due {new Date(t.due_at).toLocaleDateString()} · {t.status}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p>No case yet.</p>
          )}

          <h3>MCP tool log</h3>
          <ul className="log">
            {state.toolLog.map((entry, i) => (
              <li key={`${entry.at}-${i}`} className={entry.ok ? '' : 'bad'}>
                <strong>{entry.tool}</strong>
                <span>{entry.summary}</span>
              </li>
            ))}
          </ul>
        </aside>
      </main>
    </div>
  )
}
