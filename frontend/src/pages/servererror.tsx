export default function ServerError() {
  return (
    <div className="error-page">
      <div className="error-content">
        <span className="error-code">500</span>
        <h1 className="error-title">Server Error</h1>
        <p className="error-subtitle">Something went wrong on our end. Please try again later.</p>
        <button className="btn-primary" onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    </div>
  )
}