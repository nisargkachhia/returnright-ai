export type WorkflowStep =
  | 'connect'
  | 'search'
  | 'select'
  | 'evaluate'
  | 'case'
  | 'prepare'
  | 'confirm'
  | 'done'

export interface OrderSummary {
  id: string
  order_number: string
  merchant_name: string
  purchased_at: string
  currency: string
  total_cents: number
  item_count: number
  data_provenance: string
}

export interface OrderItem {
  id: string
  product_name: string
  sku: string
  quantity: number
  unit_price_cents: number
  category: string
  condition_notes: string
}

export interface OrderDetail extends OrderSummary {
  items: OrderItem[]
}

export interface PolicyEvidence {
  policy_id: string
  policy_title: string
  policy_version: string
  rule_id: string
  rule_code: string
  excerpt: string
  data_provenance: string
}

export interface PolicyResult {
  outcome: string
  reasons: string[]
  evidence: PolicyEvidence[]
  days_since_purchase: number
  requires_more_information: boolean
  data_provenance: string
  disclaimer: string
}

export interface CaseDetail {
  id: string
  order_id: string
  order_item_id: string
  issue_type: string
  issue_description: string
  status: string
  eligibility_outcome: string | null
  policy_rule_id: string | null
  events: { id: string; event_type: string; message: string; created_at: string }[]
  follow_ups: { id: string; title: string; due_at: string; status: string }[]
  actions: {
    id: string
    action_type: string
    status: string
    submission_status: string
    confirmed_at: string | null
    created_at: string
  }[]
  data_provenance: string
}

export interface PrepareResult {
  draft_summary: string
  action_id: string
  confirmation_token: string
  expires_in_seconds: number
  warning: string
  submission_status_if_confirmed: string
}

export interface WorkflowState {
  step: WorkflowStep
  query: string
  issueType: string
  issueDescription: string
  orders: OrderSummary[]
  selectedOrder: OrderDetail | null
  selectedItemId: string | null
  policy: PolicyResult | null
  caseDetail: CaseDetail | null
  prepared: PrepareResult | null
  toolLog: { tool: string; at: string; ok: boolean; summary: string }[]
  protocolVersion: string | null
  error: string | null
}

export const STORAGE_KEY = 'returnright.workflow.v1'

export const initialWorkflowState = (): WorkflowState => ({
  step: 'connect',
  query: '',
  issueType: 'unwanted',
  issueDescription: '',
  orders: [],
  selectedOrder: null,
  selectedItemId: null,
  policy: null,
  caseDetail: null,
  prepared: null,
  toolLog: [],
  protocolVersion: null,
  error: null,
})
