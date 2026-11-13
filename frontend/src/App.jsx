import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, CheckCircle2, ChevronRight, Clock3, Library, LogOut, Menu, Search, ShieldCheck, Sparkles, UserRound, X } from 'lucide-react'
import { api, auth } from './api'

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
  const links = user ? [['/dashboard', 'Overview'], ['/catalog', 'Browse books'], ['/borrowings', user.role === 'ADMIN' ? 'Borrowings' : 'My borrowings']] : []
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

function AuthPage({ mode, onLogin, onRegister }) {
  const isLogin = mode === 'login'; const navigate = useNavigate(); const [form, setForm] = useState({ username: '', email: '', password: '' }); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(event) { event.preventDefault(); setBusy(true); setError(''); try { if (isLogin) await onLogin(form); else await onRegister(form); navigate('/dashboard') } catch (e) { setError(e.message) } finally { setBusy(false) } }
  return <main className="auth-page"><div className="auth-panel"><p className="eyebrow">{isLogin ? 'Welcome back' : 'Start your membership'}</p><h1>{isLogin ? 'Good to see you.' : 'Make room for a new story.'}</h1><p className="auth-intro">{isLogin ? 'Sign in to pick up where you left off.' : 'Create your Haven account and begin exploring.'}</p><form onSubmit={submit}>{!isLogin && <label>Email address<input type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label>}<label>Username<input required value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /></label><label>Password<input type="password" required minLength="8" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label>{error && <div className="form-error">{error}</div>}<button disabled={busy} className="button button-dark button-full">{busy ? 'Please wait…' : isLogin ? 'Sign in' : 'Create account'} <ArrowRight size={16} /></button></form><p className="auth-switch">{isLogin ? 'New to Haven?' : 'Already a member?'} <Link to={isLogin ? '/register' : '/login'}>{isLogin ? 'Create an account' : 'Sign in'}</Link></p></div><div className="auth-aside"><div className="aside-circle"></div><p>“Reading is a way of saying<br />I am here, I am alive.”</p><span>— Mary Oliver</span></div></main>
}

function Dashboard({ user }) {
  const [borrowings, setBorrowings] = useState([]); const [books, setBooks] = useState([]); const [members, setMembers] = useState([])
  useEffect(() => { Promise.all([api.borrowings(), api.books(), user.role === 'ADMIN' ? api.users() : Promise.resolve([])]).then(([b, booksData, usersData]) => { setBorrowings(Array.isArray(b) ? b : b.results || []); setBooks(Array.isArray(booksData) ? booksData : booksData.results || []); setMembers(Array.isArray(usersData) ? usersData : usersData.results || []) }) }, [user.role])
  const active = borrowings.filter(item => item.status !== 'RETURNED')
  return <main className="page"><div className="page-intro"><div><p className="eyebrow">Your reading room</p><h1>Good morning, {user.username}.</h1><p>Here’s a little snapshot of your Haven membership.</p></div><Link className="button button-dark" to="/catalog">Find a book <ArrowRight size={16} /></Link></div><div className="stats-grid"><Stat label="Available to borrow" value={books.filter(book => book.availability === 'AVAILABLE').length} icon={<BookOpen />} /><Stat label="No. of books borrowed" value={active.length} icon={<Clock3 />} />{user.role === 'ADMIN' ? <Stat label="Total members" value={members.filter(account => account.role === 'MEMBER').length} icon={<UserRound />} /> : <Stat label="Your credits" value={user.credits} icon={<Sparkles />} />}</div><div className="dashboard-grid"><section className="panel"><div className="panel-heading"><div><p className="eyebrow">In progress</p><h2>Current borrowings</h2></div><Link to="/borrowings">View all <ArrowRight size={15} /></Link></div>{active.length ? active.slice(0, 3).map(item => <BorrowingRow item={item} key={item.id} />) : <EmptyState text="No books borrowed yet." link="/catalog" label="Browse the collection" />}</section><section className="panel recommendation"><p className="eyebrow">A thought for today</p><h2>“A book is a gift you can open again and again.”</h2><p>Take a moment to find something that meets you where you are.</p><Link className="text-link" to="/catalog">Explore all books <ArrowRight size={15} /></Link></section></div>{user.role === 'ADMIN' && <AdminPanel />}</main>
}

