// -----------------------------------------------------------------------
// Este arquivo NAO esta ativo ainda. E um guia de como plugar o Keycloak
// quando a autenticacao JWT for implementada, sem precisar redesenhar a
// estrutura de chamadas REST (src/api/httpClient.js ja esta preparado).
//
// Passos futuros:
//
// 1) Instalar a lib oficial:
//      npm install keycloak-js
//
// 2) Criar a instancia usando as variaveis de src/.env:
//
//      import Keycloak from 'keycloak-js'
//
//      const keycloak = new Keycloak({
//        url: import.meta.env.VITE_KEYCLOAK_URL,
//        realm: import.meta.env.VITE_KEYCLOAK_REALM,
//        clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
//      })
//
// 3) Inicializar no bootstrap da aplicacao (src/main.jsx), antes do
//    ReactDOM.createRoot(...).render(...), usando
//    keycloak.init({ onLoad: 'login-required', pkceMethod: 'S256' })
//
// 4) Guardar o keycloak (ou so o token) em contexto React (ex: AuthContext)
//    e trocar a funcao getAuthToken() em src/api/httpClient.js para
//    retornar keycloak.token, cuidando de dar refresh quando expirar
//    (keycloak.updateToken).
//
// 5) Proteger rotas/telas verificando keycloak.authenticated.
//
// Nenhuma tela ou service precisa mudar: eles so consomem o token
// atraves do httpClient central.
// -----------------------------------------------------------------------

export {}
