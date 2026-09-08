import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Quando a autenticacao via Keycloak for adicionada, a inicializacao
// do keycloak.init(...) deve acontecer aqui, antes do render, com uma
// tela de loading enquanto o token e obtido. Ver src/auth/keycloakPlaceholder.js

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
