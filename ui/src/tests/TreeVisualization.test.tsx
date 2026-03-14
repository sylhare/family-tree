import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { TreeVisualization } from '../components/TreeVisualization'
import { Person, Relationship } from '../types'

const persons: Person[] = [
  { id: '1', name: 'John', birth: '1970-01-01' },
  { id: '2', name: 'Jane', birth: '1971-02-02' },
  { id: '3', name: 'Child' },
]

const relationships: Relationship[] = [
  { start_id: '1', end_id: '2', type: 'MARRIED' },
  { start_id: '1', end_id: '3', type: 'PARENT_OF' },
  { start_id: '2', end_id: '3', type: 'PARENT_OF' },
]

describe('TreeVisualization', () => {
  it('renders reactflow container and legend', () => {
    render(<TreeVisualization persons={persons} relationships={relationships} />)

    // Provided by our reactflow mock
    expect(screen.getByTestId('reactflow')).toBeInTheDocument()

    // Legend present
    expect(screen.getByText('Relationships')).toBeInTheDocument()
    expect(screen.getByText('Parent')).toBeInTheDocument()
    expect(screen.getByText('Married')).toBeInTheDocument()
    expect(screen.getByText('Sibling')).toBeInTheDocument()
    expect(screen.getByText('Grandparent')).toBeInTheDocument()
  })

  it('shows empty hint when no persons', () => {
    render(<TreeVisualization persons={[]} relationships={[]} />)
    expect(screen.getByText(/add some family members/i)).toBeInTheDocument()
  })
}) 