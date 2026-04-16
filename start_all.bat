@echo off
title Telegram Bot Launcher
color 0A

setlocal enabledelayedexpansion

echo ========================================
echo    start services Telegram Bot
echo ========================================
echo.

REM Пути к вашим сервисам
set GATEWAY_PATH=D:\telegram-bot-fastapi-postgres\gateway_service
set ACCOUNT_PATH=D:\telegram-bot-fastapi-postgres\account_service


echo starting Gateway (Telegram Bot)...
start "Telegram Gateway" cmd /k "cd /d %GATEWAY_PATH% && python __main__.py"


echo starting Account Service...
start "Account Service" cmd /k "cd /d %ACCOUNT_PATH% && python __main__.py"

echo.
echo ========================================
echo    all services started successfully!
echo ========================================
echo.


pause