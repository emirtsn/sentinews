'use client';
import { useEffect, useState } from 'react';
import { 
  LayoutGrid, 
  TrendingUp, 
  AlertCircle, 
  Newspaper, 
  Globe, 
  Clock, 
  ChevronRight,
  LogIn,
  LogOut,
  X
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

export default function Home() {
  const [news, setNews] = useState<News[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [timeFilter, setTimeFilter] = useState('all'); 
  const [showLogin, setShowLogin] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false); 
  const [email, setEmail] = useState(''); 
  const [password, setPassword] = useState(''); 
  const [isRegistering, setIsRegistering] = useState(false);
  const [fullName, setFullName] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/news') 
      .then((res) => res.json())
      .then((data) => {
        setNews(data);
        setLoading(false);
      })
      .catch((err) => console.error("Veri çekme hatası:", err));
  }, []);



const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  
  const formData = new FormData();
  formData.append('username', email); // FastAPI'nin beklediği format
  formData.append('password', password);

  try {
    const res = await fetch('http://localhost:8000/auth/token', {
      method: 'POST',
      body: formData,
    });

    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.access_token); // Mühürü tarayıcıya sakla
      setIsLoggedIn(true);
      setShowLogin(false);
      // Sayfayı yenilemeden haberleri tekrar çekmek için useEffect tetiklenecek
    } else {
      alert("Giriş başarısız. Lütfen bilgileri kontrol et.");
    }
  } catch (err) {
    console.error("Login hatası:", err);
  }
};

