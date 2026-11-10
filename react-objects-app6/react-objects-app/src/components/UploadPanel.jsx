import { useCallback, useRef, useState } from 'react'

export function UploadPanel({ title = 'Enviar arquivo', hint, onUpload, uploading, extraFields }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const [feedback, setFeedback] = useState(null) // { type: 'ok' | 'error', text }

  const sendFile = useCallback(
    async (file) => {
      if (!file) return
      setFeedback(null)
      const ok = await onUpload(file)
      setFeedback(
        ok
          ? { type: 'ok', text: `${file.name} enviado.` }
          : { type: 'error', text: `Falha ao enviar ${file.name}.` }
      )
    },
    [onUpload]
  )

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files?.[0]
    sendFile(file)
  }

  const handleSelect = (event) => {
    const file = event.target.files?.[0]
    sendFile(file)
    event.target.value = ''
  }

  return (
    <div className="panel upload-panel">
      <div className="panel__header">
        <h2>{title}</h2>
        {hint && <span className="panel__hint">{hint}</span>}
      </div>

      {extraFields && <div className="upload-panel__extra">{extraFields}</div>}

      <div
        className={`dropzone ${isDragging ? 'dropzone--active' : ''} ${uploading ? 'dropzone--busy' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
        }}
      >
        <input
          ref={inputRef}
          type="file"
          onChange={handleSelect}
          disabled={uploading}
          hidden
        />
        {uploading ? (
          <p className="dropzone__text">enviando…</p>
        ) : (
          <>
            <p className="dropzone__text">Arraste um arquivo aqui</p>
            <p className="dropzone__subtext">ou clique para selecionar</p>
          </>
        )}
      </div>

      {feedback && (
        <p className={`feedback feedback--${feedback.type}`}>{feedback.text}</p>
      )}
    </div>
  )
}
