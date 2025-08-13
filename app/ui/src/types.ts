export interface Person {
  id: string;
  name: string;
  birth?: string;
}

export interface Relationship {
  start_id: string;
  end_id: string;
  type: string;
}

export interface GenealogicalTree {
  persons: Person[];
  relationships: Relationship[];
}

export interface ApiResponse {
  status: string;
} 