@echo off
set OUT=%~dp0register_out.txt
echo === pyrevit version > "%OUT%"
pyrevit --version >> "%OUT%" 2>&1
echo === add path >> "%OUT%"
pyrevit extensions paths add "%~dp0..\revit-bridge" >> "%OUT%" 2>&1
echo === paths >> "%OUT%"
pyrevit extensions paths >> "%OUT%" 2>&1
