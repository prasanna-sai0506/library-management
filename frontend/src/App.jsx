import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, CheckCircle2, ChevronRight, Clock3, Library, LogOut, Menu, Search, ShieldCheck, Sparkles, UserRound, X } from 'lucide-react'
import { api, auth } from './api'

function isLibraryStaff(user) {
  return user?.is_staff || user?.role === 'LIBRARIAN'
}

function useSession() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(auth.access))
  useEffect(() => {
    const tokenAtStart = auth.access
    if (!tokenAtStart) {
      setLoading(false)
      return undefined
    }
    let active = true
    api.profile().then(profile => {
      if (active && auth.access === tokenAtStart) setUser(profile)
    }).catch(() => {
      if (active && auth.access === tokenAtStart) {
        auth.clear()
        setUser(null)
      }
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [])
  return { user, setUser, loading }
}

function Layout({ user, onLogout, children }) {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const links = user ? [['/dashboard', 'Overview'], ['/catalog', 'Browse books'], ['/borrowings', isLibraryStaff(user) ? 'Borrowings' : 'My borrowings']] : []
  return <div className="app-shell">
    <header className="topbar">
      <Link to="/" className="brand"><span className="brand-mark"><Library size={19} /></span><span>haven<span className="brand-dot">.</span></span></Link>
      <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle navigation">{open ? <X /> : <Menu />}</button>
      <nav className={open ? 'nav-links is-open' : 'nav-links'}>
        {links.map(([href, label]) => <Link className={location.pathname === href ? 'active' : ''} onClick={() => setOpen(false)} to={href} key={href}>{label}</Link>)}
        {user ? <><Link className="user-link" to="/profile"><UserRound size={16} /> {user.username}</Link><button className="button button-quiet" onClick={onLogout}><LogOut size={16} /> Log out</button></> : <><Link to="/login" onClick={() => setOpen(false)}>Sign in</Link><Link className="button button-dark" to="/register">Join Haven <ArrowRight size={16} /></Link></>}
      </nav>
    </header>
    {children}
    <footer className="footer"><div className="brand"><span className="brand-mark"><Library size={17} /></span><span>haven<span className="brand-dot">.</span></span></div><span>Thoughtful reading, made simple.</span><span>© 2026 Haven Library</span></footer>
  </div>
}

function Home() {
  return <main>
    <section className="hero">
      <div className="hero-copy"><p className="eyebrow"><Sparkles size={15} /> A calmer way to read</p><h1>Find your next<br /><em>good story.</em></h1><p className="hero-text">A considered collection of books, ready when you are. Borrow thoughtfully, read deeply, and keep your curiosity moving.</p><div className="hero-actions"><Link className="button button-dark button-large" to="/register">Explore the collection <ArrowRight size={17} /></Link><Link className="text-link" to="/login">Already a member? Sign in</Link></div><div className="hero-note"><div className="avatar-stack"><span>J</span><span>M</span><span>A</span><span>+</span></div><span>Join a growing community of readers</span></div></div>
      <div className="hero-art"><div className="sun"></div><div className="book-card book-one"><span>ESSAYS<br />ON<br />LIVING</span><small>NO. 04</small></div><div className="book-card book-two"><span>THE<br />QUIET<br />HOUR</span><small>HAVEN EDITION</small></div><div className="leaf leaf-one"></div><div className="leaf leaf-two"></div><div className="art-caption">Slow down.<br />Stay curious.</div></div>
    </section>
    <section className="home-section"><div className="section-heading"><div><p className="eyebrow">The Haven approach</p><h2>More than a library.</h2></div><p>We believe the right book can change the pace of an entire day. Our collection is designed for discovery, not noise.</p></div><div className="feature-grid"><Feature icon={<BookOpen />} number="01" title="Curated shelves" text="A handpicked collection spanning ideas, imagination, and everything in between." /><Feature icon={<Clock3 />} number="02" title="Read at your pace" text="Simple borrowing, clear due dates, and no pressure to rush a good chapter." /><Feature icon={<ShieldCheck />} number="03" title="Made for members" text="Your personal reading space, with every detail kept clear and considered." /></div></section>
    <section className="quote-section"><p>“A room without books is like a body without a soul.”</p><span>— Marcus Tullius Cicero</span></section>
  </main>
}

function Feature({ icon, number, title, text }) { return <article className="feature-card"><div className="feature-top"><span className="feature-icon">{icon}</span><span>{number}</span></div><h3>{title}</h3><p>{text}</p><ChevronRight size={18} className="feature-arrow" /></article> }

function ProfilePage({ user, onUpdated }) {
  const [profile, setProfile] = useState(user)
  const [form, setForm] = useState({ username: user.username, first_name: user.first_name || '', last_name: user.last_name || '', email: user.email || '', password: '' })
  const [history, setHistory] = useState([])
  const [historyPage, setHistoryPage] = useState(1)
  const [historyPages, setHistoryPages] = useState(1)
  const [historyCount, setHistoryCount] = useState(0)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.profile().then(updated => {
      setProfile(updated)
      setForm({ username: updated.username, first_name: updated.first_name || '', last_name: updated.last_name || '', email: updated.email || '', password: '' })
      onUpdated(updated)
    }).catch(e => setMessage(e.message))
  }, [])

  useEffect(() => {
    api.borrowings(`?page=${historyPage}&page_size=8`)
      .then(data => {
        setHistory(Array.isArray(data) ? data : data.results || [])
        setHistoryCount(data.count || (Array.isArray(data) ? data.length : 0))
        setHistoryPages(data.count ? Math.max(1, Math.ceil(data.count / 8)) : 1)
      })
      .catch(e => setMessage(e.message))
  }, [historyPage])

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    const data = { username: form.username, first_name: form.first_name, last_name: form.last_name, email: form.email }
    if (form.password) data.password = form.password
    try {
      const updated = await api.updateProfile(data)
      setProfile(updated)
      onUpdated(updated)
      setForm({ username: updated.username, first_name: updated.first_name || '', last_name: updated.last_name || '', email: updated.email || '', password: '' })
      setMessage('Profile updated successfully.')
    } catch (e) {
      setMessage(e.message)
    } finally {
      setBusy(false)
    }
  }

  return <main className="page"><div className="page-intro"><div><p className="eyebrow">Your account</p><h1>Personal <em>details.</em></h1><p>Update your account information without signing in again.</p></div></div><div className="profile-grid"><section className="panel profile-panel"><div className="panel-heading"><div><p className="eyebrow">Profile</p><h2>{profile.username}</h2></div><span className="role-badge">{isLibraryStaff(profile) ? 'Librarian' : 'Member'}</span></div><form className="profile-form" onSubmit={submit}><label>Username<input required value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /></label><label>First name<input value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} /></label><label>Last name<input value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} /></label><label>Email address<input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label>New password<input type="password" minLength="8" placeholder="Leave blank to keep current password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label><div className="profile-readonly"><span>Role: {profile.role}</span><span>Credits: {profile.credits}</span><span>Total spent: {profile.total_credits_spent || '0.00'}</span></div><button disabled={busy} className="button button-dark">{busy ? 'Saving…' : 'Save changes'} <ArrowRight size={15} /></button></form>{message && <p className={message.includes('successfully') ? 'success-message' : 'form-error'}>{message}</p>}</section><section className="panel credit-history"><div className="panel-heading"><div><p className="eyebrow">Credit activity</p><h2>Spending history</h2></div><span className="user-credits">{profile.total_credits_spent || '0.00'} spent</span></div>{history.length ? <div className="credit-list">{history.map(item => <div className="credit-entry" key={item.id}><div><strong>{item.book_details?.title || 'Book'}</strong><span>Order #{item.id} · {item.borrowed_at ? new Date(item.borrowed_at).toLocaleDateString() : 'Date unavailable'}</span></div><strong>-{item.credits_spent} credits</strong></div>)}</div> : <p className="empty-state">No credit activity yet.</p>}<Pagination page={historyPage} pages={historyPages} onPage={setHistoryPage} /></section></div></main>
}

