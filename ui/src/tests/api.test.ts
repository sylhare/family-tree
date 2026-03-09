import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from '../api';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('healthCheck', () => {
    it('returns response when API is healthy', async () => {
      const mockResponse = { status: 'ok' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.healthCheck();
      
      expect(mockFetch).toHaveBeenCalledWith('/health');
      expect(result).toEqual(mockResponse);
    });

    it('throws error when API returns non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      await expect(api.healthCheck()).rejects.toThrow('Health check failed: Internal Server Error');
    });

    it('throws error when fetch fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(api.healthCheck()).rejects.toThrow('Network error');
    });
  });

  describe('createTree', () => {
    const mockTree = {
      persons: [{ id: '1', name: 'John', birth: '1970-01-01' }],
      relationships: [],
    };

    it('creates tree successfully', async () => {
      const mockResponse = { status: 'success' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.createTree(mockTree);
      
      expect(mockFetch).toHaveBeenCalledWith('/tree', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mockTree),
      });
      expect(result).toEqual(mockResponse);
    });

    it('throws error with detail when API returns error response', async () => {
      const errorResponse = { detail: 'Invalid data format' };
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
        json: () => Promise.resolve(errorResponse),
      });

      await expect(api.createTree(mockTree)).rejects.toThrow('Invalid data format');
    });

    it('throws error with status text when no detail provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({}),
      });

      await expect(api.createTree(mockTree)).rejects.toThrow('Request failed: Internal Server Error');
    });
  });

  describe('importGedcomX', () => {
    const mockGedcomXData = {
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

    it('imports GEDCOM X data successfully', async () => {
      const mockResponse = { status: 'success' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.importGedcomX(mockGedcomXData);
      
      expect(mockFetch).toHaveBeenCalledWith('/import/gedcomx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockGedcomXData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('throws error when import API returns error response', async () => {
      const errorText = 'Invalid GEDCOM X format';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
        text: () => Promise.resolve(errorText),
      });

      await expect(api.importGedcomX(mockGedcomXData)).rejects.toThrow(errorText);
    });

    it('throws error with status text when no error text provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
        text: () => Promise.resolve(''),
      });

      await expect(api.importGedcomX(mockGedcomXData)).rejects.toThrow('Request failed: Internal Server Error');
    });

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(api.importGedcomX(mockGedcomXData)).rejects.toThrow('Network error');
    });

    it('handles empty GEDCOM X data', async () => {
      const emptyData = { persons: [], relationships: [] };
      const mockResponse = { status: 'success' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.importGedcomX(emptyData);
      
      expect(mockFetch).toHaveBeenCalledWith('/import/gedcomx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(emptyData),
      });
      expect(result).toEqual(mockResponse);
    });
  });
}); 