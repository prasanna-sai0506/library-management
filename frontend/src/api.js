const ACCESS_KEY = 'haven_access_token'
const REFRESH_KEY = 'haven_refresh_token'

export const auth = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  save(tokens) {
    localStorage.setItem(ACCESS_KEY, tokens.access)
    if (tokens.refresh) localStorage.setItem(REFRESH_KEY, tokens.refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (auth.access) headers.Authorization = `Bearer ${auth.access}`
  const response = await fetch(path, { ...options, headers })
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const message = body?.detail || body?.error || Object.values(body || {})[0]?.[0] || 'Something went wrong.'
    throw new Error(message)
  }
  return body
}

export const api = {
  login: (credentials) => request('/auth/users/login/', { method: 'POST', body: JSON.stringify(credentials) }),
  register: (data) => request('/auth/users/register/', { method: 'POST', body: JSON.stringify(data) }),
  profile: () => request('/auth/users/profile/'),
  books: (query = '') => request(`/library/books/${query}`),
  borrowings: () => request('/lib/borrowings/'),
  borrow: (book) => request('/lib/borrowings/', { method: 'POST', body: JSON.stringify({ book }) }),
  returnBook: (id) => request(`/lib/borrowings/${id}/return/`, { method: 'POST' }),
  createLibrarian: (data) => request('/auth/users/create-admin/', { method: 'POST', body: JSON.stringify(data) }),
  users: () => request('/auth/users/users-list/'),
  user: (id) => request(`/auth/users/users-list/${id}/`),
  userBorrowings: (id) => request(`/auth/users/users-list/${id}/borrowings/`),
}