function Stat({ label, value, icon }) { return <div className="stat-card"><span className="stat-icon">{icon}</span><div><strong>{value}</strong><span>{label}</span></div></div> }
function BorrowingRow({ item, onReturn }) {
  const returned = item.status === 'RETURNED'
  const overdue = !returned && new Date(item.due_date) < new Date()
  const statusText = returned
    ? `Returned ${item.returned_at ? new Date(item.returned_at).toLocaleDateString() : ''}`.trim()
    : `${overdue ? 'Overdue · ' : ''}Due ${new Date(item.due_date).toLocaleDateString()}`
  return <div className="borrowing-row"><div className="mini-cover"><BookOpen size={19} /></div><div className="row-info"><strong>{item.book_details?.title || 'Book'}</strong><span>{item.book_details?.author || 'Unknown author'}</span></div><span className={`due-date ${returned ? 'returned' : overdue ? 'overdue' : ''}`}>{statusText}</span>{onReturn && <button className="button button-outline" onClick={() => onReturn(item.id)}>Return</button>}</div>
}
function EmptyState({ text, link, label }) { return <div className="empty-state"><p>{text}</p><Link className="text-link" to={link}>{label} <ArrowRight size={15} /></Link></div> }
function AdminPanel() {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [users, setUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => { api.users().then(data => setUsers(Array.isArray(data) ? data : data.results || [])).catch(e => setMessage(e.message)) }, [])
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
  return <section className="panel admin-panel">
    <div className="panel-heading"><div><p className="eyebrow">Administration</p><h2>Users and librarians</h2></div><ShieldCheck size={20} color="#bc7651" /></div>
    <div className="admin-content">
      <div className="user-list">{users.map(account => <button className={`user-row user-row-button${selectedUser?.id === account.id ? ' selected' : ''}`} key={account.id} onClick={() => setSelectedUser(account)}><div className="user-avatar"><UserRound size={16} /></div><div className="row-info"><strong>{account.username}</strong><span>{account.email || 'No email provided'}</span></div><span className="role-badge">{account.role === 'ADMIN' || account.is_staff ? 'Admin' : 'Member'}</span><span className="user-credits">{account.credits} credits</span></button>)}</div>
      {selectedUser && <AdminUserBorrowings user={selectedUser} />}
    </div>
    <p className="eyebrow add-user-label">Add a librarian</p>
    <form className="admin-form" onSubmit={submit}><input required placeholder="Username" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /><input required type="email" placeholder="Email address" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /><input required minLength="8" type="password" placeholder="Temporary password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /><button disabled={busy} className="button button-dark">{busy ? 'Creating…' : 'Create account'} <ArrowRight size={15} /></button></form>
    {message && <p className={message.includes('created') ? 'success-message' : 'form-error'}>{message}</p>}
  </section>
}

