import React from 'react';
import './App.css';
import Playground from './components/Playground';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>BugOwl Playground</h1>
      </header>
      <main>
        <Playground />
      </main>
    </div>
  );
}

export default App;