function AuthPage({ mode, onLogin, onRegister }) {
  const isLogin = mode === 'login'; const navigate = useNavigate(); const [form, setForm] = useState({ username: '', email: '', password: '' }); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(event) { event.preventDefault(); setBusy(true); setError(''); try { if (isLogin) await onLogin(form); else await onRegister(form); navigate('/dashboard') } catch (e) { setError(e.message) } finally { setBusy(false) } }
  return <main className="auth-page"><div className="auth-panel"><p className="eyebrow">{isLogin ? 'Welcome back' : 'Start your membership'}</p><h1>{isLogin ? 'Good to see you.' : 'Make room for a new story.'}</h1><p className="auth-intro">{isLogin ? 'Sign in to pick up where you left off.' : 'Create your Haven account and begin exploring.'}</p><form onSubmit={submit}>{!isLogin && <label>Email address<input type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label>}<label>Username<input required value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /></label><label>Password<input type="password" required minLength="8" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label>{error && <div className="form-error">{error}</div>}<button disabled={busy} className="button button-dark button-full">{busy ? 'Please wait…' : isLogin ? 'Sign in' : 'Create account'} <ArrowRight size={16} /></button></form><p className="auth-switch">{isLogin ? 'New to Haven?' : 'Already a member?'} <Link to={isLogin ? '/register' : '/login'}>{isLogin ? 'Create an account' : 'Sign in'}</Link></p></div><div className="auth-aside"><div className="aside-circle"></div><p>“Reading is a way of saying<br />I am here, I am alive.”</p><span>— Mary Oliver</span></div></main>
}