function AdminUserBorrowings({ user }) {
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
  const [books, setBooks] = useState([]); const [search, setSearch] = useState(''); const [error, setError] = useState('')
  useEffect(() => { api.books().then(data => setBooks(Array.isArray(data) ? data : data.results || [])).catch(e => setError(e.message)) }, [])
  const filtered = useMemo(() => books.filter(book => `${book.title} ${book.author} ${book.category}`.toLowerCase().includes(search.toLowerCase())), [books, search])
  return <main className="page"><div className="page-intro catalog-intro"><div><p className="eyebrow">The collection</p><h1>Find something<br /><em>worth reading.</em></h1></div><p>Browse our shelves and discover your next favorite book. Search by title, author, or subject.</p></div><div className="search-bar"><Search size={19} /><input placeholder="Search the collection…" value={search} onChange={e => setSearch(e.target.value)} /></div>{error ? <div className="form-error">{error}</div> : <div className="book-grid">{filtered.map(book => <BookCard book={book} canBorrow={user.role === 'MEMBER' && !user.is_staff} key={book.id} />)}</div>}{!filtered.length && !error && <EmptyState text="No books match your search." link="/catalog" label="Clear search" />}</main>
}
function BookCard({ book, canBorrow }) { const [busy, setBusy] = useState(false); const [message, setMessage] = useState(''); async function borrow() { setBusy(true); try { await api.borrow(book.id); setMessage('Borrowed!'); } catch (e) { setMessage(e.message) } finally { setBusy(false) } } return <article className="book-tile"><div className={`cover cover-${book.id % 4}`}><span>{book.title}</span><small>{book.category}</small></div><div className="book-details"><div><span className="book-category">{book.category}</span><h3>{book.title}</h3><p>{book.author}</p></div><div className="book-meta"><span>{book.borrowing_period} days</span><span>{book.borrowing_cost} credits</span></div>{canBorrow ? <button disabled={busy || book.availability !== 'AVAILABLE' || Boolean(message === 'Borrowed!')} className="button button-dark button-full" onClick={borrow}>{message || (book.availability === 'AVAILABLE' ? 'Borrow book' : 'Currently unavailable')}</button> : <span className="book-note">Members can borrow this book</span>}{message && message !== 'Borrowed!' && <small className="inline-error">{message}</small>}</div></article> }

function Borrowings({ user }) { const [items, setItems] = useState([]); const [error, setError] = useState(''); const isAdmin = user?.role === 'ADMIN'; useEffect(() => { api.borrowings().then(data => setItems(Array.isArray(data) ? data : data.results || [])).catch(e => setError(e.message)) }, []); async function returnBook(id) { try { await api.returnBook(id); setItems(items.map(item => item.id === id ? { ...item, status: 'RETURNED', returned_at: new Date().toISOString() } : item)) } catch (e) { setError(e.message) } } return <main className="page"><div className="page-intro"><div><p className="eyebrow">{isAdmin ? 'Library desk' : 'Your history'}</p><h1>{isAdmin ? <>All <em>borrowings.</em></> : <>Books you’ve<br /><em>taken with you.</em></>}</h1></div><p>{isAdmin ? 'Review every member’s borrowing record and check books in when they are returned.' : 'A record of your current reads and everything you’ve returned to the shelves.'}</p></div>{error && <div className="form-error">{error}</div>}<section className="panel history-panel">{items.length ? items.map(item => <BorrowingRow item={item} onReturn={isAdmin && item.status !== 'RETURNED' ? returnBook : null} key={item.id} />) : <EmptyState text="No borrowing records found." link="/catalog" label="Browse the collection" />}</section></main> }

function App() { const session = useSession(); const navigate = useNavigate(); function logout() { auth.clear(); session.setUser(null); navigate('/login', { replace: true }) } async function login(data) { auth.clear(); session.setUser(null); const tokens = await api.login(data); auth.save(tokens); const profile = await api.profile(); if (auth.access === tokens.access) session.setUser(profile) } async function register(data) { auth.clear(); await api.register(data); await login({ username: data.username, password: data.password }) } if (session.loading) return <div className="loading-screen">Opening Haven…</div>; return <Layout user={session.user} onLogout={logout}><Routes><Route path="/" element={<Home />} /><Route path="/login" element={session.user ? <Navigate to="/dashboard" /> : <AuthPage mode="login" onLogin={login} />} /><Route path="/register" element={session.user ? <Navigate to="/dashboard" /> : <AuthPage mode="register" onRegister={register} />} /><Route path="/dashboard" element={session.user ? <Dashboard user={session.user} /> : <Navigate to="/login" />} /><Route path="/catalog" element={session.user ? <Catalog user={session.user} /> : <Navigate to="/login" />} /><Route path="/borrowings" element={session.user ? <Borrowings user={session.user} /> : <Navigate to="/login" />} /><Route path="*" element={<Navigate to="/" />} /></Routes></Layout> }

export default App
