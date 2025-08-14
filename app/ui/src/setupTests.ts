import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'
import React from 'react'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Minimal ResizeObserver mock for libraries relying on it (e.g., layouts)
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-ignore
global.ResizeObserver = global.ResizeObserver || ResizeObserverMock as any

// Provide stable getBoundingClientRect for layout-sensitive components
if (!HTMLElement.prototype.getBoundingClientRect ||
    (HTMLElement.prototype.getBoundingClientRect && (HTMLElement.prototype.getBoundingClientRect as any).__isMock !== true)) {
  const rectMock = () => ({
    width: 800,
    height: 600,
    top: 0,
    left: 0,
    bottom: 600,
    right: 800,
    x: 0,
    y: 0,
    toJSON: () => {}
  })
  Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
    configurable: true,
    value: Object.assign(rectMock, { __isMock: true })
  })
}

// Mock reactflow to avoid complex DOM APIs in tests while still rendering content
vi.mock('reactflow', async () => {
  const React = await import('react')
  const addEdge = (connection: any, edges: any[]) => {
    return [
      ...edges,
      {
        id: `e-${String(Math.random()).slice(2)}`,
        source: connection.source,
        target: connection.target,
      },
    ]
  }
  const useStateLike = (initial: any) => {
    const [value, setValue] = (React as any).useState(initial)
    const onChange = vi.fn()
    return [value, setValue, onChange]
  }
  const Controls = () => React.createElement('div', { 'data-testid': 'rf-controls' })
  const MiniMap = () => React.createElement('div', { 'data-testid': 'rf-minimap' })
  const Background = () => React.createElement('div', { 'data-testid': 'rf-background' })
  const ReactFlow = ({ children }: any) => React.createElement('div', { 'data-testid': 'reactflow' }, children)

  return {
    default: ReactFlow,
    Controls,
    MiniMap,
    Background,
    BackgroundVariant: { Dots: 'dots' },
    Position: { Top: 'top', Bottom: 'bottom' },
    addEdge,
    useNodesState: useStateLike,
    useEdgesState: useStateLike,
  }
}) 