import { STORAGE_KEY, initialWorkflowState } from './types'
import type { WorkflowState } from './types'

export function loadWorkflow(): WorkflowState {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return initialWorkflowState()
    const parsed = JSON.parse(raw) as WorkflowState
    return { ...initialWorkflowState(), ...parsed, error: null }
  } catch {
    return initialWorkflowState()
  }
}

export function saveWorkflow(state: WorkflowState): void {
  const rest = { ...state, error: null }
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(rest))
}

export function clearWorkflow(): void {
  sessionStorage.removeItem(STORAGE_KEY)
}
