import React, { useState, useEffect } from 'react';
import api from '../api/api';

function Dashboard() {
  const [decks, setDecks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDecks = async () => {
      try {
        const response = await api.get('/decks/');
        setDecks(response.data);
        setLoading(false);
      } catch (error) {
        console.error("Erro ao buscar os decks:", error);
        setLoading(false);
      }
    };

    fetchDecks();
  }, []); 

  if (loading) {
    return <div>Carregando decks...</div>;
  }

  return (
    <div>
      <h1>Bem-vindo ao MemorAI!</h1>
      <h2>Seus Decks</h2>
      {decks.length === 0 ? (
        <p>Nenhum deck encontrado. Crie o seu primeiro!</p>
      ) : (
        <ul>
          {decks.map(deck => (
            <li key={deck.id}>
              <h3>{deck.name}</h3>
              <p>{deck.description}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Dashboard;