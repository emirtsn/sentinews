'use client';
import { useEffect, useState } from 'react';
import {
  Globe, Clock, ArrowUpRight, LogIn, LogOut, X,
  Sparkles, SlidersHorizontal, Search, Moon, Sun, Newspaper
} from 'lucide-react';

interface News {
  id: number;
  title: string;
  summary: string;
  category: string;
  sentiment_score: number;
  url: string;
  source: string;
  published_at: string;
}

const API = 'http://localhost:8000';
const ALL_CATEGORIES = ['Technology', 'Business', 'Sports', 'Science', 'Health', 'Entertainment'];

// Her kategori için light/dark ikili renk
const CAT_COLORS: Record<string, { light: string; dark: string }> = {
  Technology:    { light: 'bg-violet-100 text-violet-700',  dark: 'bg-violet-900/40 text-violet-300' },
  Business:      { light: 'bg-amber-100 text-amber-700',    dark: 'bg-amber-900/40 text-amber-300' },
  Sports:        { light: 'bg-emerald-100 text-emerald-700',dark: 'bg-emerald-900/40 text-emerald-300' },
  Science:       { light: 'bg-sky-100 text-sky-700',        dark: 'bg-sky-900/40 text-sky-300' },
  Health:        { light: 'bg-rose-100 text-rose-700',      dark: 'bg-rose-900/40 text-rose-300' },
  Entertainment: { light: 'bg-pink-100 text-pink-700',      dark: 'bg-pink-900/40 text-pink-300' },
  General:       { light: 'bg-slate-100 text-slate-600',    dark: 'bg-slate-800 text-slate-400' },
};

function catColor(category: string, dark: boolean): string {
  const c = CAT_COLORS[category] || CAT_COLORS.General;
  return dark ? c.dark : c.light;
}

