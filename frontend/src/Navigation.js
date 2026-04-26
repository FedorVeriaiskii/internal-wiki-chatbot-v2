import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h1>🤖 Wiki Chatbot</h1>
      </div>
      <div className="nav-links">
        <Link 
          to="/" 
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          💬 Chat
        </Link>
        <Link 
          to="/load-wiki" 
          className={`nav-link ${location.pathname === '/load-wiki' ? 'active' : ''}`}
        >
          📚 Load Wiki
        </Link>
      </div>
    </nav>
  );
};

export default Navigation;