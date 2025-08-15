import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PersonForm } from '../components/PersonForm';
import { Person } from '../types';

describe('PersonForm', () => {
  const mockOnAddPerson = vi.fn();

  beforeEach(() => {
    mockOnAddPerson.mockClear();
  });

  it('renders all form fields', () => {
    render(<PersonForm onAddPerson={mockOnAddPerson} />);
    
    expect(screen.getByLabelText(/id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/birth date/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add person/i })).toBeInTheDocument();
  });

  it('submits form with explicit id', async () => {
    const user = userEvent.setup();
    render(<PersonForm onAddPerson={mockOnAddPerson} />);

    await user.type(screen.getByLabelText(/id/i), 'test-id');
    await user.type(screen.getByLabelText(/name/i), 'Test Name');
    await user.type(screen.getByLabelText(/birth date/i), '1990-05-15');

    await user.click(screen.getByRole('button', { name: /add person/i }));

    await waitFor(() => {
      expect(mockOnAddPerson).toHaveBeenCalledWith({
        id: 'test-id',
        name: 'Test Name',
        birth: '1990-05-15',
      });
    });
  });

  it('auto-generates id when not provided', async () => {
    const user = userEvent.setup();
    const originalRandom = Math.random;
    Math.random = () => 0.123456789; // suffix '3d0rj' (approx) but we will only assert prefix and format

    render(<PersonForm onAddPerson={mockOnAddPerson} />);

    await user.type(screen.getByLabelText(/name/i), 'Alice Smith');

    await user.click(screen.getByRole('button', { name: /add person/i }));

    await waitFor(() => {
      const arg = mockOnAddPerson.mock.calls[0][0] as Person;
      expect(arg.name).toBe('Alice Smith');
      expect(arg.id).toMatch(/^alice-smith-/);
      expect(arg.birth).toBeUndefined();
    });

    Math.random = originalRandom;
  });

  it('submits form without birth date', async () => {
    const user = userEvent.setup();
    render(<PersonForm onAddPerson={mockOnAddPerson} />);

    await user.type(screen.getByLabelText(/id/i), 'test-id-2');
    await user.type(screen.getByLabelText(/name/i), 'Another Name');

    await user.click(screen.getByRole('button', { name: /add person/i }));

    await waitFor(() => {
      expect(mockOnAddPerson).toHaveBeenCalledWith({
        id: 'test-id-2',
        name: 'Another Name',
        birth: undefined,
      });
    });
  });

  it('shows alert for missing required fields', async () => {
    // Mock window.alert
    const originalAlert = window.alert;
    const alertMock = vi.fn();
    window.alert = alertMock;

    render(<PersonForm onAddPerson={mockOnAddPerson} />);

    // Submit form with empty fields using fireEvent to bypass HTML5 validation
    const form = screen.getByRole('button', { name: /add person/i }).closest('form')!;
    fireEvent.submit(form);

    expect(alertMock).toHaveBeenCalledWith('Name is required');
    expect(mockOnAddPerson).not.toHaveBeenCalled();

    // Restore original alert
    window.alert = originalAlert;
  });

  it('clears form after successful submission', async () => {
    const user = userEvent.setup();
    render(<PersonForm onAddPerson={mockOnAddPerson} />);

    const idInput = screen.getByLabelText(/id/i) as HTMLInputElement;
    const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
    const birthInput = screen.getByLabelText(/birth date/i) as HTMLInputElement;

    await user.type(idInput, 'clear-test');
    await user.type(nameInput, 'Clear Test');
    await user.type(birthInput, '2000-01-01');

    await user.click(screen.getByRole('button', { name: /add person/i }));

    await waitFor(() => {
      expect(idInput.value).toBe('');
      expect(nameInput.value).toBe('');
      expect(birthInput.value).toBe('');
    });
  });

  it('trims whitespace from inputs', async () => {
    const user = userEvent.setup();
    render(<PersonForm onAddPerson={mockOnAddPerson} />);

    await user.type(screen.getByLabelText(/id/i), '  trimmed-id  ');
    await user.type(screen.getByLabelText(/name/i), '  Trimmed Name  ');
    await user.type(screen.getByLabelText(/birth date/i), '1995-05-05');

    await user.click(screen.getByRole('button', { name: /add person/i }));

    await waitFor(() => {
      expect(mockOnAddPerson).toHaveBeenCalledWith({
        id: 'trimmed-id',
        name: 'Trimmed Name',
        birth: '1995-05-05',
      });
    });
  });
}); 