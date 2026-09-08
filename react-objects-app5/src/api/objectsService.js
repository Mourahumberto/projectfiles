import { httpClient, LOCAL_BASE_URL } from './httpClient'

const RESOURCE = '/local/objects'

// O backend usa {nome_arquivo:path} (aceita subpastas, ex: "app/data.txt").
// Codificamos cada segmento separadamente para nao escapar as barras
// (senao viraria %2F e o path converter do FastAPI nao bateria a rota).
function encodePathSegments(path) {
  return String(path)
    .split('/')
    .filter(Boolean)
    .map(encodeURIComponent)
    .join('/')
}

/**
 * GET /local/objects
 * Lista os objetos/arquivos disponiveis.
 */
export function listObjects() {
  return httpClient.get(RESOURCE)
}

/**
 * POST /local/objects  (multipart/form-data, campo "arquivo")
 * Envia um novo arquivo.
 * @param {File} file
 */
export function uploadObject(file) {
  const formData = new FormData()
  formData.append('arquivo', file)

  return httpClient.post(RESOURCE, {
    body: formData,
    isFormData: true,
  })
}

/**
 * DELETE /local/objects/{nome_arquivo}
 * Remove um arquivo pelo caminho (relativo a pasta raiz do backend, ex: "/files").
 * @param {string} nomeArquivo
 */
export function deleteObject(nomeArquivo) {
  return httpClient.delete(`${RESOURCE}/${encodePathSegments(nomeArquivo)}`)
}

/**
 * GET /local/objects/{nome_arquivo}
 * Monta a URL de download direto do arquivo (o backend responde com
 * FileResponse + Content-Disposition, entao um <a href> ou window.open
 * ja dispara o download do navegador sem precisar de fetch/blob).
 * @param {string} nomeArquivo
 */
export function getDownloadUrl(nomeArquivo) {
  return `${LOCAL_BASE_URL}${RESOURCE}/${encodePathSegments(nomeArquivo)}`
}
