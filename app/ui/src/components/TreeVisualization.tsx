import React, { useMemo, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Person, Relationship } from '../types';

interface TreeVisualizationProps {
  persons: Person[];
  relationships: Relationship[];
}

interface PersonNode extends Node {
  data: {
    label: string;
    person: Person;
  };
}

const RELATIONSHIP_COLORS = {
  'PARENT_OF': '#e74c3c',
  'MARRIED': '#f39c12',
  'SIBLING': '#3498db',
  'GRANDPARENT_OF': '#9b59b6',
} as const;

const RELATIONSHIP_LABELS = {
  'PARENT_OF': 'Parent',
  'MARRIED': 'Married',
  'SIBLING': 'Sibling',
  'GRANDPARENT_OF': 'Grandparent',
} as const;

export const TreeVisualization: React.FC<TreeVisualizationProps> = ({
  persons,
  relationships,
}) => {
  // Convert persons to nodes
  const initialNodes: PersonNode[] = useMemo(() => {
    if (persons.length === 0) return [];

    // Calculate positions using a simple layout algorithm
    const nodeWidth = 200;
    const nodeHeight = 80;
    const horizontalSpacing = 300;
    const verticalSpacing = 150;
    
    // Group people by generation based on relationships
    const generations = new Map<string, number>();
    const processed = new Set<string>();
    
    // Find root nodes (people who are not children)
    const children = new Set(
      relationships
        .filter(rel => rel.type === 'PARENT_OF')
        .map(rel => rel.end_id)
    );
    
    const roots = persons.filter(person => !children.has(person.id));
    
    // Start with roots at generation 0
    roots.forEach(person => generations.set(person.id, 0));
    
    // Process relationships to assign generations
    const queue = [...roots.map(p => p.id)];
    
    while (queue.length > 0) {
      const personId = queue.shift()!;
      if (processed.has(personId)) continue;
      processed.add(personId);
      
      const currentGeneration = generations.get(personId) || 0;
      
      // Find children
      relationships
        .filter(rel => rel.start_id === personId && rel.type === 'PARENT_OF')
        .forEach(rel => {
          if (!generations.has(rel.end_id)) {
            generations.set(rel.end_id, currentGeneration + 1);
            queue.push(rel.end_id);
          }
        });
      
      // Find spouses (same generation)
      relationships
        .filter(rel => rel.start_id === personId && rel.type === 'MARRIED')
        .forEach(rel => {
          if (!generations.has(rel.end_id)) {
            generations.set(rel.end_id, currentGeneration);
            queue.push(rel.end_id);
          }
        });
      
      relationships
        .filter(rel => rel.end_id === personId && rel.type === 'MARRIED')
        .forEach(rel => {
          if (!generations.has(rel.start_id)) {
            generations.set(rel.start_id, currentGeneration);
            queue.push(rel.start_id);
          }
        });
    }
    
    // Assign generation 0 to any remaining people
    persons.forEach(person => {
      if (!generations.has(person.id)) {
        generations.set(person.id, 0);
      }
    });
    
    // Group by generation for positioning
    const generationGroups = new Map<number, Person[]>();
    persons.forEach(person => {
      const gen = generations.get(person.id) || 0;
      if (!generationGroups.has(gen)) {
        generationGroups.set(gen, []);
      }
      generationGroups.get(gen)!.push(person);
    });
    
    // Calculate positions
    return persons.map((person, index) => {
      const generation = generations.get(person.id) || 0;
      const peopleInGeneration = generationGroups.get(generation) || [];
      const indexInGeneration = peopleInGeneration.findIndex(p => p.id === person.id);
      const totalInGeneration = peopleInGeneration.length;
      
      // Center the generation horizontally
      const totalWidth = (totalInGeneration - 1) * horizontalSpacing;
      const startX = -totalWidth / 2;
      
      const x = startX + indexInGeneration * horizontalSpacing;
      const y = generation * verticalSpacing;
      
      return {
        id: person.id,
        type: 'default',
        position: { x, y },
        data: {
          label: `${person.name}\n${person.id}${person.birth ? `\n🎂 ${person.birth}` : ''}`,
          person,
        },
        style: {
          background: '#ffffff',
          border: '2px solid #667eea',
          borderRadius: '8px',
          padding: '10px',
          width: nodeWidth,
          height: nodeHeight,
          fontSize: '12px',
          textAlign: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      } as PersonNode;
    });
  }, [persons, relationships]);

  // Convert relationships to edges
  const initialEdges: Edge[] = useMemo(() => {
    return relationships.map((rel, index) => ({
      id: `edge-${index}`,
      source: rel.start_id,
      target: rel.end_id,
      type: 'smoothstep',
      animated: rel.type === 'MARRIED',
      style: {
        stroke: RELATIONSHIP_COLORS[rel.type as keyof typeof RELATIONSHIP_COLORS] || '#666',
        strokeWidth: rel.type === 'PARENT_OF' ? 3 : 2,
      },
      label: RELATIONSHIP_LABELS[rel.type as keyof typeof RELATIONSHIP_LABELS] || rel.type,
      labelStyle: {
        fontSize: '10px',
        fontWeight: 'bold',
        fill: RELATIONSHIP_COLORS[rel.type as keyof typeof RELATIONSHIP_COLORS] || '#666',
      },
      labelBgStyle: {
        fill: 'white',
        fillOpacity: 0.8,
      },
    }));
  }, [relationships]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Update nodes and edges when props change
  React.useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  React.useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  if (persons.length === 0) {
    return (
      <div className="tree-visualization-empty">
        <div style={{ 
          textAlign: 'center', 
          padding: '3rem', 
          color: '#6c757d',
          fontSize: '1.1rem',
          background: '#f8f9fa',
          borderRadius: '12px',
          border: '2px dashed #dee2e6'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌳</div>
          Add some family members to see the tree visualization!
        </div>
      </div>
    );
  }

  return (
    <div className="tree-visualization" style={{ height: '500px', width: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.5,
          maxZoom: 1.5,
        }}
        minZoom={0.3}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
      >
        <Controls 
          position="top-right"
          style={{
            background: 'white',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
          }}
        />
        <MiniMap 
          nodeColor="#667eea"
          position="bottom-right"
          style={{
            background: 'white',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
          }}
        />
        <Background 
          variant={BackgroundVariant.Dots} 
          gap={20} 
          size={1}
          color="#e9ecef"
        />
      </ReactFlow>
      
      <div className="relationship-legend" style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'white',
        padding: '1rem',
        borderRadius: '8px',
        border: '1px solid #dee2e6',
        fontSize: '12px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      }}>
        <h4 style={{ margin: '0 0 0.5rem 0', color: '#2c3e50' }}>Relationships</h4>
        {Object.entries(RELATIONSHIP_COLORS).map(([type, color]) => (
          <div key={type} style={{ 
            display: 'flex', 
            alignItems: 'center', 
            marginBottom: '0.25rem',
            gap: '0.5rem'
          }}>
            <div style={{
              width: '20px',
              height: '3px',
              backgroundColor: color,
              borderRadius: '2px',
            }} />
            <span style={{ color: '#2c3e50' }}>
              {RELATIONSHIP_LABELS[type as keyof typeof RELATIONSHIP_LABELS]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}; 