function Dashboard({ user }) {
  const [borrowings, setBorrowings] = useState([]); const [borrowingError, setBorrowingError] = useState(''); const [books] = useState([]); const [members] = useState([])
  useEffect(() => {
    api.borrowings()
      .then(data => setBorrowings(Array.isArray(data) ? data : data.results || []))
      .catch(error => setBorrowingError(error.message))
  }, [])
  const active = borrowings.filter(item => item.status !== 'RETURNED')
  return <main className="page"><div className="page-intro"><div><p className="eyebrow">Your reading room</p><h1>Good morning, {user.username}.</h1><p>Here’s a little snapshot of your Haven membership.</p></div><Link className="button button-dark" to="/catalog">Find a book <ArrowRight size={16} /></Link></div><div className="stats-grid"><Stat label="Available to borrow" value={books.filter(book => book.availability === 'AVAILABLE').length} icon={<BookOpen />} /><Stat label="No. of books borrowed" value={active.length} icon={<Clock3 />} />{isLibraryStaff(user) ? <Stat label="Total members" value={members.filter(account => account.role === 'MEMBER').length} icon={<UserRound />} /> : <Stat label="Your credits" value={user.credits} icon={<Sparkles />} />}</div><div className="dashboard-grid"><section className="panel"><div className="panel-heading"><div><p className="eyebrow">In progress</p><h2>Current borrowings</h2></div><Link to="/borrowings">View all <ArrowRight size={15} /></Link></div>{borrowingError ? <p className="form-error">{borrowingError}</p> : active.length ? active.slice(0, 3).map(item => <BorrowingRow item={item} key={item.id} />) : <EmptyState text="No books borrowed yet." link="/catalog" label="Browse the collection" />}</section><section className="panel recommendation"><p className="eyebrow">A thought for today</p><h2>“A book is a gift you can open again and again.”</h2><p>Take a moment to find something that meets you where you are.</p><Link className="text-link" to="/catalog">Explore all books <ArrowRight size={15} /></Link></section></div>{isLibraryStaff(user) && <AdminPanel initialUsers={members} initialBooks={books} />}</main>
}

