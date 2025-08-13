import React from 'react';
import { Person, Relationship } from '../types';

interface TreeSummaryProps {
  persons: Person[];
  relationships: Relationship[];
  onClear: () => void;
}

const RELATIONSHIP_LABELS = {
  'PARENT_OF': 'is parent of',
  'MARRIED': 'is married to',
  'SIBLING': 'is sibling of',
  'GRANDPARENT_OF': 'is grandparent of',
};

export const TreeSummary: React.FC<TreeSummaryProps> = ({ 
  persons, 
  relationships, 
  onClear 
}) => {
  const getPersonName = (id: string) => {
    const person = persons.find(p => p.id === id);
    return person ? person.name : `Unknown (${id})`;
  };

  const hasData = persons.length > 0 || relationships.length > 0;

  return (
    <div className="summary-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>Current Family Tree</h2>
        {hasData && (
          <button onClick={onClear} className="btn btn-danger" style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
            Clear All
          </button>
        )}
      </div>

      <div className="tree-stats">
        <div className="stat-card">
          <span className="stat-number">{persons.length}</span>
          <span className="stat-label">Person{persons.length !== 1 ? 's' : ''}</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{relationships.length}</span>
          <span className="stat-label">Relationship{relationships.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {hasData ? (
        <div className="tree-lists">
          {persons.length > 0 && (
            <div className="tree-list">
              <h3>Family Members</h3>
              <ul>
                {persons.map((person) => (
                  <li key={person.id} className="person-item">
                    <div className="person-name">{person.name}</div>
                    <div className="person-details">
                      ID: {person.id}
                      {person.birth && ` • Born: ${person.birth}`}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {relationships.length > 0 && (
            <div className="tree-list">
              <h3>Relationships</h3>
              <ul>
                {relationships.map((rel, index) => (
                  <li key={index} className="relationship-item">
                    <div className="relationship-text">
                      <strong>{getPersonName(rel.start_id)}</strong> {RELATIONSHIP_LABELS[rel.type as keyof typeof RELATIONSHIP_LABELS] || rel.type.toLowerCase().replace('_', ' ')} <strong>{getPersonName(rel.end_id)}</strong>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          Start building your family tree by adding some people!
        </div>
      )}
    </div>
  );
}; 