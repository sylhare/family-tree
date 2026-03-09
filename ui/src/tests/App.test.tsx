import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import App from '../App';
import { api } from '../api';

// Mock the API module
vi.mock('../api', () => ({
  api: {
    healthCheck: vi.fn(),
    createTree: vi.fn(),
    getTree: vi.fn(),
  }
}));

// Mock window.confirm
const mockConfirm = vi.fn();
Object.defineProperty(window, 'confirm', {
  value: mockConfirm,
  writable: true,
});

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockConfirm.mockReturnValue(true);
    // Mock successful health check by default
    vi.mocked(api.healthCheck).mockResolvedValue({ status: 'ok' });
    vi.mocked(api.createTree).mockResolvedValue({ status: 'success' });
    vi.mocked(api.getTree).mockResolvedValue({ persons: [], relationships: [] });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('renders the main app layout', async () => {
    render(<App />);
    
    expect(screen.getByText('🌳 Family Tree Manager')).toBeInTheDocument();
    expect(screen.getByText('API Status:')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Add Person' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Add Relationship' })).toBeInTheDocument();
    expect(screen.getByText('Built with React + TypeScript • Backend: FastAPI + Neo4j')).toBeInTheDocument();
  });

  it('checks API health on mount and shows online status', async () => {
    render(<App />);
    
    // Initially shows checking
    expect(screen.getByText('Checking...')).toBeInTheDocument();
    
    // Wait for health check to complete
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });
    
    expect(api.healthCheck).toHaveBeenCalledTimes(1);
  });

  it('shows offline status when API health check fails', async () => {
    vi.mocked(api.healthCheck).mockRejectedValue(new Error('API unavailable'));
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('❌ Offline')).toBeInTheDocument();
    });
    
    expect(screen.getByText('⚠️ API is offline. Make sure the backend is running with')).toBeInTheDocument();
  });

  it('adds a person successfully', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Wait for initial health check
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add a person
    await user.type(screen.getByLabelText(/id/i), 'person-1');
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/birth date/i), '1970-01-01');
    
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Check success message
    await waitFor(() => {
      expect(screen.getByText('Added John Doe to the family tree')).toBeInTheDocument();
    });

    // Check person appears in summary (switch to List view to see details)
    expect(screen.getByText('Person')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /list/i }));
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('prevents adding duplicate person IDs', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add first person
    await user.type(screen.getByLabelText(/id/i), 'duplicate-id');
    await user.type(screen.getByLabelText(/name/i), 'First Person');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Try to add person with same ID
    await user.type(screen.getByLabelText(/id/i), 'duplicate-id');
    await user.type(screen.getByLabelText(/name/i), 'Second Person');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Check error message
    await waitFor(() => {
      expect(screen.getByText('Person with ID "duplicate-id" already exists')).toBeInTheDocument();
    });

    // Should still only have 1 person
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('adds a relationship successfully', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add two persons first
    await user.type(screen.getByLabelText(/id/i), 'person-1');
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    await user.type(screen.getByLabelText(/id/i), 'person-2');
    await user.type(screen.getByLabelText(/name/i), 'Jane Doe');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Add relationship
    await user.selectOptions(screen.getByLabelText(/from person/i), 'person-1');
    await user.selectOptions(screen.getByLabelText(/relationship type/i), 'MARRIED');
    await user.selectOptions(screen.getByLabelText(/to person/i), 'person-2');
    await user.click(screen.getByRole('button', { name: /add relationship/i }));

    // Check success message and summary
    await waitFor(() => {
      expect(screen.getByText('Added relationship')).toBeInTheDocument();
    });

    // Relationship count card shows 1
    expect(screen.getAllByText('1')[0]).toBeInTheDocument();
  });

  it('prevents adding duplicate relationships', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add persons and relationship
    await user.type(screen.getByLabelText(/id/i), 'p1');
    await user.type(screen.getByLabelText(/name/i), 'Person 1');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    await user.type(screen.getByLabelText(/id/i), 'p2');
    await user.type(screen.getByLabelText(/name/i), 'Person 2');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Add first relationship
    await user.selectOptions(screen.getByLabelText(/from person/i), 'p1');
    await user.selectOptions(screen.getByLabelText(/relationship type/i), 'SIBLING');
    await user.selectOptions(screen.getByLabelText(/to person/i), 'p2');
    await user.click(screen.getByRole('button', { name: /add relationship/i }));

    // Try to add same relationship again
    await user.selectOptions(screen.getByLabelText(/from person/i), 'p1');
    await user.selectOptions(screen.getByLabelText(/relationship type/i), 'SIBLING');
    await user.selectOptions(screen.getByLabelText(/to person/i), 'p2');
    await user.click(screen.getByRole('button', { name: /add relationship/i }));

    // Check error message
    await waitFor(() => {
      expect(screen.getByText('This relationship already exists')).toBeInTheDocument();
    });

    // Should still only have 1 relationship
    expect(screen.getAllByText('1')[0]).toBeInTheDocument();
  });

  it('submits tree to API successfully', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add a person
    await user.type(screen.getByLabelText(/id/i), 'test-person');
    await user.type(screen.getByLabelText(/name/i), 'Test Person');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Submit tree
    await user.click(screen.getByRole('button', { name: /save to neo4j/i }));

    // Wait for completion (the loading state might be too brief to catch)
    await waitFor(() => {
      expect(screen.getByText('Family tree successfully saved to Neo4j!')).toBeInTheDocument();
    });

    expect(api.createTree).toHaveBeenCalledWith({
      persons: [{ id: 'test-person', name: 'Test Person', birth: undefined }],
      relationships: []
    });
  });

  it('shows error when tree submission fails', async () => {
    vi.mocked(api.createTree).mockRejectedValue(new Error('Server error'));
    
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add a person and submit
    await user.type(screen.getByLabelText(/id/i), 'test-person');
    await user.type(screen.getByLabelText(/name/i), 'Test Person');
    await user.click(screen.getByRole('button', { name: /add person/i }));
    await user.click(screen.getByRole('button', { name: /save to neo4j/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed to save tree: Server error')).toBeInTheDocument();
    });
  });

  it('prevents submission when no persons exist', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // The submit button should be disabled when no persons exist
    const submitButton = screen.getByRole('button', { name: /save to neo4j/i });
    expect(submitButton).toBeDisabled();
    
    // Clicking a disabled button shouldn't trigger the handler
    // So we don't expect any message to appear
    expect(api.createTree).not.toHaveBeenCalled();
  });

  it('disables submit button when API is offline', async () => {
    vi.mocked(api.healthCheck).mockRejectedValue(new Error('Offline'));
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('❌ Offline')).toBeInTheDocument();
    });

    const submitButton = screen.getByRole('button', { name: /save to neo4j/i });
    expect(submitButton).toBeDisabled();
  });

  it('clears all data when confirmed', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add some data
    await user.type(screen.getByLabelText(/id/i), 'test-person');
    await user.type(screen.getByLabelText(/name/i), 'Test Person');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    expect(screen.getAllByText('1')[0]).toBeInTheDocument();

    // Clear all data
    await user.click(screen.getByRole('button', { name: /clear all/i }));

    await waitFor(() => {
      expect(screen.getByText('All data cleared')).toBeInTheDocument();
    });

    expect(screen.getByText(/start building your family tree/i)).toBeInTheDocument();
    expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to clear all data?');
  });

  it('does not clear data when confirmation is cancelled', async () => {
    mockConfirm.mockReturnValue(false);
    
    const user = userEvent.setup();
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    // Add some data
    await user.type(screen.getByLabelText(/id/i), 'test-person');
    await user.type(screen.getByLabelText(/name/i), 'Test Person');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Try to clear but cancel
    await user.click(screen.getByRole('button', { name: /clear all/i }));

    // Data should still be there
    expect(screen.getAllByText('1')[0]).toBeInTheDocument();
    expect(screen.queryByText('All data cleared')).not.toBeInTheDocument();
  });

  it('renders API documentation links', () => {
    render(<App />);
    
    const apiDocsLink = screen.getByRole('link', { name: 'API Documentation' });
    const neo4jLink = screen.getByRole('link', { name: 'Neo4j Browser' });
    
    expect(apiDocsLink).toHaveAttribute('href', '/docs');
    expect(apiDocsLink).toHaveAttribute('target', '_blank');
    
    expect(neo4jLink).toHaveAttribute('href', 'http://localhost:7474');
    expect(neo4jLink).toHaveAttribute('target', '_blank');
  });

  it('shows submit button as disabled when no persons exist', async () => {
    render(<App />);
    
    // Wait for health check to complete
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    const submitButton = screen.getByRole('button', { name: /save to neo4j/i });
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when persons exist and API is online', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Wait for health check to complete
    await waitFor(() => {
      expect(screen.getByText('✅ Online')).toBeInTheDocument();
    });

    const submitButton = screen.getByRole('button', { name: /save to neo4j/i });
    expect(submitButton).toBeDisabled();

    // Add a person
    await user.type(screen.getByLabelText(/id/i), 'test-person');
    await user.type(screen.getByLabelText(/name/i), 'Test Person');
    await user.click(screen.getByRole('button', { name: /add person/i }));

    // Wait for person to be added
    await waitFor(() => {
      expect(screen.getAllByText('1')[0]).toBeInTheDocument();
    });

    // Button should now be enabled
    expect(submitButton).not.toBeDisabled();
  });
}); 