@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python en este equipo.
  echo Instala Python desde https://www.python.org/ y vuelve a intentar.
  pause
  exit /b 1
)
python -m pip install --upgrade pip >nul 2>nul
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Error instalando dependencias.
  pause
  exit /b 1
)
echo.
echo Listo. Dependencias instaladas.
pause
