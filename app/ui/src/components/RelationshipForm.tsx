import React, { useState } from 'react';
import { Person, Relationship } from '../types';

interface RelationshipFormProps {
  persons: Person[];
  onAddRelationship: (relationship: Relationship) => void;
}

const RELATIONSHIP_TYPES = [
  'PARENT_OF',
  'MARRIED',
  'SIBLING',
  'GRANDPARENT_OF',
];

const RELATIONSHIP_LABELS = {
  'PARENT_OF': 'Parent of',
  'MARRIED': 'Married to',
  'SIBLING': 'Sibling of',
  'GRANDPARENT_OF': 'Grandparent of',
};

export const RelationshipForm: React.FC<RelationshipFormProps> = ({ 
  persons, 
  onAddRelationship 
}) => {
  const [startId, setStartId] = useState('');
  const [endId, setEndId] = useState('');
  const [type, setType] = useState('PARENT_OF');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!startId || !endId) {
      alert('Please select both persons');
      return;
    }
    
    if (startId === endId) {
      alert('A person cannot have a relationship with themselves');
      return;
    }

    const relationship: Relationship = {
      start_id: startId,
      end_id: endId,
      type,
    };

    onAddRelationship(relationship);
    setStartId('');
    setEndId('');
    setType('PARENT_OF');
  };

  const isFormValid = persons.length >= 2 && startId && endId && startId !== endId;

  return (
    <div className="form-container">
      <h2>Add Relationship</h2>
      {persons.length < 2 ? (
        <div className="empty-state" style={{ padding: '2rem 1rem' }}>
          Add at least 2 people to create relationships
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="start-person">From Person *</label>
            <select
              id="start-person"
              value={startId}
              onChange={(e) => setStartId(e.target.value)}
              required
            >
              <option value="">Select person...</option>
              {persons.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name} (ID: {person.id})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="relationship-type">Relationship Type *</label>
            <select
              id="relationship-type"
              value={type}
              onChange={(e) => setType(e.target.value)}
              required
            >
              {RELATIONSHIP_TYPES.map((relType) => (
                <option key={relType} value={relType}>
                  {RELATIONSHIP_LABELS[relType as keyof typeof RELATIONSHIP_LABELS]}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="end-person">To Person *</label>
            <select
              id="end-person"
              value={endId}
              onChange={(e) => setEndId(e.target.value)}
              required
            >
              <option value="">Select person...</option>
              {persons.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name} (ID: {person.id})
                </option>
              ))}
            </select>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={!isFormValid}
          >
            Add Relationship
          </button>
        </form>
      )}
    </div>
  );
}; 