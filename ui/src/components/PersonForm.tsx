import React, { useState } from 'react';
import { Person } from '../types';

interface PersonFormProps {
  onAddPerson: (person: Person) => void;
}

export const PersonForm: React.FC<PersonFormProps> = ({ onAddPerson }) => {
  const [id, setId] = useState('');
  const [name, setName] = useState('');
  const [birth, setBirth] = useState('');

  const generateIdFromName = (inputName: string) => {
    const base = inputName
      .trim()
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '');
    const suffix = Math.random().toString(36).slice(2, 7);
    return `${base || 'person'}-${suffix}`;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert('Name is required');
      return;
    }

    const computedId = id.trim() || generateIdFromName(name);

    const person: Person = {
      id: computedId,
      name: name.trim(),
      birth: birth.trim() || undefined,
    };

    onAddPerson(person);
    setId('');
    setName('');
    setBirth('');
  };

  return (
    <div className="form-container">
      <h2>Add Person</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="id">ID (optional)</label>
          <input
            type="text"
            id="id"
            value={id}
            onChange={(e) => setId(e.target.value)}
            placeholder="Leave blank to auto-generate"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="name">Name *</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Full name (e.g., John Doe)"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="birth">Birth Date</label>
          <input
            type="date"
            id="birth"
            value={birth}
            onChange={(e) => setBirth(e.target.value)}
          />
        </div>
        
        <button type="submit" className="btn btn-primary">Add Person</button>
      </form>
    </div>
  );
}; 