function Stat({ label, value, icon }) { return <div className="stat-card"><span className="stat-icon">{icon}</span><div><strong>{value}</strong><span>{label}</span></div></div> }
function BorrowingRow({ item, onReturn }) {
  const returned = item.status === 'RETURNED'
  const overdue = !returned && new Date(item.due_date) < new Date()
  const statusText = returned
    ? `Returned ${item.returned_at ? new Date(item.returned_at).toLocaleDateString() : ''}`.trim()
    : `${overdue ? 'Overdue · ' : ''}Due ${new Date(item.due_date).toLocaleDateString()}`
  return <div className="borrowing-row"><div className="mini-cover"><BookOpen size={19} /></div><div className="row-info"><strong>{item.book_details?.title || 'Book'}</strong><span>Book #{item.book_details?.id || item.book}</span><small>Order #{item.id}</small></div><span className={`due-date ${returned ? 'returned' : overdue ? 'overdue' : ''}`}>{statusText}</span>{onReturn && <button className="button button-outline" onClick={() => onReturn(item.id)}>Return</button>}</div>
}
function EmptyState({ text, link, label }) { return <div className="empty-state"><p>{text}</p><Link className="text-link" to={link}>{label} <ArrowRight size={15} /></Link></div> }
function Pagination({ page, pages, onPage }) {
  if (pages <= 1) return null
  return <nav className="pagination" aria-label="Pagination">
    <button type="button" className="button button-outline" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
    <span>Page {page} of {pages}</span>
    <button type="button" className="button button-outline" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</button>
  </nav>
}
function AdminPanel({ initialUsers, initialBooks }) {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [users, setUsers] = useState(initialUsers)
  const [selectedUser, setSelectedUser] = useState(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => { setUsers(initialUsers) }, [initialUsers])
  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      await api.createLibrarian(form)
      const updated = await api.users()
      setUsers(Array.isArray(updated) ? updated : updated.results || [])
      setMessage('Librarian account created.')
      setForm({ username: '', email: '', password: '' })
    } catch (e) {
      setMessage(e.message)
    } finally {
      setBusy(false)
    }
  }
  return <><section className="panel admin-panel">
    <div className="panel-heading"><div><p className="eyebrow">Administration</p><h2>Users and librarians</h2></div><ShieldCheck size={20} color="#bc7651" /></div>
    <div className="admin-content">
      <div className="user-list">{users.map(account => <button className={`user-row user-row-button${selectedUser?.id === account.id ? ' selected' : ''}`} key={account.id} onClick={() => setSelectedUser(account)}><div className="user-avatar"><UserRound size={16} /></div><div className="row-info"><strong>{account.username}</strong><span>{account.email || 'No email provided'}</span></div><span className="role-badge">{account.role === 'LIBRARIAN' || account.is_staff ? 'Librarian' : 'Member'}</span><span className="user-credits">{account.credits} credits</span></button>)}</div>
      {selectedUser && <LibrarianUserBorrowings user={selectedUser} />}
    </div>
    <p className="eyebrow add-user-label">Add a librarian</p>
    <form className="admin-form" onSubmit={submit}><input required placeholder="Username" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /><input required type="email" placeholder="Email address" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /><input required minLength="8" type="password" placeholder="Temporary password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /><button disabled={busy} className="button button-dark">{busy ? 'Creating…' : 'Create account'} <ArrowRight size={15} /></button></form>
    {message && <p className={message.includes('created') ? 'success-message' : 'form-error'}>{message}</p>}
  </section><UnderDeskDesk /><AdminBooks initialBooks={initialBooks} /></>
}

