@echo off
set OUT=%~dp0smoke_out.txt
py -3 "%~dp0smoke_health.py" > "%OUT%" 2>&1
