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
  updateProfile: (data) => request('/auth/users/profile/', { method: 'PATCH', body: JSON.stringify(data) }),
  books: (query = '') => request(`/library/books/${query}`),
  createBook: (data) => request('/library/books/', { method: 'POST', body: JSON.stringify(data) }),
  updateBook: (id, data) => request(`/library/books/?id=${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  borrowings: () => request('/api/borrowings/'),
  borrow: (book, borrowingPeriod) => request('/api/borrowings/', { method: 'POST', body: JSON.stringify({ book, borrowing_period: Number(borrowingPeriod) }) }),
  returnBook: (id) => request(`/api/borrowings/return/?id=${id}`, { method: 'POST' }),
  createLibrarian: (data) => request('/auth/users/create-librarian/', { method: 'POST', body: JSON.stringify(data) }),
  users: () => request('/auth/users/users-list/'),
  user: (id) => request(`/auth/users/users-list/${id}/`),
  userBorrowings: (id) => request(`/auth/users/users-list/borrowings/?user_id=${id}`),
}
