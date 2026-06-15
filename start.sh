#!/bin/bash

echo "🚀 SentiNews başlatılıyor..."

# 1. Docker container'ı başlat
echo "\n[1/3] PostgreSQL başlatılıyor..."
docker start sentinews_db
sleep 2

# DB hazır olana kadar bekle
echo "  Veritabanı bağlantısı bekleniyor..."
until docker exec sentinews_db pg_isready -U admin -d sentinews_db -q; do
  sleep 1
done
echo "  ✓ Veritabanı hazır"

# 2. Backend'i arka planda başlat
echo "\n[2/3] Backend başlatılıyor..."
source .venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "  ✓ Backend PID: $BACKEND_PID"

# Backend hazır olana kadar bekle
sleep 3

# 3. Frontend'i başlat
echo "\n[3/3] Frontend başlatılıyor..."
cd web && npm run dev &
FRONTEND_PID=$!
cd ..
echo "  ✓ Frontend PID: $FRONTEND_PID"

echo "\n✅ SentiNews çalışıyor!"
echo "   Frontend : http://localhost:3000"
echo "   Backend  : http://localhost:8000"
echo "   API Docs : http://localhost:8000/docs"
echo "\nDurdurmak için Ctrl+C"

# Ctrl+C ile her şeyi durdur
trap "echo '\nDurduruluyor...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" SIGINT
wait