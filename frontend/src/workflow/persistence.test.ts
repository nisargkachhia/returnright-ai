import { beforeEach, describe, expect, it } from 'vitest'
import { clearWorkflow, loadWorkflow, saveWorkflow } from './persistence'
import { initialWorkflowState } from './types'

describe('workflow persistence', () => {
  beforeEach(() => {
    clearWorkflow()
  })

  it('round-trips workflow state through sessionStorage', () => {
    const state = {
      ...initialWorkflowState(),
      step: 'evaluate' as const,
      query: 'kettle',
      issueDescription: 'unused',
    }
    saveWorkflow(state)
    const loaded = loadWorkflow()
    expect(loaded.step).toBe('evaluate')
    expect(loaded.query).toBe('kettle')
    expect(loaded.issueDescription).toBe('unused')
  })

  it('returns initial state when empty', () => {
    expect(loadWorkflow().step).toBe('connect')
  })
})
