import { useEffect } from 'react'

export function PreviewModal({ preview, onClose }) {
  useEffect(() => {
    if (!preview) return
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [preview, onClose])

  if (!preview) return null

  return (
    <div className="preview-overlay" onClick={onClose}>
      <div className="preview-modal" onClick={(e) => e.stopPropagation()}>
        <div className="preview-modal__header">
          <span className="preview-modal__name">{preview.nome}</span>
          <button className="preview-modal__close" onClick={onClose} aria-label="Fechar">
            ✕
          </button>
        </div>
        <img src={preview.url} alt={preview.nome} className="preview-modal__image" />
      </div>
    </div>
  )
}
