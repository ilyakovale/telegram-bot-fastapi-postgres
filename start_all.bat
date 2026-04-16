@echo off
title Telegram Bot Launcher
color 0A

setlocal enabledelayedexpansion

echo ========================================
echo    Запуск микросервисов Telegram Bot
echo ========================================
echo.

REM Пути к вашим сервисам
set GATEWAY_PATH=D:\telegram-bot-fastapi-postgres\gateway_service
set ACCOUNT_PATH=D:\telegram-bot-fastapi-postgres\account_service


timeout /t 2 /nobreak > nul

echo Запуск Gateway (Telegram Bot)...
start "Telegram Gateway" cmd /k "cd /d %GATEWAY_PATH% && python __main__.py"

timeout /t 2 /nobreak > nul

echo Запуск Account Service...
start "Account Service" cmd /k "cd /d %ACCOUNT_PATH% && python __main__.py"

echo.
echo ========================================
echo    ✅ Все сервисы запущены!
echo ========================================
echo.
echo Сервисы работают в отдельных окнах
echo Закройте окна для остановки сервисов
echo.

pause