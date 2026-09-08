import { useCallback, useEffect, useState } from 'react'
import { listS3Objects, uploadS3Object, deleteS3Object } from '../api/s3Service'

// Formato real da API:
// {
//   "bucket": "filess3humberto",
//   "prefixo_buscado": "",
//   "total_objetos": 5,
//   "objetos": [
//     { "chave": "datasets/janeiro/dataset-sa.sh", "tamanho_bytes": 1153, "ultima_modificacao": "2026-07-07T18:27:06+00:00" },
//     ...
//   ]
// }
function normalize(raw) {
  if (!raw) {
    return { bucket: null, prefixoBuscado: null, items: [] }
  }

  const objetos = raw.objetos ?? []
  const items = objetos.map((obj) => ({
    chave: obj.chave,
    nome: obj.chave?.split('/').pop() || obj.chave,
    tamanhoBytes: obj.tamanho_bytes,
    ultimaModificacao: obj.ultima_modificacao,
  }))

  return {
    bucket: raw.bucket ?? null,
    prefixoBuscado: raw.prefixo_buscado ?? '',
    items,
  }
}

export function useS3Objects() {
  const [bucket, setBucket] = useState(null)
  const [prefixoBuscado, setPrefixoBuscado] = useState('')
  const [objects, setObjects] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [deletingKey, setDeletingKey] = useState(null)
  const [error, setError] = useState(null)

  const refresh = useCallback(async (prefixo) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listS3Objects(prefixo)
      const { bucket: b, prefixoBuscado: p, items } = normalize(data)
      setBucket(b)
      setPrefixoBuscado(p)
      setObjects(items)
    } catch (err) {
      setError(err.message || 'Falha ao carregar objetos do S3.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const upload = useCallback(
    async (file, caminhoDestinoS3) => {
      setUploading(true)
      setError(null)
      try {
        await uploadS3Object(file, caminhoDestinoS3)
        await refresh()
        return true
      } catch (err) {
        setError(err.message || 'Falha ao enviar arquivo para o S3.')
        return false
      } finally {
        setUploading(false)
      }
    },
    [refresh]
  )

  const remove = useCallback(
    async (chave) => {
      setDeletingKey(chave)
      setError(null)
      try {
        await deleteS3Object(chave)
        await refresh()
        return true
      } catch (err) {
        setError(err.message || 'Falha ao remover objeto do S3.')
        return false
      } finally {
        setDeletingKey(null)
      }
    },
    [refresh]
  )

  return {
    bucket,
    prefixoBuscado,
    objects,
    loading,
    uploading,
    deletingKey,
    error,
    refresh,
    upload,
    remove,
  }
}