const handleRegister = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    const res = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        password: password,
        full_name: fullName
      }),
    });

    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      setIsLoggedIn(true);
      setShowLogin(false);
      alert("Hesabın başarıyla oluşturuldu!");
    } else {
      alert("Kayıt sırasında bir hata oluştu.");
    }
  } catch (err) {
    console.error("Kayıt hatası:", err);
  }
};


  const filteredNews = news.filter(item => {
    const categoryMatch = selectedCategory === 'All' || item.category === selectedCategory;
    
    const newsDate = new Date(item.published_at);
    const now = new Date();
    const diffInHours = (now.getTime() - newsDate.getTime()) / (1000 * 60 * 60);
    
    let timeMatch = true;
    if (timeFilter === 'day') timeMatch = diffInHours <= 24;
    else if (timeFilter === 'week') timeMatch = diffInHours <= 168;
    
    return categoryMatch && timeMatch;
  })
  .sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());

  const avgSentiment = news.length > 0 
    ? news.reduce((acc, curr) => acc + curr.sentiment_score, 0) / news.length 
    : 0;

  if (loading) return (
    <div className="flex h-screen items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
        <p className="font-bold text-slate-400">SentiNews Hazırlanıyor...</p>
      </div>
    </div>
  );

  return (
    <main className="min-h-screen bg-[#f8fafc] pb-20">
      {/* 1. Modern Navbar */}
      <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-8 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-200">
              <Newspaper size={20} />
            </div>
            <span className="text-xl font-black tracking-tight text-slate-800 uppercase">
              Senti<span className="text-blue-600">News</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            {isLoggedIn ? (
              <div className="flex items-center gap-4">
                <div className="text-right hidden sm:block">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Hoş Geldin</p>
                  <p className="text-sm font-bold text-slate-900">Merhaba, {fullName || email.split('@')[0]}</p>
                </div>

                <button 
                  onClick={() => { localStorage.removeItem('token'); setIsLoggedIn(false); }}
                  className="rounded-xl bg-slate-100 p-2 text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition-all"
                >
                  <LogOut size={18} />
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setShowLogin(true)}
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all"
              >
                <LogIn size={18} />
                <span>Giriş Yap</span>
              </button>
            )}
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-6xl px-8 pt-12">
        {/* 2. İstatistik Paneli */}
        <div className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm transition-all hover:shadow-md">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-blue-600">
              <Globe size={18} />
            </div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Veritabanı Hacmi</p>
            <h3 className="text-2xl font-black text-slate-800">{news.length} Haber</h3>
          </div>

          <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm transition-all hover:shadow-md">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
              <TrendingUp size={18} />
            </div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Genel Toplum Modu</p>
            <h3 className="text-2xl font-black text-slate-800">
              {avgSentiment > 0.1 ? 'Pozitif 😊' : avgSentiment < -0.1 ? 'Negatif 😟' : 'Nötr 😐'}
            </h3>
          </div>

          <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm transition-all hover:shadow-md">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-rose-50 text-rose-600">
              <AlertCircle size={18} />
            </div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Kritik Gelişmeler</p>
            <h3 className="text-2xl font-black text-slate-800">
              {news.filter(n => n.sentiment_score < -0.1).length} Haber
            </h3>
          </div>
        </div>

        {!isLoggedIn && (
          <div className="mb-10 overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 to-indigo-700 p-6 text-white shadow-xl shadow-blue-200/40">
            <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
              <div className="flex items-center gap-4">
                
                <p className="text-lg font-bold tracking-tight">
                  Sana özel haberleri kaçırma, hemen giriş yap!
                </p>
              </div>
              <button 
                onClick={() => setShowLogin(true)}
                className="rounded-xl bg-white px-6 py-3 text-sm font-black text-blue-600 transition-all hover:bg-blue-50 active:scale-95 shadow-md"
              >
                Giriş Yap
              </button>
            </div>
          </div>
        )}

        {/* 3. Filtreleme Alanı */}
        <div className="mb-10 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <LayoutGrid size={20} className="text-blue-600" />
              <h2>Kategoriler</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {['All', 'Technology', 'Business', 'Sports', 'Science', 'Health', 'Entertainment'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`rounded-xl px-5 py-2 text-xs font-bold transition-all duration-300 ${
                    selectedCategory === cat 
                      ? 'bg-slate-900 text-white shadow-lg' 
                      : 'bg-white text-slate-500 border border-slate-100 hover:border-blue-200 hover:text-blue-600'
                  }`}
                >
                  {cat === 'All' ? 'Tümü' : cat}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3">
            <Clock size={16} className="text-slate-400" />
            <div className="flex gap-2">
              {[
                { id: 'all', label: 'Tüm Zamanlar' },
                { id: 'day', label: 'Son 24 Saat' },
                { id: 'week', label: 'Son 1 Hafta' }
              ].map((time) => (
                <button
                  key={time.id}
                  onClick={() => setTimeFilter(time.id)}
                  className={`px-4 py-1.5 text-[10px] font-black uppercase tracking-wider rounded-lg transition-all ${
                    timeFilter === time.id 
                      ? 'bg-blue-600 text-white shadow-sm' 
                      : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  {time.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 4. Haber Kartları Izgarası */}
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {filteredNews.map((item) => (
            <div 
              key={item.id} 
              className="group relative flex flex-col rounded-[2.5rem] border border-slate-100 bg-white p-3 shadow-sm transition-all duration-500 hover:-translate-y-2 hover:shadow-2xl hover:shadow-blue-100/40"
            >
              <div className="flex flex-1 flex-col p-6">
                <div className="mb-4 flex items-center justify-between">
                  <span className="rounded-lg bg-blue-50 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-blue-600">
                    {item.category}
                  </span>
                  <div className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-black ${
                    item.sentiment_score > 0.1 ? 'bg-emerald-50 text-emerald-600' : 
                    item.sentiment_score < -0.1 ? 'bg-rose-50 text-rose-600' : 'bg-slate-50 text-slate-400'
                  }`}>
                    {item.sentiment_score > 0.1 ? '+' : ''}{item.sentiment_score.toFixed(2)}
                  </div>
                </div>

                <h2 className="mb-3 text-lg font-bold leading-tight text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-2">
                  {item.title}
                </h2>
                
                <p className="mb-6 line-clamp-3 text-sm leading-relaxed text-slate-500">
                  {item.summary}
                </p>

                <div className="mt-auto flex items-center justify-between border-t border-slate-50 pt-5">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-slate-800 uppercase tracking-tighter">{item.source}</span>
                    <span className="text-[9px] text-slate-400 font-medium">
                      {new Date(item.published_at).toLocaleDateString('tr-TR')}
                    </span>
                  </div>
                  <a 
                    href={item.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white transition-all hover:bg-blue-600 hover:scale-110"
                  >
                    <ChevronRight size={20} />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredNews.length === 0 && (
          <div className="mt-20 text-center">
            <p className="text-slate-400 font-medium">Bu kriterlere uygun haber bulunamadı.</p>
          </div>
        )}
      </div>

      {showLogin && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-md animate-in fade-in zoom-in duration-300 rounded-[2.5rem] border border-slate-200 bg-white p-10 shadow-2xl">
            
            <button 
              onClick={() => setShowLogin(false)}
              className="absolute right-6 top-6 rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-all"
            >
              <X size={20} />
            </button>

            <div className="mb-8">
              <h2 className="text-3xl font-black text-slate-900">
                {isRegistering ? 'Hesap Oluştur' : 'Giriş Yap'}
              </h2>
              <p className="text-sm font-medium text-slate-500">SentiNews dünyasına adım at.</p>
            </div>
            
            <form onSubmit={isRegistering ? handleRegister : handleLogin} className="space-y-4">
              {isRegistering && (
                <div className="space-y-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Ad Soyad</label>
                  <input 
                    type="text" 
                    className="w-full rounded-2xl border-2 border-slate-100 bg-white p-4 text-slate-900 outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-50/50 transition-all placeholder:text-slate-300"
                    placeholder="Ahmet Emir"
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                </div>
              )}

              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">E-Posta</label>
                <input 
                  type="email" 
                  className="w-full rounded-2xl border-2 border-slate-100 bg-white p-4 text-slate-900 outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-50/50 transition-all placeholder:text-slate-300"
                  placeholder="emir@sentinews.com"
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-2">Şifre</label>
                <input 
                  type="password" 
                  className="w-full rounded-2xl border-2 border-slate-100 bg-white p-4 text-slate-900 outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-50/50 transition-all placeholder:text-slate-300"
                  placeholder="••••••••"
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              
              <button type="submit" className="w-full rounded-2xl bg-blue-600 py-5 font-black text-white shadow-xl shadow-blue-200 hover:bg-blue-700 hover:scale-[1.02] active:scale-95 transition-all">
                {isRegistering ? 'Üye Ol' : 'Devam Et'}
              </button>

              <div className="pt-4 text-center">
                <button 
                  type="button"
                  onClick={() => setIsRegistering(!isRegistering)}
                  className="text-xs font-bold text-slate-500 hover:text-blue-600 underline underline-offset-4 decoration-slate-200"
                >
                  {isRegistering ? 'Giriş ekranına dön' : 'Henüz hesabın yok mu? Kayıt ol'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </main>
  );
}