export default function BadGateway() {
  return (
    <div className="error-page">
      <div className="error-content">
        <span className="error-code">502</span>
        <h1 className="error-title">Bad Gateway</h1>
        <p className="error-subtitle">The server is temporarily unavailable. Please try again in a moment.</p>
        <button className="btn-primary" onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    </div>
  )
}