function UnderDeskDesk() {
  const [copies, setCopies] = useState([])
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [count, setCount] = useState(0)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function loadCopies(nextPage = page) {
    try {
      const data = await api.underDesk(`?page=${nextPage}&page_size=10`)
      setCopies(Array.isArray(data) ? data : data.results || [])
      setCount(data.count || (Array.isArray(data) ? data.length : 0))
      setPages(data.count ? Math.max(1, Math.ceil(data.count / 10)) : 1)
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => { loadCopies(page) }, [page])

  async function closeUnderDesk() {
    setBusy(true)
    setMessage('')
    setError('')
    try {
      const result = await api.closeUnderDesk()
      setMessage(result.message)
      setPage(1)
      await loadCopies(1)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return <section className="panel admin-panel under-desk-panel">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">Library desk</p>
        <h2>Under-desk books</h2>
      </div>
      <span className="under-desk-count">{count} waiting</span>
    </div>
    <div className="under-desk-actions">
      <span>Returned copies are kept here until end of day.</span>
      <button className="button button-dark" disabled={busy || count === 0} onClick={closeUnderDesk}>
        {busy ? 'Moving...' : 'Move all to shelf'}
      </button>
    </div>
    {error && <p className="form-error">{error}</p>}
    {message && <p className="success-message">{message}</p>}
    {copies.length ? <div className="under-desk-list">
      {copies.map(copy => <div className="under-desk-row" key={copy.id}>
        <div className="row-info">
          <strong>{copy.title}</strong>
          <span>ISBN {copy.isbn}</span>
        </div>
        <span className="under-desk-borrower">Returned by borrowing #{copy.borrowing}</span>
        <span className="under-desk-time">{new Date(copy.placed_at).toLocaleString()}</span>
      </div>)}
    </div> : !error && <p className="empty-state">No books are currently under the desk.</p>}
    <Pagination page={page} pages={pages} onPage={setPage} />
  </section>
}

function AdminBooks({ initialBooks }) {
  const emptyForm = { title: '', author: '', isbn: '', category: '', shelf_location: '', total_copies: 1, borrowing_cost: '5.00', borrowing_period: 7 }
  const emptyShelfForm = { name: '', capacity: 1 }
  const [shelfSearch, setShelfSearch] = useState('')
  const emptyAssignmentForm = { shelf: '', book: '', copies: 1 }
  const [form, setForm] = useState(emptyForm)
  const [shelfForm, setShelfForm] = useState(emptyShelfForm)
  const [assignmentForm, setAssignmentForm] = useState(emptyAssignmentForm)
  const [books, setBooks] = useState(initialBooks)
  const [shelves, setShelves] = useState([])
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  async function loadBooks() {
    const data = await api.books()
    setBooks(Array.isArray(data) ? data : data.results || [])
  }

  async function loadShelves() {
    const data = await api.shelves()
    setShelves(Array.isArray(data) ? data : [])
  }

  useEffect(() => {
    setBooks(initialBooks)
    loadShelves().catch(e => setMessage(e.message))
  }, [initialBooks])

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      if (form.id) {
        await api.updateBook(form.id, { shelf_location: form.shelf_location })
        setMessage('Shelf location updated.')
      } else {
        await api.createBook({ ...form, total_copies: Number(form.total_copies), borrowing_period: Number(form.borrowing_period) })
        setMessage('Book added to the collection.')
      }
      setForm(emptyForm)
      await loadBooks()
      await loadShelves()
    } catch (e) {
      setMessage(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function createShelf(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      await api.createShelf({
        name: shelfForm.name,
        capacity: Number(shelfForm.capacity),
      })
      setShelfForm(emptyShelfForm)
      await loadShelves()
      setMessage('Shelf created.')
    } catch (e) {
      setMessage(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function assignCopies(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      await api.createShelfAssignment({
        shelf: Number(assignmentForm.shelf),
        book: Number(assignmentForm.book),
        copies: books.find(book => book.id === Number(assignmentForm.book))?.total_copies,
      })
      setAssignmentForm(emptyAssignmentForm)
      await loadShelves()
      await loadBooks()
      setMessage('Copies assigned to shelf.')
    } catch (e) {
      setMessage(e.message)
    } finally {
      setBusy(false)
    }
  }

  return <section className="panel admin-panel">
    <div className="panel-heading"><div><p className="eyebrow">Collection desk</p><h2>Book locations</h2></div><BookOpen size={20} color="#bc7651" /></div>
    <div className="staff-book-list">{books.map(book => <div className="staff-book-row" key={book.id}><div className="row-info"><strong>{book.title}</strong><span>{book.author}</span></div><span className="shelf-label">{book.shelf_location || "Unassigned"} / {book.total_copies} copies</span><button type="button" onClick={() => setForm({ ...book })}>Edit shelf</button></div>)}</div>
    <p className="eyebrow add-user-label">{form.id ? `Update shelf for ${form.title}` : 'Add a book'}</p>
    <form className="admin-form" onSubmit={submit}>
      <input placeholder="Shelf name or ID" value={form.shelf_location} onChange={e => setForm({ ...form, shelf_location: e.target.value })} />
      {!form.id && <><input required placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /><input required placeholder="Author" value={form.author} onChange={e => setForm({ ...form, author: e.target.value })} /><input required placeholder="ISBN" value={form.isbn} onChange={e => setForm({ ...form, isbn: e.target.value })} /><input required placeholder="Category" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} /></>}
      {!form.id && <><input required min="1" type="number" placeholder="Copies" value={form.total_copies} onChange={e => setForm({ ...form, total_copies: e.target.value })} /><input required min="0" step="0.01" type="number" placeholder="Cost" value={form.borrowing_cost} onChange={e => setForm({ ...form, borrowing_cost: e.target.value })} /><input required min="1" type="number" placeholder="Borrowing days" value={form.borrowing_period} onChange={e => setForm({ ...form, borrowing_period: e.target.value })} /></>}
      <button disabled={busy} className="button button-dark">{busy ? 'Saving…' : form.id ? 'Save shelf' : 'Add book'} <ArrowRight size={15} /></button>
    </form>

    <div className="shelf-management">
      <div className="panel-heading shelf-heading"><div><p className="eyebrow">Physical shelves</p><h2>Create shelf</h2></div></div>
      <form className="admin-form shelf-form" onSubmit={createShelf}>
        <input required placeholder="Shelf name or location (e.g. A-12)" value={shelfForm.name} onChange={e => setShelfForm({ ...shelfForm, name: e.target.value })} />
        <input required min="1" type="number" placeholder="Capacity" value={shelfForm.capacity} onChange={e => setShelfForm({ ...shelfForm, capacity: e.target.value })} />
        <button disabled={busy} className="button button-dark">Create shelf <ArrowRight size={15} /></button>
      </form>

      <input aria-label="Search shelves" placeholder="Search shelf name or ID" value={shelfSearch} onChange={e => setShelfSearch(e.target.value)} />
      <p>{shelves.length} shelves. Showing up to 50 matching shelves.</p>
      <div className="shelf-list">
        {shelves.filter(shelf => shelf.name.toLowerCase().includes(shelfSearch.toLowerCase()) || String(shelf.id) === shelfSearch).slice(0, 50).map(shelf => <div className="shelf-row" key={shelf.id}>
          <div className="row-info"><strong>{shelf.name}</strong><span>{shelf.assigned_copies} / {shelf.capacity} copies assigned</span></div>
          <span className="role-badge">{shelf.remaining_capacity} remaining</span>
        </div>)}
      </div>

      <div className="panel-heading shelf-heading"><div><p className="eyebrow">Copy placement</p><h2>Assign books to shelves</h2></div></div>
      <form className="admin-form shelf-form" onSubmit={assignCopies}>
        <select required value={assignmentForm.shelf} onChange={e => setAssignmentForm({ ...assignmentForm, shelf: e.target.value })}>
          <option value="">Choose shelf</option>
          {shelves.filter(shelf => shelf.remaining_capacity > 0).map(shelf => <option value={shelf.id} key={shelf.id}>{shelf.name} ({shelf.remaining_capacity} remaining)</option>)}
        </select>
        <select required value={assignmentForm.book} onChange={e => setAssignmentForm({ ...assignmentForm, book: e.target.value })}>
          <option value="">Choose book</option>
          {books.map(book => <option value={book.id} key={book.id}>{book.title} ({book.total_copies} copies)</option>)}
        </select>
        <p>All copies of the selected book move together.</p>
        <button disabled={busy} className="button button-dark">Assign copies <ArrowRight size={15} /></button>
      </form>
    </div>
    {message && <p className={message.includes('updated') || message.includes('added') ? 'success-message' : 'form-error'}>{message}</p>}
  </section>
}

function LibrarianUserBorrowings({ user }) {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  useEffect(() => { setError(''); api.userBorrowings(user.id).then(data => setItems(Array.isArray(data) ? data : data.results || [])).catch(e => setError(e.message)) }, [user.id])
  async function returnBook(id) {
    try {
      await api.returnBook(id)
      setItems(items.map(item => item.id === id ? { ...item, status: 'RETURNED', returned_at: new Date().toISOString() } : item))
    } catch (e) {
      setError(e.message)
    }
  }
  return <div className="selected-user-panel"><div className="panel-heading"><div><p className="eyebrow">Selected member</p><h3>{user.username}’s borrowings</h3></div><span className="user-credits">{user.email || 'No email provided'}</span></div>{error ? <p className="form-error">{error}</p> : items.length ? items.map(item => <BorrowingRow item={item} onReturn={item.status !== 'RETURNED' ? returnBook : null} key={item.id} />) : <p className="empty-state">This user has no borrowing history.</p>}</div>
}

function Catalog({ user }) {
  const [books, setBooks] = useState([])
  const [search, setSearch] = useState('')
  const [submittedSearch, setSubmittedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [count, setCount] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: '9',
    })
    if (submittedSearch) params.set('title', submittedSearch)

    api.books(`?${params.toString()}`)
      .then(data => {
        setBooks(Array.isArray(data) ? data : data.results || [])
        setCount(data.count || (Array.isArray(data) ? data.length : 0))
        setPages(data.count ? Math.max(1, Math.ceil(data.count / 9)) : 1)
      })
      .catch(e => setError(e.message))
  }, [page, submittedSearch])

  function submitSearch(event) {
    event.preventDefault()
    setPage(1)
    setSubmittedSearch(search.trim())
  }

  function clearSearch() {
    setSearch('')
    setSubmittedSearch('')
    setPage(1)
  }

  return <main className="page"><div className="page-intro catalog-intro"><div><p className="eyebrow">The collection</p><h1>Find something<br /><em>worth reading.</em></h1></div><p>Browse our shelves and discover your next favorite book. Search by title, author, or subject.</p></div><form className="search-bar" onSubmit={submitSearch}><Search size={19} /><input placeholder="Search by title…" value={search} onChange={e => setSearch(e.target.value)} />{search && <button className="search-clear" type="button" aria-label="Clear search" onClick={clearSearch}><X size={16} /></button>}<button className="search-submit" type="submit">Search</button></form>{error ? <div className="form-error">{error}</div> : <div className="book-grid">{books.map(book => <BookCard book={book} canBorrow={user.role === 'MEMBER' && !user.is_staff} key={book.id} />)}</div>}{!count && !error && <div className="empty-state"><p>No books match your search.</p>{submittedSearch && <button className="button button-outline" type="button" onClick={clearSearch}>Clear search</button>}</div>}<Pagination page={page} pages={pages} onPage={setPage} /></main>
}
function BookCard({ book, canBorrow }) {
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [showBorrowModal, setShowBorrowModal] = useState(false)
  const [borrowingPeriod, setBorrowingPeriod] = useState(book.borrowing_period || 7)
  async function borrow() {
    setBusy(true)
    try {
      await api.borrow(book.id, borrowingPeriod)
      setMessage('Borrowed!')
      setShowBorrowModal(false)
    } catch (e) {
      setMessage(e.message)
    } finally {
      setBusy(false)
    }
  }
  return <><article className="book-tile"><div className={`cover cover-${book.id % 4}`}><span>{book.title}</span><small>{book.category}</small></div><div className="book-details"><div><span className="book-category">{book.category}</span><h3>{book.title}</h3><p>{book.author}</p>{book.shelf_location !== undefined && <span className="shelf-location">Shelf {book.shelf_location || 'not assigned'}</span>}</div><div className="book-meta"><span>{book.borrowing_period} days default</span><span>{book.borrowing_cost} credits</span></div>{canBorrow ? <button disabled={busy || book.availability !== 'AVAILABLE' || Boolean(message === 'Borrowed!')} className="button button-dark button-full" onClick={() => setShowBorrowModal(true)}>{message || (book.availability === 'AVAILABLE' ? 'Borrow book' : 'Currently unavailable')}</button> : <span className="book-note">Members can borrow this book</span>}{message && message !== 'Borrowed!' && <small className="inline-error">{message}</small>}</div></article>{showBorrowModal && <div className="modal-backdrop" onClick={() => setShowBorrowModal(false)}><div className="borrow-modal" onClick={event => event.stopPropagation()}><button className="modal-close" onClick={() => setShowBorrowModal(false)} aria-label="Close">×</button><p className="eyebrow">Borrow this book</p><h2>{book.title}</h2><p>Choose how many days you want to keep it.</p><label>Borrowing period (days)<input autoFocus type="number" min="1" value={borrowingPeriod} onChange={e => setBorrowingPeriod(e.target.value)} /></label><div className="modal-actions"><button className="button button-outline" onClick={() => setShowBorrowModal(false)}>Cancel</button><button className="button button-dark" disabled={busy} onClick={borrow}>{busy ? 'Borrowing…' : 'Confirm borrowing'}</button></div></div></div>}</>
}

function Borrowings({ user }) { const [items, setItems] = useState([]); const [error, setError] = useState(''); const isLibrarian = isLibraryStaff(user); useEffect(() => { api.borrowings().then(data => setItems(Array.isArray(data) ? data : data.results || [])).catch(e => setError(e.message)) }, []); async function returnBook(id) { try { await api.returnBook(id); setItems(items.map(item => item.id === id ? { ...item, status: 'RETURNED', returned_at: new Date().toISOString() } : item)) } catch (e) { setError(e.message) } } return <main className="page"><div className="page-intro"><div><p className="eyebrow">{isLibrarian ? 'Library desk' : 'Your history'}</p><h1>{isLibrarian ? <>All <em>borrowings.</em></> : <>Books you’ve<br /><em>taken with you.</em></>}</h1></div><p>{isLibrarian ? 'Review every member’s borrowing record and check books in when they are returned.' : 'A record of your current reads and everything you’ve returned to the shelves.'}</p></div>{error && <div className="form-error">{error}</div>}<section className="panel history-panel">{items.length ? items.map(item => <BorrowingRow item={item} onReturn={isLibrarian && item.status !== 'RETURNED' ? returnBook : null} key={item.id} />) : <EmptyState text="No borrowing records found." link="/catalog" label="Browse the collection" />}</section></main> }

function App() { const session = useSession(); const navigate = useNavigate(); function logout() { auth.clear(); session.setUser(null); navigate('/login', { replace: true }) } async function login(data) { auth.clear(); session.setUser(null); const tokens = await api.login(data); auth.save(tokens); const profile = await api.profile(); if (auth.access === tokens.access) session.setUser(profile) } async function register(data) { auth.clear(); await api.register(data); await login({ username: data.username, password: data.password }) } if (session.loading) return <div className="loading-screen">Opening Haven…</div>; return <Layout user={session.user} onLogout={logout}><Routes><Route path="/" element={<Home />} /><Route path="/login" element={session.user ? <Navigate to="/dashboard" /> : <AuthPage mode="login" onLogin={login} />} /><Route path="/register" element={session.user ? <Navigate to="/dashboard" /> : <AuthPage mode="register" onRegister={register} />} /><Route path="/dashboard" element={session.user ? <Dashboard user={session.user} /> : <Navigate to="/login" />} /><Route path="/catalog" element={session.user ? <Catalog user={session.user} /> : <Navigate to="/login" />} /><Route path="/borrowings" element={session.user ? <Borrowings user={session.user} /> : <Navigate to="/login" />} /><Route path="/profile" element={session.user ? <ProfilePage user={session.user} onUpdated={session.setUser} /> : <Navigate to="/login" />} /><Route path="*" element={<Navigate to="/" />} /></Routes></Layout> }

export default App
