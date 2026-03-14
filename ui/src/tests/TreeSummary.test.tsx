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

    expect(screen.getByText(/start building your family tree/i)).toBeInTheDocument();
    expect(screen.queryByText(/clear all/i)).not.toBeInTheDocument();
  });

  it('shows visualization by default and allows switching to list', async () => {
    const user = userEvent.setup();
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={mockRelationships} 
        onClear={mockOnClear} 
      />
    );

    // reactflow container should be present due to mock
    expect(screen.getByTestId('reactflow')).toBeInTheDocument();

    // Switch to list view
    await user.click(screen.getByRole('button', { name: /list/i }));

    // List headers should be visible
    expect(screen.getByRole('heading', { name: 'Family Members' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { name: 'Relationships' })[0]).toBeInTheDocument();
  });

  it('lists all persons with their details in list view', async () => {
    const user = userEvent.setup();
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={[]} 
        onClear={mockOnClear} 
      />
    );

    await user.click(screen.getByRole('button', { name: /list/i }));

    // Each person item has a details div; assert its combined text
    const personItems = screen.getAllByRole('listitem');

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(personItems[0].querySelector('.person-details')).toHaveTextContent(/ID:\s*1\s*•\s*Born:\s*1970-01-01/);

    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(personItems[1].querySelector('.person-details')).toHaveTextContent(/ID:\s*2\s*•\s*Born:\s*1972-02-14/);

    expect(screen.getByText('Alice Doe')).toBeInTheDocument();
    expect(personItems[2].querySelector('.person-details')).toHaveTextContent(/ID:\s*3/);
    // Alice has no birth date
    expect(personItems[2].querySelector('.person-details')).not.toHaveTextContent(/Born:/i);
  });

  it('lists relationships with human-friendly labels in list view', async () => {
    const user = userEvent.setup();
    render(
      <TreeSummary 
        persons={mockPersons} 
        relationships={mockRelationships} 
        onClear={mockOnClear} 
      />
    );

    await user.click(screen.getByRole('button', { name: /list/i }));

    expect(screen.getAllByRole('heading', { name: 'Relationships' })[0]).toBeInTheDocument();
    // Check human-friendly labels
    expect(screen.getByText(/is married to/i)).toBeInTheDocument();
    expect(screen.getAllByText(/is parent of/i)).toHaveLength(2);

    // Verify names appear in relationships list
    expect(screen.getAllByText('John Doe').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Jane Doe').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Alice Doe').length).toBeGreaterThanOrEqual(1);
  });

  it('handles unknown person IDs gracefully', async () => {
    const user = userEvent.setup();
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

    await user.click(screen.getByRole('button', { name: /list/i }));

    expect(screen.getByText('Unknown (unknown1)')).toBeInTheDocument();
    expect(screen.getByText('Unknown (unknown2)')).toBeInTheDocument();
    expect(screen.getByText(/is married to/i)).toBeInTheDocument();
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

  it('formats relationship types with spaces correctly', async () => {
    const user = userEvent.setup();
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

    await user.click(screen.getByRole('button', { name: /list/i }));

    // Human-readable
    expect(screen.getByText(/is grandparent of/i)).toBeInTheDocument();
  });
}); 