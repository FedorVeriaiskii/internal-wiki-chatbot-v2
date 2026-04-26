import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="navigation">
      <div className="navigation-container">
        <h1>🤖 Wiki Chatbot</h1>
        <div className="nav-links">
          <Link 
            to="/" 
            className={location.pathname === '/' ? 'active' : ''}
          >
            💬 Chat
          </Link>
          <Link 
            to="/load-wiki" 
            className={location.pathname === '/load-wiki' ? 'active' : ''}
          >
            📚 Load Wiki
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;