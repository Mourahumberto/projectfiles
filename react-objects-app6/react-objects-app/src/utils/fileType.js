const IMAGE_EXTENSIONS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'avif'])

const CATEGORY_BY_EXT = {
  pdf: { label: 'PDF', className: 'file-thumb--pdf' },
  zip: { label: 'ZIP', className: 'file-thumb--archive' },
  tar: { label: 'TAR', className: 'file-thumb--archive' },
  gz: { label: 'GZ', className: 'file-thumb--archive' },
  rar: { label: 'RAR', className: 'file-thumb--archive' },
  '7z': { label: '7Z', className: 'file-thumb--archive' },
  doc: { label: 'DOC', className: 'file-thumb--doc' },
  docx: { label: 'DOC', className: 'file-thumb--doc' },
  xls: { label: 'XLS', className: 'file-thumb--doc' },
  xlsx: { label: 'XLS', className: 'file-thumb--doc' },
  ppt: { label: 'PPT', className: 'file-thumb--doc' },
  pptx: { label: 'PPT', className: 'file-thumb--doc' },
  csv: { label: 'CSV', className: 'file-thumb--data' },
  json: { label: 'JSON', className: 'file-thumb--data' },
  txt: { label: 'TXT', className: 'file-thumb--text' },
  md: { label: 'MD', className: 'file-thumb--text' },
  log: { label: 'LOG', className: 'file-thumb--text' },
  sh: { label: 'SH', className: 'file-thumb--code' },
  py: { label: 'PY', className: 'file-thumb--code' },
  js: { label: 'JS', className: 'file-thumb--code' },
  ts: { label: 'TS', className: 'file-thumb--code' },
  yml: { label: 'YML', className: 'file-thumb--code' },
  yaml: { label: 'YML', className: 'file-thumb--code' },
  xml: { label: 'XML', className: 'file-thumb--code' },
}

export function getExtension(nome) {
  if (!nome) return ''
  const parts = nome.split('.')
  if (parts.length < 2) return ''
  return parts.pop().toLowerCase()
}

export function isImageFile(nome) {
  return IMAGE_EXTENSIONS.has(getExtension(nome))
}

export function getFileCategory(nome) {
  const ext = getExtension(nome)
  return CATEGORY_BY_EXT[ext] || { label: ext ? ext.slice(0, 4).toUpperCase() : '?', className: 'file-thumb--generic' }
}
