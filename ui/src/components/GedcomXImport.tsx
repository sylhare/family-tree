import React, { useState } from 'react';
import { api } from '../api';

interface Props {
  onImported: () => void;
}

export const GedcomXImport: React.FC<Props> = ({ onImported }) => {
  const [importing, setImporting] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setImporting(true);
      const text = await file.text();
      const json = JSON.parse(text);
      await api.importGedcomX(json);
      onImported();
      alert('GEDCOM X imported successfully.');
    } catch (err) {
      console.error(err);
      alert(`Failed to import GEDCOM X: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setImporting(false);
      e.target.value = '';
    }
  };

  return (
    <div className="form-container">
      <h2>Import GEDCOM X</h2>
      <input
        type="file"
        accept="application/json,.json"
        onChange={handleFileChange}
        disabled={importing}
      />
      <p style={{ fontSize: '0.9rem', color: '#6c757d', marginTop: '0.5rem' }}>
        Upload a GEDCOM X JSON file. Persons and relationships will be imported into Neo4j.
      </p>
    </div>
  );
}; 