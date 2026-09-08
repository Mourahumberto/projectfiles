import { useCallback, useEffect, useMemo, useState } from 'react'
import { listObjects, uploadObject, deleteObject } from '../api/objectsService'

// Junta duas partes de caminho sem duplicar barras.
function joinPath(base, name) {
  if (!base) return name
  return `${base.replace(/\/+$/, '')}/${name}`
}

// Formato real da API:
// {
//   "caminho_solicitado": "/code",
//   "total_arquivos": 2,
//   "total_pastas": 1,
//   "arquivos": ["image.png", "requirements.txt"],
//   "pastas": ["app"]
// }
//
// Aqui transformamos isso em uma lista unica de itens
// { tipo: 'arquivo' | 'pasta', nome, caminho } para a tabela renderizar.
function normalize(raw) {
  if (!raw) {
    return { caminhoSolicitado: null, items: [] }
  }

  const caminhoSolicitado = raw.caminho_solicitado ?? null
  const arquivos = raw.arquivos ?? []
  const pastas = raw.pastas ?? []

  const items = [
    ...pastas.map((nome) => ({
      tipo: 'pasta',
      nome,
      caminho: joinPath(caminhoSolicitado, nome),
    })),
    ...arquivos.map((nome) => ({
      tipo: 'arquivo',
      nome,
      caminho: joinPath(caminhoSolicitado, nome),
    })),
  ]

  return { caminhoSolicitado, items }
}

export function useObjects() {
  const [caminhoSolicitado, setCaminhoSolicitado] = useState(null)
  const [objects, setObjects] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [deletingPath, setDeletingPath] = useState(null)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listObjects()
      const { caminhoSolicitado: base, items } = normalize(data)
      setCaminhoSolicitado(base)
      setObjects(items)
    } catch (err) {
      setError(err.message || 'Falha ao carregar objetos.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const upload = useCallback(
    async (file) => {
      setUploading(true)
      setError(null)
      try {
        await uploadObject(file)
        await refresh()
        return true
      } catch (err) {
        setError(err.message || 'Falha ao enviar arquivo.')
        return false
      } finally {
        setUploading(false)
      }
    },
    [refresh]
  )

  const remove = useCallback(
    async (caminhoArquivo) => {
      setDeletingPath(caminhoArquivo)
      setError(null)
      try {
        await deleteObject(caminhoArquivo)
        await refresh()
        return true
      } catch (err) {
        setError(err.message || 'Falha ao remover arquivo.')
        return false
      } finally {
        setDeletingPath(null)
      }
    },
    [refresh]
  )

  const totals = useMemo(
    () => ({
      arquivos: objects.filter((o) => o.tipo === 'arquivo').length,
      pastas: objects.filter((o) => o.tipo === 'pasta').length,
    }),
    [objects]
  )

  return {
    caminhoSolicitado,
    objects,
    totals,
    loading,
    uploading,
    deletingPath,
    error,
    refresh,
    upload,
    remove,
  }
}