function timeAgo(dateStr: string): string {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 3600)  return `${Math.floor(diff / 60)}dk önce`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}sa önce`;
  return `${Math.floor(diff / 86400)}g önce`;
}

function SentimentBadge({ score }: { score: number }) {
  if (score > 0.1)  return <span className="text-[10px] font-bold text-emerald-500">↑ Pozitif</span>;
  if (score < -0.1) return <span className="text-[10px] font-bold text-rose-500">↓ Negatif</span>;
  return <span className="text-[10px] font-bold text-slate-400">— Nötr</span>;
}

export default function Home() {
  const [news, setNews]                         = useState<News[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [timeFilter, setTimeFilter]             = useState('all');
  const [searchQuery, setSearchQuery]           = useState('');
  const [showLogin, setShowLogin]               = useState(false);
  const [isLoggedIn, setIsLoggedIn]             = useState(false);
  const [email, setEmail]                       = useState('');
  const [password, setPassword]                 = useState('');
  const [isRegistering, setIsRegistering]       = useState(false);
  const [fullName, setFullName]                 = useState('');
  const [mode, setMode]                         = useState<'general' | 'personal'>('general');
  const [showPreferences, setShowPreferences]   = useState(false);
  const [selectedPrefs, setSelectedPrefs]       = useState<string[]>([]);
  const [savingPrefs, setSavingPrefs]           = useState(false);
  const [dark, setDark]                         = useState(false);

  // Renk yardımcıları
  const bg       = dark ? '#0F0F0F' : '#F7F5F0';
  const bgCard   = dark ? '#1C1C1C' : '#FFFFFF';
  const bgHover  = dark ? '#242424' : '#F8F7F4';
  const border   = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.10)';
  const txtMain  = dark ? '#EDEDED' : '#0F172A';
  const txtMuted = dark ? '#888'    : '#64748B';
  const txtDim   = dark ? '#555'    : '#94A3B8';
  const bgDecorative = dark ? '#262626' : '#E8E6E0';
  const bgSkeleton   = dark ? '#2A2A2A' : '#DEDBD4';

  // ── Haber çekme ────────────────────────────────────────────────────────
  const fetchNews = async (loggedIn: boolean, currentMode: 'general' | 'personal') => {
    setLoading(true);
    const token = localStorage.getItem('token');
    const url = loggedIn && token && currentMode === 'personal' ? `${API}/news/me` : `${API}/news`;
    const headers: Record<string, string> = loggedIn && token ? { Authorization: `Bearer ${token}` } : {};
    try {
      const res = await fetch(url, { headers });
      if (res.status === 401) {
        localStorage.removeItem('token');
        setIsLoggedIn(false);
        setMode('general');
        const fb = await fetch(`${API}/news`);
        setNews(Array.isArray(await fb.json()) ? await fb.json() : []);
        return;
      }
      const data = await res.json();
      setNews(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Veri çekme hatası:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('token');
    if (token) {
      setIsLoggedIn(true);
      fetch(`${API}/users/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then(res => res.status === 401 ? (localStorage.removeItem('token'), setIsLoggedIn(false), null) : res.json())
        .then(data => { if (data?.full_name) setFullName(data.full_name); if (data?.email) setEmail(data.email); })
        .catch(() => {});
    }
    fetchNews(!!token, 'general');
  }, []);

  const handleModeSwitch = async (newMode: 'general' | 'personal') => {
    if (newMode === 'personal' && !isLoggedIn) { setShowLogin(true); return; }
    if (newMode === 'personal') {
      const token = localStorage.getItem('token');
      try {
        const res  = await fetch(`${API}/users/me/preferences`, { headers: { Authorization: `Bearer ${token}` } });
        const data = await res.json();
        if (!data.preferences || data.preferences.length === 0) { setShowPreferences(true); return; }
        setSelectedPrefs(data.preferences);
      } catch {}
    }
    setMode(newMode);
    fetchNews(isLoggedIn, newMode);
  };

  const savePreferences = async () => {
    if (selectedPrefs.length === 0) return;
    setSavingPrefs(true);
    const token = localStorage.getItem('token');
    try {
      await fetch(`${API}/users/me/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ preferences: selectedPrefs }),
      });
      setShowPreferences(false);
      setMode('personal');
      fetchNews(true, 'personal');
    } catch {} finally { setSavingPrefs(false); }
  };

  const togglePref = (cat: string) =>
    setSelectedPrefs(prev => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]);

  const logInteraction = (newsId: number, type: 'click' | 'view' | 'bookmark') => {
    const token = localStorage.getItem('token');
    if (!token) return;
    fetch(`${API}/log-interaction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ news_id: newsId, interaction_type: type }),
    }).then(res => { if (res.status === 401) { localStorage.removeItem('token'); setIsLoggedIn(false); setMode('general'); } }).catch(() => {});
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append('username', email);
    fd.append('password', password);
    const res = await fetch(`${API}/auth/token`, { method: 'POST', body: fd });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      setIsLoggedIn(true); setShowLogin(false);
      fetchNews(true, mode);
    } else alert('Giriş başarısız.');
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      setIsLoggedIn(true); setShowLogin(false); setShowPreferences(true);
    } else alert('Kayıt başarısız.');
  };

  const filteredNews = news.filter(item => {
    const catOk  = selectedCategory === 'All' || item.category === selectedCategory;
    const diff   = (Date.now() - new Date(item.published_at).getTime()) / 3600000;
    const timeOk = timeFilter === 'all' || (timeFilter === 'day' && diff <= 72) || (timeFilter === 'week' && diff <= 168);
    const q      = searchQuery.toLowerCase();
    const srchOk = !q || item.title.toLowerCase().includes(q) || (item.summary || '').toLowerCase().includes(q);
    return catOk && timeOk && srchOk;
  }).sort((a, b) => mode === 'general' ? new Date(b.published_at).getTime() - new Date(a.published_at).getTime() : 0);

  const avgSentiment = news.length > 0 ? news.reduce((s, n) => s + n.sentiment_score, 0) / news.length : 0;
  const featured  = filteredNews[0];
  const secondary = filteredNews.slice(1, 3);
  const rest      = filteredNews.slice(3);

  // Paylaşılan input stili
  const inputStyle = {
    background: bgCard,
    border: `1px solid ${border}`,
    color: txtMain,
    outline: 'none',
  };

  if (loading) return (
    <div className="min-h-screen" style={{ background: bg }}>
      <div className="sticky top-0 z-50 border-b px-6 py-6" style={{ background: bg, borderColor: border }}>
        <div className="mx-auto max-w-7xl flex items-center justify-between">
          <div className="h-8 w-40 rounded-lg animate-pulse" style={{ background: bgCard }} />
          <div className="h-8 w-48 rounded-full animate-pulse" style={{ background: bgCard }} />
          <div className="h-8 w-24 rounded-lg animate-pulse" style={{ background: bgCard }} />
        </div>
      </div>
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-10 grid grid-cols-3 gap-px rounded-2xl overflow-hidden" style={{ background: border }}>
          {[1,2,3].map(i => (
            <div key={i} className="p-5" style={{ background: bgCard }}>
              <div className="h-3 w-20 rounded animate-pulse mb-3" style={{ background: bgSkeleton }} />
              <div className="h-7 w-28 rounded animate-pulse" style={{ background: bgSkeleton }} />
            </div>
          ))}
        </div>
        <div className="mb-6 rounded-2xl overflow-hidden h-56 animate-pulse" style={{ background: bgSkeleton }} />
        <div className="grid grid-cols-2 gap-4 mb-6">
          {[1,2].map(i => (
            <div key={i} className="rounded-2xl p-6 animate-pulse" style={{ background: bgCard }}>
              <div className="h-3 w-20 rounded mb-4" style={{ background: bgSkeleton }} />
              <div className="h-5 w-full rounded mb-2" style={{ background: bgSkeleton }} />
              <div className="h-5 w-3/4 rounded mb-4" style={{ background: bgSkeleton }} />
              <div className="h-3 w-full rounded mb-2" style={{ background: bgSkeleton }} />
              <div className="h-3 w-2/3 rounded" style={{ background: bgSkeleton }} />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="rounded-xl p-5 animate-pulse" style={{ background: bgCard }}>
              <div className="h-3 w-16 rounded mb-3" style={{ background: bgSkeleton }} />
              <div className="h-4 w-full rounded mb-2" style={{ background: bgSkeleton }} />
              <div className="h-4 w-4/5 rounded mb-4" style={{ background: bgSkeleton }} />
              <div className="h-3 w-full rounded mb-1" style={{ background: bgSkeleton }} />
              <div className="h-3 w-3/4 rounded" style={{ background: bgSkeleton }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <main className="min-h-screen" style={{ background: bg, color: txtMain, fontFamily: "'Georgia', serif" }}>

      {/* ── NAVBAR ─────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 backdrop-blur-sm" style={{ background: `${bg}F0`, borderBottom: `1px solid ${border}` }}>
        <div className="mx-auto max-w-7xl px-6">

          {/* Üst şerit */}
          <div className="flex items-center justify-between py-2.5" style={{ borderBottom: `1px solid ${border}`, fontFamily: 'sans-serif' }}>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: txtDim }}>
              {new Date().toLocaleDateString('tr-TR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
            <div className="flex items-center gap-3">
              {/* Dark mode toggle */}
              <button
                onClick={() => setDark(d => !d)}
                className="flex items-center justify-center w-7 h-7 rounded-full transition-colors"
                style={{ color: txtMuted, background: bgHover }}
              >
                {dark ? <Sun size={13} /> : <Moon size={13} />}
              </button>

              {isLoggedIn ? (
                <div className="flex items-center gap-3">
                  <span className="text-xs" style={{ color: txtMuted }}>{fullName || email.split('@')[0]}</span>
                  <button
                    onClick={() => { localStorage.removeItem('token'); setIsLoggedIn(false); setMode('general'); fetchNews(false, 'general'); }}
                    className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest transition-colors"
                    style={{ color: txtMuted }}
                  >
                    <LogOut size={12} /> Çıkış
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowLogin(true)}
                  className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest transition-colors"
                  style={{ color: txtMuted }}
                >
                  <LogIn size={12} /> Giriş Yap
                </button>
              )}
            </div>
          </div>

          {/* Logo + Mod toggle */}
          <div className="flex items-center justify-between py-4">
            <div>
              <h1 className="text-4xl font-black tracking-tight leading-none" style={{ color: txtMain }}>
                Senti<span className="italic" style={{ color: txtMuted }}>News</span>
              </h1>
              <p className="text-[10px] uppercase tracking-[0.3em] mt-0.5" style={{ color: txtDim, fontFamily: 'sans-serif' }}>
                Akıllı Haber Platformu
              </p>
            </div>
            <div className="flex items-center rounded-full overflow-hidden" style={{ border: `1px solid ${border}`, fontFamily: 'sans-serif' }}>
              <button
                onClick={() => handleModeSwitch('general')}
                className="flex items-center gap-2 px-5 py-2 text-xs font-bold uppercase tracking-wider transition-all"
                style={{ background: mode === 'general' ? txtMain : 'transparent', color: mode === 'general' ? bg : txtMuted }}
              >
                <Globe size={12} /> Genel
              </button>
              <button
                onClick={() => handleModeSwitch('personal')}
                className="flex items-center gap-2 px-5 py-2 text-xs font-bold uppercase tracking-wider transition-all"
                style={{ background: mode === 'personal' ? txtMain : 'transparent', color: mode === 'personal' ? bg : txtMuted }}
              >
                <Sparkles size={12} /> Benim İçin
              </button>
            </div>
          </div>

          {/* Filtreler */}
          <div className="flex items-center justify-between pb-3 gap-4" style={{ fontFamily: 'sans-serif' }}>
            <div className="flex items-center gap-1 flex-wrap">
              {['All', ...ALL_CATEGORIES].map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full transition-all"
                  style={{
                    background: selectedCategory === cat ? txtMain : 'transparent',
                    color: selectedCategory === cat ? bg : txtMuted,
                  }}
                >
                  {cat === 'All' ? 'Tümü' : cat}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-3">
              {/* Arama */}
              <div className="relative">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: txtDim }} />
                <input
                  type="text"
                  placeholder="Haber ara..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="pl-8 pr-4 py-1.5 text-xs rounded-full w-44 transition-all"
                  style={{ ...inputStyle, '::placeholder': { color: txtDim } } as React.CSSProperties}
                />
              </div>

              {/* Zaman filtresi */}
              <div className="flex items-center gap-1">
                <Clock size={12} style={{ color: txtDim }} />
                {[{ id: 'all', label: 'Tümü' }, { id: 'day', label: '72s' }, { id: 'week', label: '1H' }].map(t => (
                  <button
                    key={t.id}
                    onClick={() => setTimeFilter(t.id)}
                    className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full transition-all"
                    style={{
                      background: timeFilter === t.id ? txtMain : 'transparent',
                      color: timeFilter === t.id ? bg : txtMuted,
                    }}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-6 py-8">

        {/* ── KİŞİSEL MOD BAŞLIĞI ──────────────────────────────────────── */}
        {mode === 'personal' && (
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-1 w-8 rounded-full" style={{ background: txtMain }} />
              <p className="text-xs font-bold uppercase tracking-[0.2em]" style={{ color: txtMuted, fontFamily: 'sans-serif' }}>
                Sana Özel · İlgi alanların ve geçmişine göre sıralandı
              </p>
            </div>
            <button
              onClick={() => setShowPreferences(true)}
              className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider rounded-full px-4 py-2 transition-colors"
              style={{ color: txtMuted, border: `1px solid ${border}`, fontFamily: 'sans-serif' }}
            >
              <SlidersHorizontal size={11} /> İlgi Alanlarım
            </button>
          </div>
        )}

        {/* ── GİRİŞ BANNER ─────────────────────────────────────────────── */}
        {!isLoggedIn && (
          <div className="mb-8 rounded-2xl p-5 flex items-center justify-between" style={{ background: txtMain, fontFamily: 'sans-serif' }}>
            <div className="flex items-center gap-4">
              <Sparkles size={18} className="text-amber-400" />
              <div>
                <p className="text-sm font-bold" style={{ color: bg }}>Kişiselleştirilmiş haber akışı için giriş yap</p>
                <p className="text-xs mt-0.5" style={{ color: `${bg}99` }}>Tıkladıkların seni anlamamıza yardım eder</p>
              </div>
            </div>
            <button
              onClick={() => setShowLogin(true)}
              className="text-xs font-bold uppercase tracking-wider px-5 py-2.5 rounded-full transition-colors"
              style={{ background: bg, color: txtMain }}
            >
              Giriş Yap
            </button>
          </div>
        )}

        {/* ── İSTATİSTİK ───────────────────────────────────────────────── */}
        <div className="mb-10 grid grid-cols-3 rounded-2xl overflow-hidden" style={{ border: `1px solid ${border}`, fontFamily: 'sans-serif' }}>
          {[
            {
              label: mode === 'personal' ? 'Sana Özel' : 'Veritabanı',
              value: `${news.length}`,
              unit: 'haber',
            },
            {
              label: 'Genel Duygu',
              value: avgSentiment > 0.1 ? '😊' : avgSentiment < -0.1 ? '😟' : '😐',
              unit: avgSentiment > 0.1 ? 'Pozitif' : avgSentiment < -0.1 ? 'Negatif' : 'Nötr',
            },
            {
              label: 'Kritik Haberler',
              value: `${news.filter(n => n.sentiment_score < -0.1).length}`,
              unit: 'negatif',
              valueColor: 'text-rose-500',
            },
          ].map((stat, i) => (
            <div
              key={i}
              className="p-5"
              style={{
                background: bgCard,
                borderRight: i < 2 ? `1px solid ${border}` : undefined,
              }}
            >
              <p className="text-[9px] font-bold uppercase tracking-[0.2em] mb-1" style={{ color: txtDim }}>{stat.label}</p>
              <p className={`text-2xl font-black ${stat.valueColor || ''}`} style={!stat.valueColor ? { color: txtMain } : {}}>
                {stat.value}
                <span className="text-base font-normal ml-1" style={{ color: txtMuted }}>{stat.unit}</span>
              </p>
            </div>
          ))}
        </div>

        {filteredNews.length === 0 ? (
          <div className="py-32 text-center">
            <p className="text-sm" style={{ color: txtMuted, fontFamily: 'sans-serif' }}>Bu kriterlere uygun haber bulunamadı.</p>
          </div>
        ) : (
          <>
            {/* ── FEATURED ─────────────────────────────────────────────── */}
            {featured && (
              <a
                href={featured.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => logInteraction(featured.id, 'click')}
                className="group block mb-6 rounded-2xl overflow-hidden transition-all"
                style={{ background: bgCard, border: `1px solid ${border}` }}
              >
                <div className="grid grid-cols-5">
                  <div className="col-span-3 p-8 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-4" style={{ fontFamily: 'sans-serif' }}>
                        <span className={`text-[9px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full ${catColor(featured.category, dark)}`}>
                          {featured.category}
                        </span>
                        <span className="text-[10px]" style={{ color: txtDim }}>{timeAgo(featured.published_at)}</span>
                        <SentimentBadge score={featured.sentiment_score} />
                      </div>
                      <h2 className="text-3xl font-black leading-tight mb-4 transition-colors" style={{ color: txtMain }}>
                        {featured.title}
                      </h2>
                      <p className="leading-relaxed text-base" style={{ color: txtMuted, fontFamily: 'sans-serif' }}>
                        {featured.summary}
                      </p>
                    </div>
                    <div className="flex items-center justify-between mt-6" style={{ fontFamily: 'sans-serif' }}>
                      <span className="text-xs font-bold uppercase tracking-wider" style={{ color: txtDim }}>{featured.source}</span>
                      <div className="flex items-center gap-1.5 text-xs font-bold" style={{ color: txtMain }}>
                        Haberi Oku <ArrowUpRight size={14} />
                      </div>
                    </div>
                  </div>
                  <div className="col-span-2 flex items-center justify-center p-8" style={{ background: bgDecorative }}>
                    <div className="text-center">
                      <div className="text-6xl font-black leading-none mb-2" style={{ color: `${txtMain}25` }}>
                        {featured.category.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.3em]" style={{ color: txtDim, fontFamily: 'sans-serif' }}>
                        {featured.category}
                      </div>
                    </div>
                  </div>
                </div>
              </a>
            )}

            {/* ── İKİNCİL (2 kolon) ────────────────────────────────────── */}
            {secondary.length > 0 && (
              <div className="grid grid-cols-2 gap-4 mb-6">
                {secondary.map(item => (
                  <a
                    key={item.id}
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => logInteraction(item.id, 'click')}
                    className="group block rounded-2xl p-6 transition-all"
                    style={{ background: bgCard, border: `1px solid ${border}` }}
                  >
                    <div className="flex items-center gap-2 mb-3" style={{ fontFamily: 'sans-serif' }}>
                      <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${catColor(item.category, dark)}`}>
                        {item.category}
                      </span>
                      <span className="text-[10px]" style={{ color: txtDim }}>{timeAgo(item.published_at)}</span>
                    </div>
                    <h3 className="text-xl font-black leading-snug mb-3 line-clamp-2 transition-colors" style={{ color: txtMain }}>
                      {item.title}
                    </h3>
                    <p className="text-sm leading-relaxed line-clamp-2 mb-4" style={{ color: txtMuted, fontFamily: 'sans-serif' }}>
                      {item.summary}
                    </p>
                    <div className="flex items-center justify-between" style={{ fontFamily: 'sans-serif' }}>
                      <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: txtDim }}>{item.source}</span>
                      <SentimentBadge score={item.sentiment_score} />
                    </div>
                  </a>
                ))}
              </div>
            )}

            {/* ── AYIRICI ──────────────────────────────────────────────── */}
            {rest.length > 0 && (
              <div className="flex items-center gap-4 mb-6" style={{ fontFamily: 'sans-serif' }}>
                <div className="h-px flex-1" style={{ background: border }} />
                <span className="text-[9px] font-bold uppercase tracking-[0.3em]" style={{ color: txtDim }}>Diğer Haberler</span>
                <div className="h-px flex-1" style={{ background: border }} />
              </div>
            )}

            {/* ── KALAN (3 kolon) ──────────────────────────────────────── */}
            <div className="grid grid-cols-3 gap-4">
              {rest.map(item => (
                <a
                  key={item.id}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => logInteraction(item.id, 'click')}
                  className="group block rounded-xl p-5 transition-all"
                  style={{ background: bgCard, border: `1px solid ${border}` }}
                >
                  <div className="flex items-center justify-between mb-3" style={{ fontFamily: 'sans-serif' }}>
                    <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${catColor(item.category, dark)}`}>
                      {item.category}
                    </span>
                    <span className="text-[10px]" style={{ color: txtDim }}>{timeAgo(item.published_at)}</span>
                  </div>
                  <h3 className="text-base font-black leading-snug mb-2 line-clamp-2 transition-colors" style={{ color: txtMain }}>
                    {item.title}
                  </h3>
                  <p className="text-xs leading-relaxed line-clamp-3 mb-4" style={{ color: txtMuted, fontFamily: 'sans-serif' }}>
                    {item.summary}
                  </p>
                  <div className="flex items-center justify-between pt-3" style={{ borderTop: `1px solid ${border}`, fontFamily: 'sans-serif' }}>
                    <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: txtDim }}>{item.source}</span>
                    <SentimentBadge score={item.sentiment_score} />
                  </div>
                </a>
              ))}
            </div>
          </>
        )}
      </div>

      {/* ── TERCİH MODALI ────────────────────────────────────────────────── */}
      {showPreferences && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center backdrop-blur-sm p-4" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <div className="w-full max-w-lg rounded-3xl p-8 shadow-2xl" style={{ background: bg, border: `1px solid ${border}` }}>
            <div className="mb-6">
              <h2 className="text-2xl font-black mb-1" style={{ color: txtMain }}>İlgi Alanlarını Seç</h2>
              <p className="text-sm" style={{ color: txtMuted, fontFamily: 'sans-serif' }}>Öneri motorumuz seçimlerine göre seni tanımaya başlayacak.</p>
            </div>
            <div className="flex flex-wrap gap-2 mb-8" style={{ fontFamily: 'sans-serif' }}>
              {ALL_CATEGORIES.map(cat => (
                <button
                  key={cat}
                  onClick={() => togglePref(cat)}
                  className="px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-full transition-all"
                  style={{
                    background: selectedPrefs.includes(cat) ? txtMain : bgCard,
                    color: selectedPrefs.includes(cat) ? bg : txtMuted,
                    border: `1px solid ${selectedPrefs.includes(cat) ? txtMain : border}`,
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>
            <div className="flex gap-3" style={{ fontFamily: 'sans-serif' }}>
              <button
                onClick={() => { setShowPreferences(false); fetchNews(isLoggedIn, 'general'); }}
                className="flex-1 py-3 text-sm font-bold rounded-full transition-all"
                style={{ color: txtMuted, border: `1px solid ${border}` }}
              >
                Şimdi Değil
              </button>
              <button
                onClick={savePreferences}
                disabled={selectedPrefs.length === 0 || savingPrefs}
                className="flex-1 py-3 text-sm font-bold rounded-full transition-all disabled:opacity-40"
                style={{ background: txtMain, color: bg }}
              >
                {savingPrefs ? 'Kaydediliyor...' : `Kaydet (${selectedPrefs.length})`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── LOGIN MODALI ─────────────────────────────────────────────────── */}
      {showLogin && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center backdrop-blur-sm p-4" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <div className="relative w-full max-w-md rounded-3xl p-8 shadow-2xl" style={{ background: bg, border: `1px solid ${border}` }}>
            <button onClick={() => setShowLogin(false)} className="absolute right-6 top-6 transition-colors" style={{ color: txtMuted }}>
              <X size={18} />
            </button>
            <div className="mb-6">
              <h2 className="text-2xl font-black" style={{ color: txtMain }}>
                {isRegistering ? 'Hesap Oluştur' : 'Giriş Yap'}
              </h2>
              <p className="text-sm mt-1" style={{ color: txtMuted, fontFamily: 'sans-serif' }}>SentiNews dünyasına adım at.</p>
            </div>
            <form onSubmit={isRegistering ? handleRegister : handleLogin} className="space-y-4" style={{ fontFamily: 'sans-serif' }}>
              {isRegistering && (
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-widest block mb-1.5" style={{ color: txtDim }}>Ad Soyad</label>
                  <input type="text" placeholder="Ahmet Emir" onChange={e => setFullName(e.target.value)} required
                    className="w-full rounded-xl px-4 py-3 text-sm transition-all"
                    style={{ ...inputStyle, '::placeholder': { color: txtDim } } as React.CSSProperties} />
                </div>
              )}
              <div>
                <label className="text-[10px] font-bold uppercase tracking-widest block mb-1.5" style={{ color: txtDim }}>E-Posta</label>
                <input type="email" placeholder="emir@sentinews.com" onChange={e => setEmail(e.target.value)} required
                  className="w-full rounded-xl px-4 py-3 text-sm transition-all"
                  style={inputStyle} />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase tracking-widest block mb-1.5" style={{ color: txtDim }}>Şifre</label>
                <input type="password" placeholder="••••••••" onChange={e => setPassword(e.target.value)} required
                  className="w-full rounded-xl px-4 py-3 text-sm transition-all"
                  style={inputStyle} />
              </div>
              <button type="submit"
                className="w-full py-3 text-sm font-bold rounded-full transition-all"
                style={{ background: txtMain, color: bg }}>
                {isRegistering ? 'Üye Ol' : 'Devam Et'}
              </button>
              <div className="text-center pt-2">
                <button type="button" onClick={() => setIsRegistering(!isRegistering)}
                  className="text-xs underline underline-offset-4 transition-colors"
                  style={{ color: txtDim }}>
                  {isRegistering ? 'Giriş ekranına dön' : 'Hesabın yok mu? Kayıt ol'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}