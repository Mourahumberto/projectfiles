import { useState } from 'react'
import { isImageFile, getFileCategory } from '../utils/fileType'

export function FileThumb({ nome, previewUrl, onOpenPreview }) {
  const [imageFailed, setImageFailed] = useState(false)
  const showImage = previewUrl && isImageFile(nome) && !imageFailed

  if (showImage) {
    return (
      <button
        type="button"
        className="file-thumb file-thumb--image"
        onClick={() => onOpenPreview?.({ url: previewUrl, nome })}
        title={`Ver ${nome} em tamanho maior`}
      >
        <img src={previewUrl} alt={nome} loading="lazy" onError={() => setImageFailed(true)} />
      </button>
    )
  }

  const { label, className } = getFileCategory(nome)
  return (
    <div className={`file-thumb file-thumb--icon ${className}`} aria-hidden="true">
      {label}
    </div>
  )
}
