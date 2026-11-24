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
  login: (credentials) => request('/auth/login/', { method: 'POST', body: JSON.stringify(credentials) }),
  register: (data) => request('/users/register/', { method: 'POST', body: JSON.stringify(data) }),
  profile: () => request('/users/profile/'),
  updateProfile: (data) => request('/users/profile/', { method: 'PATCH', body: JSON.stringify(data) }),
  books: (query = '') => request(`/library/books/${query}`),
  createBook: (data) => request('/library/books/', { method: 'POST', body: JSON.stringify(data) }),
  updateBook: (id, data) => request(`/library/books/?id=${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  shelves: (query = '') => request(`/library/shelves/${query}`),
  packShelves: () => request('/library/shelves/pack/', { method: 'POST' }),
  createShelf: (data) => request('/library/shelves/', { method: 'POST', body: JSON.stringify(data) }),
  updateShelf: (id, data) => request(`/library/shelves/?id=${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteShelf: (id) => request(`/library/shelves/?id=${id}`, { method: 'DELETE' }),
  shelfAssignments: (query = '') => request(`/library/shelf-assignments/${query}`),
  createShelfAssignment: (data) => request('/library/shelf-assignments/', { method: 'POST', body: JSON.stringify(data) }),
  updateShelfAssignment: (id, data) => request(`/library/shelf-assignments/?id=${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteShelfAssignment: (id) => request(`/library/shelf-assignments/?id=${id}`, { method: 'DELETE' }),
  borrowings: (query = '') => request(`/borrowings/${query}`),
  borrow: (book, borrowingPeriod) => request('/borrowings/', { method: 'POST', body: JSON.stringify({ book, borrowing_period: Number(borrowingPeriod) }) }),
  returnBook: (id) => request(`/borrowings/return/?id=${id}`, { method: 'POST' }),
  closeUnderDesk: () => request('/borrowings/under-desk/close/', { method: 'POST' }),
  underDesk: (query = '') => request(`/borrowings/under-desk/${query}`),
  createLibrarian: (data) => request('/users/create-librarian/', { method: 'POST', body: JSON.stringify(data) }),
  users: () => request('/users/userslist/'),
  userBorrowings: (id) => request(`/borrowings/?user_id=${id}`),
}
