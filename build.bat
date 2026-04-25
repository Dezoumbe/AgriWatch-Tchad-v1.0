@echo off
echo ╔══════════════════════════════════════════╗
echo ║   AgriWatch Tchad — Build .EXE          ║
echo ╚══════════════════════════════════════════╝
echo.

REM 1. Installer les dépendances
echo [1/3] Installation des dépendances...
pip install customtkinter pyinstaller

REM 2. Compiler en .exe
echo.
echo [2/3] Compilation en .exe (patiente 1-2 minutes)...
pyinstaller --onefile --windowed --name "AgriWatch_Tchad" main.py

REM 3. Résultat
echo.
echo [3/3] Terminé !
echo Le fichier AgriWatch_Tchad.exe se trouve dans le dossier : dist\
echo.
pause
