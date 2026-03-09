import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { GedcomXImport } from '../components/GedcomXImport';
import { api } from '../api';

// Mock the API module
vi.mock('../api', () => ({
  api: {
    importGedcomX: vi.fn(),
  },
}));

// Mock window.alert
const mockAlert = vi.fn();
vi.stubGlobal('alert', mockAlert);

// Mock console.error to avoid noise in tests
const mockConsoleError = vi.fn();
vi.stubGlobal('console', { ...console, error: mockConsoleError });

// Helper function to create a mock file with text() method
const createMockFile = (content: string, name: string = 'test.json') => {
  const file = new File([content], name, { type: 'application/json' });
  // Add the text() method directly to the file object
  (file as any).text = vi.fn().mockResolvedValue(content);
  return file;
};

describe('GedcomXImport', () => {
  const mockOnImported = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders import form correctly', () => {
    const { container } = render(<GedcomXImport onImported={mockOnImported} />);
    
    expect(screen.getByText('Import GEDCOM X')).toBeInTheDocument();
    expect(screen.getByText(/upload a gedcom x json file/i)).toBeInTheDocument();
    
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).not.toBeDisabled();
    expect(fileInput).toHaveAttribute('accept', 'application/json,.json');
  });

  it('successfully imports valid GEDCOM X file', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);
    mockImportGedcomX.mockResolvedValueOnce({ status: 'success' });

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    // Create a mock file with valid GEDCOM X JSON
    const gedcomXData = {
      persons: [
        {
          id: 'I1',
          names: [{ nameForms: [{ fullText: 'John Doe' }] }],
          facts: [{ type: 'http://gedcomx.org/Birth', date: { original: '1970-01-01' } }]
        }
      ],
      relationships: [
        {
          type: 'http://gedcomx.org/Couple',
          person1: { resource: '#I1' },
          person2: { resource: '#I2' }
        }
      ]
    };

    const file = createMockFile(JSON.stringify(gedcomXData), 'family.json');
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Simulate file selection
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockImportGedcomX).toHaveBeenCalledWith(gedcomXData);
      expect(mockOnImported).toHaveBeenCalledTimes(1);
      expect(mockAlert).toHaveBeenCalledWith('GEDCOM X imported successfully.');
    });
  });

  it('handles invalid JSON file', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    const file = createMockFile('{ invalid json }', 'invalid.json');
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockImportGedcomX).not.toHaveBeenCalled();
      expect(mockOnImported).not.toHaveBeenCalled();
      expect(mockAlert).toHaveBeenCalledWith(
        expect.stringMatching(/Failed to import GEDCOM X:.*/)
      );
      expect(mockConsoleError).toHaveBeenCalled();
    });
  });

  it('handles API import failure', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);
    mockImportGedcomX.mockRejectedValueOnce(new Error('Server error'));

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    const gedcomXData = { persons: [], relationships: [] };
    const file = createMockFile(JSON.stringify(gedcomXData), 'empty.json');
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockImportGedcomX).toHaveBeenCalledWith(gedcomXData);
      expect(mockOnImported).not.toHaveBeenCalled();
      expect(mockAlert).toHaveBeenCalledWith('Failed to import GEDCOM X: Server error');
      expect(mockConsoleError).toHaveBeenCalledWith(expect.any(Error));
    });
  });

  it('handles unknown error types', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);
    mockImportGedcomX.mockRejectedValueOnce('String error');

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    const gedcomXData = { persons: [], relationships: [] };
    const file = createMockFile(JSON.stringify(gedcomXData), 'test.json');
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalledWith('Failed to import GEDCOM X: Unknown error');
    });
  });

  it('disables input during import', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);
    
    // Create a promise that we can control
    let resolveImport: (value: { status: string }) => void;
    const importPromise = new Promise<{ status: string }>(resolve => {
      resolveImport = resolve;
    });
    mockImportGedcomX.mockReturnValueOnce(importPromise);

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    const gedcomXData = { persons: [], relationships: [] };
    const file = createMockFile(JSON.stringify(gedcomXData), 'test.json');
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Start the upload
    fireEvent.change(fileInput, { target: { files: [file] } });

    // Input should be disabled during import
    await waitFor(() => {
      expect(fileInput).toBeDisabled();
    });

    // Resolve the import
    resolveImport!({ status: 'success' });

    // Wait for import to complete and input to be re-enabled
    await waitFor(() => {
      expect(fileInput).not.toBeDisabled();
      expect(mockOnImported).toHaveBeenCalledTimes(1);
    });
  });

  it('clears file input after import attempt', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);
    mockImportGedcomX.mockResolvedValueOnce({ status: 'success' });

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    const gedcomXData = { persons: [], relationships: [] };
    const file = createMockFile(JSON.stringify(gedcomXData), 'test.json');
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockImportGedcomX).toHaveBeenCalled();
    });

    // The file input value should be cleared
    expect(fileInput.value).toBe('');
  });

  it('handles file selection cancellation', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Simulate selecting no file (user cancels file dialog)
    fireEvent.change(fileInput, { target: { files: [] } });

    // Wait a bit to ensure no async operations start
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockImportGedcomX).not.toHaveBeenCalled();
    expect(mockOnImported).not.toHaveBeenCalled();
    expect(mockAlert).not.toHaveBeenCalled();
  });

  it('handles empty file', async () => {
    const mockImportGedcomX = vi.mocked(api.importGedcomX);

    const { container } = render(<GedcomXImport onImported={mockOnImported} />);

    const file = createMockFile('', 'empty.json');
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalledWith(
        expect.stringMatching(/Failed to import GEDCOM X:.*/)
      );
    });

    expect(mockImportGedcomX).not.toHaveBeenCalled();
    expect(mockOnImported).not.toHaveBeenCalled();
  });
}); 