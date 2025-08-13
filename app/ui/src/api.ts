import { GenealogicalTree, ApiResponse } from './types';

const API_BASE = import.meta.env.PROD ? '' : '';

export const api = {
  async healthCheck(): Promise<ApiResponse> {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  },

  async createTree(tree: GenealogicalTree): Promise<ApiResponse> {
    const response = await fetch(`${API_BASE}/tree`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tree),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Request failed: ${response.statusText}`);
    }
    
    return response.json();
  },
}; 