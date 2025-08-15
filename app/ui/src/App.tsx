import React, { useState, useEffect } from 'react';
import { PersonForm } from './components/PersonForm';
import { RelationshipForm } from './components/RelationshipForm';
import { TreeSummary } from './components/TreeSummary';
import { GedcomXImport } from './components/GedcomXImport';
import { api } from './api';
import { Person, Relationship, GenealogicalTree } from './types';
import './App.css';

function App() {
  const [persons, setPersons] = useState<Person[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      await api.healthCheck();
      setApiStatus('online');
      // Load initial tree after API is reachable
      await loadInitialTree();
    } catch (error) {
      setApiStatus('offline');
      console.error('API health check failed:', error);
    }
  };

  const loadInitialTree = async () => {
    try {
      const tree = await api.getTree();
      // Only update if backend has some data
      if ((tree.persons && tree.persons.length) || (tree.relationships && tree.relationships.length)) {
        setPersons(tree.persons);
        setRelationships(tree.relationships);
      }
    } catch (error) {
      console.error('Failed to load initial tree:', error);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleAddPerson = (person: Person) => {
    if (persons.some(p => p.id === person.id)) {
      showMessage('error', `Person with ID "${person.id}" already exists`);
      return;
    }
    setPersons(prev => [...prev, person]);
    showMessage('success', `Added ${person.name} to the family tree`);
  };

  const handleAddRelationship = (relationship: Relationship) => {
    // Check if relationship already exists
    const exists = relationships.some(r => 
      r.start_id === relationship.start_id && 
      r.end_id === relationship.end_id && 
      r.type === relationship.type
    );
    
    if (exists) {
      showMessage('error', 'This relationship already exists');
      return;
    }

    setRelationships(prev => [...prev, relationship]);
    showMessage('success', 'Added relationship');
  };

  const handleSubmitTree = async () => {
    if (persons.length === 0) {
      showMessage('error', 'Please add at least one person before submitting');
      return;
    }

    setLoading(true);
    try {
      const tree: GenealogicalTree = {
        persons,
        relationships,
      };
      
      await api.createTree(tree);
      showMessage('success', 'Family tree successfully saved to Neo4j!');
    } catch (error) {
      showMessage('error', `Failed to save tree: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear all data?')) {
      setPersons([]);
      setRelationships([]);
      showMessage('success', 'All data cleared');
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🌳 Family Tree Manager</h1>
        <div className="api-status">
          API Status: 
          <span className={`status-indicator ${apiStatus}`}>
            {apiStatus === 'checking' && ' Checking...'}
            {apiStatus === 'online' && ' ✅ Online'}
            {apiStatus === 'offline' && ' ❌ Offline'}
          </span>
        </div>
      </header>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <main className="app-main">
        <div className="forms-section">
          <PersonForm onAddPerson={handleAddPerson} />
          <RelationshipForm persons={persons} onAddRelationship={handleAddRelationship} />
          <GedcomXImport onImported={loadInitialTree} />
        </div>

        <div className="summary-section">
          <TreeSummary
            persons={persons}
            relationships={relationships}
            onClear={handleClearAll}
          />
          
          <div className="submit-section">
            <button
              onClick={handleSubmitTree}
              disabled={loading || persons.length === 0 || apiStatus !== 'online'}
              className="submit-btn"
            >
              {loading ? 'Saving...' : 'Save to Neo4j'}
            </button>
            
            {apiStatus === 'offline' && (
              <p className="api-warning">
                ⚠️ API is offline. Make sure the backend is running with <code>docker compose up</code>
              </p>
            )}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>
          Built with React + TypeScript • Backend: FastAPI + Neo4j
        </p>
        <p>
          <a href="/docs" target="_blank" rel="noopener noreferrer">
            API Documentation
          </a>
          {' | '}
          <a href="http://localhost:7474" target="_blank" rel="noopener noreferrer">
            Neo4j Browser
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App; 