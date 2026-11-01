@echo off
py -3 "%~dp0smoke.py" overview --save overview_snowdon > "%~dp0smoke_out.txt" 2>&1
type "%~dp0smoke_out.txt"
pause
