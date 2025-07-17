import React from 'react';
import './App.css';
import LiveStream from './LiveStream';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>BugOwl Live Stream</h1>
      </header>
      <main>
        <LiveStream />
      </main>
    </div>
  );
}

export default App;
