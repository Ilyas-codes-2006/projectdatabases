export default function NotFound() {
  return (
    <div className="error-page">
      <div className="error-content">
        <span className="error-code">404</span>
        <h1 className="error-title">Page Not Found</h1>
        <p className="error-subtitle">The page you're looking for doesn't exist or has been moved.</p>
        <button className="btn-primary" onClick={() => window.location.href = '/'}>
          Back to Home
        </button>
      </div>
    </div>
  )
}