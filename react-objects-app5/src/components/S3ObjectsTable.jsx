function formatBytes(bytes) {
  if (bytes == null) return '—'
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let value = bytes
  let unitIndex = -1
  do {
    value /= 1024
    unitIndex += 1
  } while (value >= 1024 && unitIndex < units.length - 1)
  return `${value.toFixed(1)} ${units[unitIndex]}`
}

function formatDate(isoString) {
  if (!isoString) return '—'
  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return isoString
  return date.toLocaleString('pt-BR')
}

export function S3ObjectsTable({ objects, loading, deletingKey, onDelete }) {
  return (
    <div className="panel">
      <div className="panel__header">
        <h2>Objetos</h2>
        <span className="panel__hint">GET · DELETE /s3</span>
      </div>

      {loading && objects.length === 0 ? (
        <p className="empty-state">carregando…</p>
      ) : objects.length === 0 ? (
        <p className="empty-state">Nenhum objeto encontrado no bucket.</p>
      ) : (
        <table className="objects-table">
          <thead>
            <tr>
              <th>chave</th>
              <th>tamanho</th>
              <th>modificado em</th>
              <th aria-label="acoes" />
            </tr>
          </thead>
          <tbody>
            {objects.map((obj) => (
              <tr key={obj.chave}>
                <td className="objects-table__name" title={obj.chave}>
                  {obj.chave}
                </td>
                <td className="objects-table__muted">{formatBytes(obj.tamanhoBytes)}</td>
                <td className="objects-table__muted">{formatDate(obj.ultimaModificacao)}</td>
                <td>
                  <button
                    className="btn btn--danger"
                    onClick={() => onDelete(obj.chave)}
                    disabled={deletingKey === obj.chave}
                  >
                    {deletingKey === obj.chave ? 'removendo…' : 'remover'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
