import { s3HttpClient } from './httpClient'

const RESOURCE = '/s3'

/**
 * GET /s3
 * Lista os objetos do bucket S3. Aceita opcionalmente um prefixo
 * (o backend devolve isso em "prefixo_buscado" na resposta).
 * @param {string} [prefixo]
 */
export function listS3Objects(prefixo) {
  if (!prefixo) return s3HttpClient.get(RESOURCE)
  const query = new URLSearchParams({ prefixo }).toString()
  return s3HttpClient.get(`${RESOURCE}?${query}`)
}

/**
 * POST /s3?caminho_destino_s3=...  (multipart/form-data, campo "arquivo")
 * Envia um novo arquivo para dentro de um "diretorio" (prefixo) do bucket.
 * @param {File} file
 * @param {string} [caminhoDestinoS3] prefixo/pasta de destino dentro do bucket (ex: "datasets")
 */
export function uploadS3Object(file, caminhoDestinoS3 = '') {
  const formData = new FormData()
  formData.append('arquivo', file)

  const query = new URLSearchParams({ caminho_destino_s3: caminhoDestinoS3 }).toString()

  return s3HttpClient.post(`${RESOURCE}?${query}`, {
    body: formData,
    isFormData: true,
  })
}

/**
 * DELETE /s3?caminho_objeto_s3=...
 * Remove um objeto do bucket pela chave completa (ex: "datasets/janeiro/local.txt").
 * @param {string} caminhoObjetoS3
 */
export function deleteS3Object(caminhoObjetoS3) {
  const query = new URLSearchParams({ caminho_objeto_s3: caminhoObjetoS3 }).toString()
  return s3HttpClient.delete(`${RESOURCE}?${query}`)
}
