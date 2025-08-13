import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TreeSummary } from '../components/TreeSummary';
import { Person, Relationship } from '../types';

const mockPersons: Person[] = [
  { id: '1', name: 'John Doe', birth: '1970-01-01' },
  { id: '2', name: 'Jane Doe', birth: '1972-02-14' },
  { id: '3', name: 'Alice Doe' }, // No birth date
];

const mockRelationships: Relationship[] = [
  { start_id: '1', end_id: '2', type: 'MARRIED' },
  { start_id: '1', end_id: '3', type: 'PARENT_OF' },
  { start_id: '2', end_id: '3', type: 'PARENT_OF' },
];

describe('TreeSummary', () => {
  const mockOnClear = vi.fn();

  beforeEach(() => {
    mockOnClear.mockClear();
  });

  it('displays empty state when no data', () => {
    render(
      <TreeSummary 
        persons={[]} 
        relationships={[]} 
        onClear={mockOnClear} 
      />
    );

    expect(screen.getByText(/no family data yet/i)).toBeInTheDocument();
    expect(screen.getByText(/start by adding some persons/i)).toBeInTheDocument();
    expect(screen.queryByText(/clear all/i)).not.toBeInTheDocument();
  });

  it('displays correct statistics', () => {
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={mockRelationships} 
        onClear={mockOnClear} 
      />
    );

    expect(screen.getByText('👥 3 persons')).toBeInTheDocument();
    expect(screen.getByText('🔗 3 relationships')).toBeInTheDocument();
  });

  it('handles singular vs plural correctly', () => {
    const singlePerson = [mockPersons[0]];
    const singleRelationship = [mockRelationships[0]];

    render(
      <TreeSummary 
        persons={singlePerson} 
        relationships={singleRelationship} 
        onClear={mockOnClear} 
      />
    );

    expect(screen.getByText('👥 1 person')).toBeInTheDocument();
    expect(screen.getByText('🔗 1 relationship')).toBeInTheDocument();
  });

  it('lists all persons with their details', () => {
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={[]} 
        onClear={mockOnClear} 
      />
    );

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('(ID: 1)')).toBeInTheDocument();
    expect(screen.getByText('• Born: 1970-01-01')).toBeInTheDocument();

    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText('(ID: 2)')).toBeInTheDocument();
    expect(screen.getByText('• Born: 1972-02-14')).toBeInTheDocument();

    expect(screen.getByText('Alice Doe')).toBeInTheDocument();
    expect(screen.getByText('(ID: 3)')).toBeInTheDocument();
    // Alice has no birth date, so shouldn't show "Born:"
    expect(screen.queryByText(/alice.*born/i)).not.toBeInTheDocument();
  });

  it('lists all relationships', () => {
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={mockRelationships} 
        onClear={mockOnClear} 
      />
    );

    // Check that the relationships section exists
    expect(screen.getByText('Relationships')).toBeInTheDocument();
    
    // Check for relationship types (these should be unique in this test)
    expect(screen.getByText('MARRIED')).toBeInTheDocument();
    expect(screen.getAllByText('PARENT OF')).toHaveLength(2); // Two parent relationships
    
    // Verify all names appear in relationships list 
    // (John Doe appears in persons list + 2 relationships = 3 total)
    expect(screen.getAllByText('John Doe')).toHaveLength(3); 
    expect(screen.getAllByText('Jane Doe')).toHaveLength(3); // persons list + 2 relationships
    expect(screen.getAllByText('Alice Doe')).toHaveLength(3); // persons list + 2 relationships as target
  });

  it('handles unknown person IDs gracefully', () => {
    const badRelationship: Relationship[] = [
      { start_id: 'unknown1', end_id: 'unknown2', type: 'MARRIED' }
    ];

    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={badRelationship} 
        onClear={mockOnClear} 
      />
    );

    expect(screen.getByText('Unknown (unknown1)')).toBeInTheDocument();
    expect(screen.getByText('Unknown (unknown2)')).toBeInTheDocument();
    expect(screen.getByText('MARRIED')).toBeInTheDocument();
  });

  it('shows clear button when data exists', () => {
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={[]} 
        onClear={mockOnClear} 
      />
    );

    expect(screen.getByRole('button', { name: /clear all/i })).toBeInTheDocument();
  });

  it('calls onClear when clear button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={mockRelationships} 
        onClear={mockOnClear} 
      />
    );

    await user.click(screen.getByRole('button', { name: /clear all/i }));
    expect(mockOnClear).toHaveBeenCalledTimes(1);
  });

  it('formats relationship types correctly', () => {
    const underscoreRelationship: Relationship[] = [
      { start_id: '1', end_id: '3', type: 'GRANDPARENT_OF' }
    ];

    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={underscoreRelationship} 
        onClear={mockOnClear} 
      />
    );

    // Should replace underscore with space
    expect(screen.getByText('GRANDPARENT OF')).toBeInTheDocument();
  });
}); 