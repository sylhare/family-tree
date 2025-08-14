import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { RelationshipForm } from '../components/RelationshipForm';
import { Person, Relationship } from '../types';

const mockPersons: Person[] = [
  { id: '1', name: 'John Doe', birth: '1970-01-01' },
  { id: '2', name: 'Jane Doe', birth: '1972-02-14' },
  { id: '3', name: 'Alice Doe', birth: '2000-05-30' },
];

describe('RelationshipForm', () => {
  const mockOnAddRelationship = vi.fn();

  beforeEach(() => {
    mockOnAddRelationship.mockClear();
  });

  it('renders all form fields', () => {
    render(
      <RelationshipForm 
        persons={mockPersons} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );
    
    expect(screen.getByLabelText(/from person/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/relationship type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/to person/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add relationship/i })).toBeInTheDocument();
  });

  it('populates person dropdowns with provided persons', () => {
    render(
      <RelationshipForm 
        persons={mockPersons} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );

    mockPersons.forEach(person => {
      expect(screen.getAllByText(new RegExp(`${person.name} \\(ID: ${person.id}\\)`))).toHaveLength(2);
    });
  });

  it('submits valid relationship', async () => {
    const user = userEvent.setup();
    render(
      <RelationshipForm 
        persons={mockPersons} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );

    await user.selectOptions(screen.getByLabelText(/from person/i), '1');
    await user.selectOptions(screen.getByLabelText(/relationship type/i), 'MARRIED');
    await user.selectOptions(screen.getByLabelText(/to person/i), '2');

    await user.click(screen.getByRole('button', { name: /add relationship/i }));

    await waitFor(() => {
      expect(mockOnAddRelationship).toHaveBeenCalledWith({
        start_id: '1',
        end_id: '2',
        type: 'MARRIED',
      });
    });
  });

  it('shows alert when persons are not selected', async () => {
    // Mock window.alert
    const originalAlert = window.alert;
    const alertMock = vi.fn();
    window.alert = alertMock;
    
    render(
      <RelationshipForm 
        persons={mockPersons} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );

    // Submit form with empty selections using fireEvent to bypass HTML5 validation
    const form = screen.getByRole('button', { name: /add relationship/i }).closest('form')!;
    fireEvent.submit(form);

    expect(alertMock).toHaveBeenCalledWith('Please select both persons');
    expect(mockOnAddRelationship).not.toHaveBeenCalled();

    // Restore original alert
    window.alert = originalAlert;
  });

  it('shows alert when same person is selected for both fields', async () => {
    const user = userEvent.setup();
    
    // Mock window.alert
    const originalAlert = window.alert;
    const alertMock = vi.fn();
    window.alert = alertMock;
    
    render(
      <RelationshipForm 
        persons={mockPersons} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );

    await user.selectOptions(screen.getByLabelText(/from person/i), '1');
    await user.selectOptions(screen.getByLabelText(/to person/i), '1');

    // Submit via form to bypass button disabled state
    const form = screen.getByRole('button', { name: /add relationship/i }).closest('form')!;
    fireEvent.submit(form);

    expect(alertMock).toHaveBeenCalledWith('A person cannot have a relationship with themselves');
    expect(mockOnAddRelationship).not.toHaveBeenCalled();

    // Restore original alert
    window.alert = originalAlert;
  });

  it('shows empty-state when less than 2 persons available', () => {
    const singlePerson = [mockPersons[0]];
    
    render(
      <RelationshipForm 
        persons={singlePerson} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );

    expect(screen.getByText(/add at least 2 people/i)).toBeInTheDocument();
  });

  it('clears form after successful submission', async () => {
    const user = userEvent.setup();
    render(
      <RelationshipForm 
        persons={mockPersons} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );

    const fromSelect = screen.getByLabelText(/from person/i) as HTMLSelectElement;
    const toSelect = screen.getByLabelText(/to person/i) as HTMLSelectElement;
    const typeSelect = screen.getByLabelText(/relationship type/i) as HTMLSelectElement;

    await user.selectOptions(fromSelect, '1');
    await user.selectOptions(typeSelect, 'SIBLING');
    await user.selectOptions(toSelect, '3');

    await user.click(screen.getByRole('button', { name: /add relationship/i }));

    await waitFor(() => {
      expect(fromSelect.value).toBe('');
      expect(toSelect.value).toBe('');
      expect(typeSelect.value).toBe('PARENT_OF'); // default value
    });
  });

  it('includes all relationship types in dropdown', () => {
    render(
      <RelationshipForm 
        persons={mockPersons} 
        onAddRelationship={mockOnAddRelationship} 
      />
    );
    
    // Use more specific selectors to avoid conflicts
    const typeSelect = screen.getByLabelText(/relationship type/i);
    expect(typeSelect.querySelector('option[value="PARENT_OF"]')).toBeInTheDocument();
    expect(typeSelect.querySelector('option[value="MARRIED"]')).toBeInTheDocument();
    expect(typeSelect.querySelector('option[value="SIBLING"]')).toBeInTheDocument();
    expect(typeSelect.querySelector('option[value="GRANDPARENT_OF"]')).toBeInTheDocument();
  });
}); 