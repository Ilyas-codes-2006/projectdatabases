import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

type AdminUser = {
  id: number
  first_name: string
  last_name: string
  email: string
  date_of_birth: string
  created_at: string
}

interface Props {
  setMessage: (msg: { text: string; type: 'error' | 'success' } | null) => void
}

export default function AdminPage({ setMessage }: Props) {
  const navigate = useNavigate()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const isAdmin = localStorage.getItem('is_admin') === 'true'
    if (!isAdmin) {
      navigate('/')
      return
    }
    fetchUsers()
  }, [navigate])

  const fetchUsers = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const res = await fetch('/api/admin/users', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      })
      const data = await res.json()
      if (res.ok) {
        setUsers(data)
      } else {
        setMessage({ text: data.error || 'Kon gebruikers niet laden', type: 'error' })
      }
    } catch {
      setMessage({ text: 'Kan geen verbinding maken met de server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="admin-wrapper">
      <div className="admin-container">
        <div className="admin-header">
          <h1>Admin Dashboard</h1>
          <p>Manage registered users</p>
        </div>

        <div className="admin-card">
          <div className="admin-card-header">
            <h2>Users</h2>
            <p>
              {loading
                ? 'Loading…'
                : `${users.length} registered user${users.length !== 1 ? 's' : ''}`}
            </p>
          </div>

          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Email</th>
                  <th>Date of Birth</th>
                  <th>Created At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {users.length > 0 ? (
                  users.map((user) => (
                    <tr key={user.id}>
                      <td>{user.first_name}</td>
                      <td>{user.last_name}</td>
                      <td>{user.email}</td>
                      <td>{new Date(user.date_of_birth).toLocaleDateString()}</td>
                      <td>{new Date(user.created_at).toLocaleDateString()}</td>
                      <td>
                        <button
                          className="edit-btn"
                          onClick={() => alert('Edit user ' + user.id)}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="empty-cell">
                      {loading ? 'Loading users…' : 'No users found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}