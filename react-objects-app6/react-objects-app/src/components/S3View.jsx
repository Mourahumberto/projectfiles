import { useState } from 'react'
import { useS3Objects } from '../hooks/useS3Objects'
import { StatusBar } from './StatusBar'
import { UploadPanel } from './UploadPanel'
import { S3ObjectsTable } from './S3ObjectsTable'
import { S3_BASE_URL } from '../api/httpClient'

export function S3View() {
  const { bucket, prefixoBuscado, objects, loading, uploading, deletingKey, error, upload, remove } =
    useS3Objects()

  const [destino, setDestino] = useState('')

  return (
    <div>
      <StatusBar
        baseUrl={S3_BASE_URL}
        path={bucket ? `s3://${bucket}/${prefixoBuscado || ''}` : '/s3'}
        loading={loading}
        rightText={`${objects.length} ${objects.length === 1 ? 'objeto' : 'objetos'}`}
      />

      {error && <div className="alert">{error}</div>}

      <main className="app__grid">
        <UploadPanel
          title="Enviar para o S3"
          hint="POST /s3"
          uploading={uploading}
          onUpload={(file) => upload(file, destino)}
          extraFields={
            <label className="field">
              <span className="field__label">pasta de destino (caminho_destino_s3)</span>
              <input
                type="text"
                className="field__input"
                placeholder="ex: datasets/janeiro"
                value={destino}
                onChange={(e) => setDestino(e.target.value)}
                disabled={uploading}
              />
            </label>
          }
        />
        <S3ObjectsTable
          objects={objects}
          loading={loading}
          deletingKey={deletingKey}
          onDelete={remove}
        />
      </main>
    </div>
  )
}
