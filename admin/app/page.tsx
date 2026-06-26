'use client';

'use client';

import axios from 'axios';
import { useEffect, useState } from 'react';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export default function Home() {
  const [content, setContent] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = window.localStorage.getItem('vex_token');
    if (!token) return;

    api
      .get('/content', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => setContent(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Unable to load content'));
  }, []);

  return (
    <main className="container">
      <section className="hero">
        <h1>VEX Admin Dashboard</h1>
        <p>Manage content and review usage for your AI Content Studio.</p>
      </section>
      <section className="content-list">
        {error && <div className="error">{error}</div>}
        {content.length === 0 ? (
          <p>No content items yet.</p>
        ) : (
          <ul>
            {content.map((item: any) => (
              <li key={item.id}>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
