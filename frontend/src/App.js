import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './Navigation';
import ChatPage from './ChatPage';
import LoadWikiPage from './LoadWikiPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <div className="app-content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/load-wiki" element={<LoadWikiPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;