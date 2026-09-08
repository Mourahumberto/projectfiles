import { useObjects } from '../hooks/useObjects'
import { StatusBar } from './StatusBar'
import { UploadPanel } from './UploadPanel'
import { ObjectsTable } from './ObjectsTable'
import { LOCAL_BASE_URL } from '../api/httpClient'

export function LocalView() {
  const { caminhoSolicitado, objects, totals, loading, uploading, deletingPath, error, upload, remove } =
    useObjects()

  return (
    <div>
      <StatusBar
        baseUrl={LOCAL_BASE_URL}
        path={caminhoSolicitado || '/local/objects'}
        loading={loading}
        rightText={`${totals.arquivos} ${totals.arquivos === 1 ? 'arquivo' : 'arquivos'} · ${totals.pastas} ${totals.pastas === 1 ? 'pasta' : 'pastas'}`}
      />

      {error && <div className="alert">{error}</div>}

      <main className="app__grid">
        <UploadPanel title="Enviar arquivo" hint="POST /local/objects" onUpload={upload} uploading={uploading} />
        <ObjectsTable
          objects={objects}
          loading={loading}
          deletingPath={deletingPath}
          onDelete={remove}
        />
      </main>
    </div>
  )
}
