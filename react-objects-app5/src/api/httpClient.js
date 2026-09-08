// Fabrica de clientes HTTP. Cada API (local, S3, ...) tem sua propria
// base URL/porta, mas compartilham a mesma logica de headers, erro e
// (no futuro) injecao do token JWT do Keycloak.

// Ponto unico de injecao do token. Hoje retorna null (sem auth).
// Quando o Keycloak for integrado, troque a implementacao aqui
// (ex: importar de src/auth/keycloakPlaceholder.js) e todos os
// clientes criados por createHttpClient passam a usar o token.
function getAuthToken() {
  return null
}

export function createHttpClient(baseUrl) {
  async function request(path, { method = 'GET', headers = {}, body, isFormData = false } = {}) {
    const token = getAuthToken()

    const finalHeaders = {
      Accept: 'application/json',
      ...headers,
    }

    // Nao setamos Content-Type manualmente em multipart/form-data:
    // o browser define o boundary correto sozinho.
    if (!isFormData && body !== undefined) {
      finalHeaders['Content-Type'] = 'application/json'
    }

    if (token) {
      finalHeaders.Authorization = `Bearer ${token}`
    }

    const response = await fetch(`${baseUrl}${path}`, {
      method,
      headers: finalHeaders,
      body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      let detail = response.statusText
      try {
        const errorBody = await response.json()
        detail = errorBody.detail || errorBody.message || JSON.stringify(errorBody)
      } catch {
        // corpo de erro nao era JSON, mantem statusText
      }
      const error = new Error(detail || `Erro ${response.status}`)
      error.status = response.status
      throw error
    }

    if (response.status === 204) return null

    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      return response.json()
    }
    return response.text()
  }

  return {
    baseUrl,
    get: (path, options) => request(path, { ...options, method: 'GET' }),
    post: (path, options) => request(path, { ...options, method: 'POST' }),
    delete: (path, options) => request(path, { ...options, method: 'DELETE' }),
  }
}

// Cliente da API de objetos locais (backend FastAPI "/local/objects").
export const LOCAL_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.0.53:5001'
export const localHttpClient = createHttpClient(LOCAL_BASE_URL)

// Cliente da API de objetos no S3 (backend FastAPI "/s3").
export const S3_BASE_URL = import.meta.env.VITE_S3_API_BASE_URL || 'http://192.168.0.53:5002'
export const s3HttpClient = createHttpClient(S3_BASE_URL)

// Mantidos por compatibilidade com o codigo existente.
export const BASE_URL = LOCAL_BASE_URL
export const httpClient = localHttpClient
