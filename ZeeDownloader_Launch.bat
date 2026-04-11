@echo off
cd /d "%~dp0"
title Zee Downloader
py -3.12 "%~dp0ZeeDownloader.py"
if errorlevel 1 (
    echo.
    echo ERROR: Could not start Zee Downloader.
    pause
)
