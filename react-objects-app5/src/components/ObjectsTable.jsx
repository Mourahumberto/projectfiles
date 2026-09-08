import { getDownloadUrl } from '../api/objectsService'

const TYPE_LABEL = {
  arquivo: 'arquivo',
  pasta: 'pasta',
}

export function ObjectsTable({ objects, loading, deletingPath, onDelete }) {
  return (
    <div className="panel">
      <div className="panel__header">
        <h2>Objetos</h2>
        <span className="panel__hint">GET · DELETE /local/objects</span>
      </div>

      {loading && objects.length === 0 ? (
        <p className="empty-state">carregando…</p>
      ) : objects.length === 0 ? (
        <p className="empty-state">Nada por aqui. Envie um arquivo para comecar.</p>
      ) : (
        <table className="objects-table">
          <thead>
            <tr>
              <th>tipo</th>
              <th>nome</th>
              <th aria-label="acoes" />
            </tr>
          </thead>
          <tbody>
            {objects.map((obj) => (
              <tr key={`${obj.tipo}-${obj.caminho}`}>
                <td>
                  <span className={`type-tag type-tag--${obj.tipo}`}>
                    {TYPE_LABEL[obj.tipo] || obj.tipo}
                  </span>
                </td>
                <td className="objects-table__name" title={obj.caminho}>
                  {obj.nome}
                </td>
                <td>
                  {obj.tipo === 'arquivo' ? (
                    <div className="row-actions">
                      <a
                        className="btn btn--ghost"
                        href={getDownloadUrl(obj.nome)}
                        download={obj.nome}
                        target="_blank"
                        rel="noreferrer"
                      >
                        baixar
                      </a>
                      <button
                        className="btn btn--danger"
                        onClick={() => onDelete(obj.nome)}
                        disabled={deletingPath === obj.nome}
                      >
                        {deletingPath === obj.nome ? 'removendo…' : 'remover'}
                      </button>
                    </div>
                  ) : (
                    <span className="objects-table__muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
