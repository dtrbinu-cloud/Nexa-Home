import { useEffect, useState } from 'react';
import {
  House,
  Cpu,
  Moon,
  Sun,
  CheckCircle,
  WifiHigh,
  ArrowsClockwise,
} from '@phosphor-icons/react';
import './App.css';

interface ServerHealth {
  status: string;
  app: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  database: {
    status: string;
    journal_mode: string;
  };
}

export function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [health, setHealth] = useState<ServerHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/health');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data: ServerHealth = await res.json();
      setHealth(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Koneksi gagal';
      setError(msg);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <House size={24} weight="regular" />
          <span>Rumah</span>
          <span className="brand-badge">v0.1.0</span>
        </div>
        <div className="topbar-actions">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Ganti mode tampilan"
          >
            {theme === 'light' ? (
              <>
                <Moon size={20} weight="regular" />
                <span>Mode Gelap</span>
              </>
            ) : (
              <>
                <Sun size={20} weight="regular" />
                <span>Mode Terang</span>
              </>
            )}
          </button>
        </div>
      </header>

      <main className="main-content">
        <section className="header-section">
          <h1 className="page-title">Smart Home & Pengawasan Keluarga</h1>
          <p className="page-subtitle">
            Fondasi repositori dan konfigurasi awal (Tahap 0)
          </p>
        </section>

        <div className="grid-two">
          <div className="card">
            <h2 className="card-title">
              <Cpu size={20} weight="regular" />
              <span>Status Backend</span>
            </h2>
            <div className="stat-row">
              <span className="stat-label">Layanan</span>
              <span className="stat-value">FastAPI (Python 3.11)</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Status Koneksi</span>
              {loading ? (
                <span className="status-badge warn">Memeriksa...</span>
              ) : health?.status === 'ok' ? (
                <span className="status-badge ok">Terhubung</span>
              ) : (
                <span className="status-badge danger">
                  {error ?? 'Terputus'}
                </span>
              )}
            </div>
            <div className="stat-row">
              <span className="stat-label">Database</span>
              <span className="stat-value">
                {health?.database.status === 'connected'
                  ? `SQLite (${health.database.journal_mode.toUpperCase()})`
                  : 'Belum terhubung'}
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Uptime Server</span>
              <span className="stat-value">
                {health ? `${health.uptime_seconds} detik` : '-'}
              </span>
            </div>
            <div style={{ marginTop: 'var(--space-2)' }}>
              <button
                type="button"
                className="primary"
                onClick={checkHealth}
                disabled={loading}
              >
                <ArrowsClockwise size={20} weight="regular" />
                <span>{loading ? 'Menghubungkan...' : 'Periksa Ulang'}</span>
              </button>
            </div>
          </div>

          <div className="card">
            <h2 className="card-title">
              <WifiHigh size={20} weight="regular" />
              <span>Ceklist Tahap 0 Selesai</span>
            </h2>
            <ul className="checklist">
              <li className="checklist-item">
                <CheckCircle
                  size={20}
                  weight="regular"
                  className="checklist-icon"
                />
                <span>Monorepo: server, web, firmware, camera-app, docs</span>
              </li>
              <li className="checklist-item">
                <CheckCircle
                  size={20}
                  weight="regular"
                  className="checklist-icon"
                />
                <span>Dokumentasi arsitektur docs/DECISIONS.md</span>
              </li>
              <li className="checklist-item">
                <CheckCircle
                  size={20}
                  weight="regular"
                  className="checklist-icon"
                />
                <span>Sistem token desain (Public Sans & IBM Plex Mono)</span>
              </li>
              <li className="checklist-item">
                <CheckCircle
                  size={20}
                  weight="regular"
                  className="checklist-icon"
                />
                <span>Skrip orkestrasi Windows scripts/dev.ps1</span>
              </li>
              <li className="checklist-item">
                <CheckCircle
                  size={20}
                  weight="regular"
                  className="checklist-icon"
                />
                <span>Backend FastAPI + SQLite mode WAL diverifikasi tes</span>
              </li>
            </ul>
          </div>
        </div>
      </main>

      <footer className="footer">
        <span>Sistem Smart Home "Rumah" — Risang</span>
        <span className="mono">Target: Windows 10 | i3 gen 4 | 8GB RAM</span>
      </footer>
    </div>
  );
}

export default App;
