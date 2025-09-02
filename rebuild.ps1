# PowerShell скрипт для пересборки Docker контейнеров

Write-Host "🔄 Пересборка Docker контейнеров..." -ForegroundColor Cyan

# Остановка и удаление контейнеров
Write-Host "⏹️  Останавливаю контейнеры..." -ForegroundColor Yellow
docker-compose down

# Удаление образов для принудительной пересборки
Write-Host "🗑️  Удаляю старые образы..." -ForegroundColor Yellow
docker-compose down --rmi all

# Очистка неиспользуемых образов
Write-Host "🧹 Очищаю неиспользуемые образы..." -ForegroundColor Yellow
docker image prune -f

# Пересборка и запуск
Write-Host "🔨 Пересобираю контейнеры..." -ForegroundColor Green
docker-compose up --build -d

Write-Host "✅ Готово! Контейнеры пересобраны и запущены." -ForegroundColor Green
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps
