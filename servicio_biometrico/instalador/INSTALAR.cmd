@echo off
setlocal
title Instalador HuelleroBridge - JainSportBox

:: ── Auto-elevacion: si no somos admin, relanzar con UAC ──
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Pidiendo permisos de administrador...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
echo.
echo  ============================================
echo   Instalador del huellero - JainSportBox
echo  ============================================
echo.
echo  IMPORTANTE: NO conectes el lector de huella todavia.
echo.
pause

:: ── Paso 1: runtime DigitalPersona (driver + COM) ──
if exist "%SystemRoot%\SysWOW64\DPFPApi.dll" (
    echo [1/5] DigitalPersona ya esta instalado, se omite.
) else if exist "%SystemRoot%\System32\DPFPApi.dll" (
    echo [1/5] DigitalPersona ya esta instalado, se omite.
) else (
    echo [1/5] Instalando DigitalPersona RTE... esto tarda 1-2 minutos.
    if exist "%ProgramFiles(x86)%" (
        msiexec /i "%~dp0RTE\Install\x64\Setup.msi" /passive /norestart
    ) else (
        msiexec /i "%~dp0RTE\Install\Setup.msi" /passive /norestart
    )
    if errorlevel 1 (
        echo   ERROR instalando el RTE. Proba ejecutar RTE\Setup.exe a mano.
        pause
        exit /b 1
    )
    echo   RTE instalado.
)

:: ── Paso 2: copiar el bridge ──
echo [2/5] Deteniendo bridge anterior si esta corriendo...
taskkill /f /im HuelleroBridge.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [2/5] Copiando HuelleroBridge a C:\JainSportBox\HuelleroBridge ...
if not exist "C:\JainSportBox\HuelleroBridge" mkdir "C:\JainSportBox\HuelleroBridge"
xcopy /y /q "%~dp0Bridge\*" "C:\JainSportBox\HuelleroBridge\"
if errorlevel 1 (
    echo   ERROR: no se pudo copiar el exe. Cierra HuelleroBridge.exe en el
    echo   Administrador de tareas y volve a correr este instalador.
    pause
    exit /b 1
)
fc /b "%~dp0Bridge\HuelleroBridge.exe" "C:\JainSportBox\HuelleroBridge\HuelleroBridge.exe" >nul
if errorlevel 1 (
    echo   ERROR: el exe copiado NO coincide con el del paquete. Cierra el
    echo   bridge en el Administrador de tareas y reintenta.
    pause
    exit /b 1
)
echo   Copiado y verificado.

:: ── Paso 3: BRIDGE_SECRET (OBLIGATORIO) ──
:: Sin el secreto correcto el bridge arranca igual y no da ningun error de auth:
:: simplemente loguea "Templates cargados: 0" y no reconoce ninguna huella. Por eso
:: se pide en un bucle en vez de ofrecer un default, como hacia la version anterior.
echo.
echo [3/5] BRIDGE_SECRET
echo   Tiene que ser EXACTAMENTE el mismo que el del backend
echo   (en Render: Environment ^> BRIDGE_SECRET).
echo.
:pedir_secreto
set "SECRETO="
set /p SECRETO="  Pega el BRIDGE_SECRET: "
if "%SECRETO%"=="" (
    echo   No puede quedar vacio: sin el, el lector no va a reconocer a nadie.
    echo   Si de verdad querés saltear este paso, escribi SALTAR.
    goto pedir_secreto
)
if /i "%SECRETO%"=="SALTAR" (
    echo   Salteado. OJO: el bridge va a usar el default compilado, que el backend
    echo   de produccion RECHAZA. Habra que configurarlo a mano despues.
) else (
    setx BRIDGE_SECRET "%SECRETO%" /M >nul
    echo   BRIDGE_SECRET configurado a nivel maquina.
)

:: ── Paso 4: puerto de la palanquera (opcional) ──
:: La autodeteccion recorre los puertos COM pingueando; si el bridge arranca antes
:: de que el Arduino este enchufado, no encuentra nada. Fijarlo evita ese caso.
echo.
echo [4/5] Palanquera (Arduino)
echo   Si esta PC controla la palanquera, indica su puerto COM (ej. COM3).
echo   Enter = dejar que el bridge lo autodetecte.
set "PUERTO="
set /p PUERTO="  Puerto COM del Arduino: "
if not "%PUERTO%"=="" (
    setx PALANQUERA_COM "%PUERTO%" /M >nul
    echo   PALANQUERA_COM=%PUERTO% configurado.
) else (
    echo   Se usara la autodeteccion.
)

:: ── Paso 5: tarea programada (autoarranque como admin) ──
echo.
echo [5/5] Creando tarea de inicio automatico...
schtasks /create /f /tn "HuelleroBridge" /sc onlogon /rl highest /tr "C:\JainSportBox\HuelleroBridge\HuelleroBridge.exe" >nul
echo   Tarea "HuelleroBridge" creada (arranca al iniciar sesion).

echo.
echo  ============================================
echo   LISTO. Ahora:
echo   1. Conecta el lector de huella U.are.U 4500
echo      (espera a que Windows lo detecte)
echo   2. Presiona una tecla para arrancar el bridge
echo  ============================================
pause

:: El primer arranque va DIRECTO y no por schtasks: el Task Scheduler es un servicio
:: que puede tener cacheado el entorno viejo, asi que lanzado por ahi el bridge no
:: veria el BRIDGE_SECRET que acabamos de setear. Desde el proximo inicio de sesion
:: la tarea ya lo toma bien.
if not "%SECRETO%"=="" if /i not "%SECRETO%"=="SALTAR" set "BRIDGE_SECRET=%SECRETO%"
if not "%PUERTO%"=="" set "PALANQUERA_COM=%PUERTO%"
start "" "C:\JainSportBox\HuelleroBridge\HuelleroBridge.exe"

echo.
echo  Esperando que el bridge levante...
timeout /t 10 /nobreak >nul

:: Verificacion: templates_en_cache es LO QUE IMPORTA. Con 0, el lector no reconoce
:: a nadie, y es el sintoma que no da ningun error visible en pantalla.
powershell -NoProfile -Command ^
  "try {" ^
  "  $s = Invoke-RestMethod 'http://localhost:8001/status' -TimeoutSec 10;" ^
  "  Write-Host ('  Lector: ' + $s.dispositivo + ' | Huellas en cache: ' + $s.templates_en_cache);" ^
  "  if ($s.templates_en_cache -gt 0) { Write-Host '  OK: el bridge se autentico y cargo las huellas.' -ForegroundColor Green }" ^
  "  else { Write-Host '  ATENCION: 0 huellas en cache.' -ForegroundColor Yellow;" ^
  "         Write-Host '  Puede ser (a) el BRIDGE_SECRET no coincide con el backend, o' -ForegroundColor Yellow;" ^
  "         Write-Host '  (b) todavia no hay ninguna huella enrolada. Revisa bridge.log.' -ForegroundColor Yellow }" ^
  "} catch { Write-Host '  ERROR: el bridge no responde en localhost:8001. Revisa bridge.log.' -ForegroundColor Red }"

echo.
echo  Log del bridge: C:\JainSportBox\HuelleroBridge\bridge.log
echo  Las primeras lineas [CONFIG] dicen a que backend apunta.
echo.
pause
