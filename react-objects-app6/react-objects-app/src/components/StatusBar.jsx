export function StatusBar({ baseUrl, path, rightText, loading, loadingText = 'sincronizando…' }) {
  return (
    <div className="status-bar">
      <span className="status-bar__prompt">
        <span className="status-bar__dot" aria-hidden="true" />
        {baseUrl}
        <span className="status-bar__path">{path}</span>
      </span>
      <span className="status-bar__count">{loading ? loadingText : rightText}</span>
    </div>
  )
}
