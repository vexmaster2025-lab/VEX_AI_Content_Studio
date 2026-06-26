'use client';

import axios from 'axios';
import { FormEvent, useEffect, useMemo, useState } from 'react';

type AuthMode = 'login' | 'register';

type User = {
  id: number;
  email: string;
  full_name?: string | null;
  plan: string;
  subscription_status: string;
  has_active_subscription: boolean;
};

type ContentItem = {
  id: number;
  title: string;
  body: string;
  status: 'draft' | 'published';
  created_at: string;
};

type BillingStatus = {
  plan: string;
  subscription_status: string;
  has_active_subscription: boolean;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [status, setStatus] = useState<'draft' | 'published'>('draft');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const api = useMemo(
    () =>
      axios.create({
        baseURL: API_URL,
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      }),
    [token],
  );

  useEffect(() => {
    const stored = window.localStorage.getItem('vex_token');
    if (stored) setToken(stored);
  }, []);

  useEffect(() => {
    if (!token) return;
    void loadDashboard();
  }, [token]);

  async function loadDashboard() {
    setError('');
    try {
      const [me, items, billingStatus] = await Promise.all([
        api.get<User>('/auth/me'),
        api.get<ContentItem[]>('/content'),
        api.get<BillingStatus>('/billing/status'),
      ]);
      setUser(me.data);
      setContent(items.data);
      setBilling(billingStatus.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to load dashboard');
    }
  }

  async function submitAuth(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      if (authMode === 'register') {
        await axios.post(`${API_URL}/auth/register`, {
          email,
          full_name: fullName || null,
          password,
        });
      }
      const response = await axios.post<{ access_token: string }>(`${API_URL}/auth/login`, { email, password });
      window.localStorage.setItem('vex_token', response.data.access_token);
      setToken(response.data.access_token);
      setPassword('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  }

  async function createContent(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await api.post('/content', { title, body, status });
      setTitle('');
      setBody('');
      setStatus('draft');
      setMessage('Content saved');
      await loadDashboard();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to save content');
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(item: ContentItem, nextStatus: 'draft' | 'published') {
    setError('');
    try {
      await api.patch(`/content/${item.id}`, { status: nextStatus });
      await loadDashboard();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to update content');
    }
  }

  async function deleteContent(item: ContentItem) {
    setError('');
    try {
      await api.delete(`/content/${item.id}`);
      await loadDashboard();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to delete content');
    }
  }

  async function startCheckout(plan: 'go' | 'pro' | 'business') {
    setError('');
    try {
      const response = await api.post<{ checkout_url: string }>('/billing/checkout', { plan });
      window.location.href = response.data.checkout_url;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to start checkout');
    }
  }

  function logout() {
    window.localStorage.removeItem('vex_token');
    setToken(null);
    setUser(null);
    setContent([]);
    setBilling(null);
  }

  if (!token) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <h1>VEX Admin</h1>
          <div className="segmented">
            <button className={authMode === 'login' ? 'active' : ''} onClick={() => setAuthMode('login')} type="button">
              Sign in
            </button>
            <button className={authMode === 'register' ? 'active' : ''} onClick={() => setAuthMode('register')} type="button">
              Register
            </button>
          </div>
          <form onSubmit={submitAuth}>
            <label>
              Email
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
            </label>
            {authMode === 'register' && (
              <label>
                Full name
                <input value={fullName} onChange={(event) => setFullName(event.target.value)} />
              </label>
            )}
            <label>
              Password
              <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required />
            </label>
            {error && <p className="alert error">{error}</p>}
            <button disabled={loading} type="submit">{loading ? 'Working...' : authMode === 'login' ? 'Sign in' : 'Create account'}</button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="container">
      <header className="topbar">
        <div>
          <h1>VEX Admin Dashboard</h1>
          <p>{user?.email}</p>
        </div>
        <button className="secondary" onClick={logout} type="button">Sign out</button>
      </header>

      {error && <p className="alert error">{error}</p>}
      {message && <p className="alert success">{message}</p>}

      <section className="grid">
        <div className="panel">
          <h2>Billing</h2>
          <p className="metric">{billing?.plan || user?.plan || 'free'}</p>
          <p>{billing?.subscription_status || user?.subscription_status || 'inactive'}</p>
          <div className="actions">
            <button onClick={() => startCheckout('go')} type="button">Go</button>
            <button onClick={() => startCheckout('pro')} type="button">Pro</button>
            <button onClick={() => startCheckout('business')} type="button">Business</button>
          </div>
        </div>

        <form className="panel" onSubmit={createContent}>
          <h2>New Content</h2>
          <label>
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} minLength={3} required />
          </label>
          <label>
            Body
            <textarea value={body} onChange={(event) => setBody(event.target.value)} minLength={10} required />
          </label>
          <label>
            Status
            <select value={status} onChange={(event) => setStatus(event.target.value as 'draft' | 'published')}>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </label>
          <button disabled={loading} type="submit">{loading ? 'Saving...' : 'Save content'}</button>
        </form>
      </section>

      <section className="panel">
        <h2>Content</h2>
        {content.length === 0 ? (
          <p>No content items yet.</p>
        ) : (
          <ul className="content-list">
            {content.map((item) => (
              <li key={item.id}>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                  <span>{item.status}</span>
                </div>
                <div className="actions">
                  <button className="secondary" onClick={() => updateStatus(item, item.status === 'draft' ? 'published' : 'draft')} type="button">
                    {item.status === 'draft' ? 'Publish' : 'Unpublish'}
                  </button>
                  <button className="danger" onClick={() => deleteContent(item)} type="button">Delete</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
