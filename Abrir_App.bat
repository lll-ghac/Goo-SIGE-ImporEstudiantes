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
python -m pip install -r requirements.txt >nul 2>nul
start "Correos Estudiantes" cmd /k "streamlit run app.py"
