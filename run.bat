@echo off
title Sistema Inventarios Kardex Digital - Control de Existencias
echo =====================================================================
echo   INICIANDO SISTEMA INVENTARIOS KARDEX DIGITAL v3.2
echo   Plataforma de Control Logistico, Kardex y Gestion de Almacen
echo =====================================================================
echo.
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python main.py
pause
