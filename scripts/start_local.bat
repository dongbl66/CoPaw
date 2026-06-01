@echo off
setlocal EnableDelayedExpansion

REM --- Local QwenPaw startup script ---
REM Starts this project's QwenPaw with custom ports (8090 range).

set "PROJECT_ROOT=%~dp0.."
for %%I in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fI"

REM --- Conda environment ---
set "CONDA_PYTHON=D:\Program\anaconda3\envs\evotraders-py310\python.exe"

if not exist "%CONDA_PYTHON%" (
    echo [qwenpaw-local] ERROR: Conda env not found: %CONDA_PYTHON%
    echo [qwenpaw-local] Please run scripts\install.bat first.
    pause
    exit /b 1
)

for /f "delims=" %%v in ('"%CONDA_PYTHON%" --version 2^>^&1') do set "PY_VERSION=%%v"
echo [qwenpaw-local] Using conda env: %PY_VERSION%

pushd "%PROJECT_ROOT%"
echo [qwenpaw-local] Working dir: %CD%

REM --- Port config ---
set "QWENPAW_PORT=8090"
set "QWENPAW_WS_PORT=6190"
set "QWENPAW_SIP_PORT=5090"

REM --- Isolate working dir from official QwenPaw ---
set "QWENPAW_WORKING_DIR=%PROJECT_ROOT%\.qwenpaw"
set "COPAW_WORKING_DIR=%QWENPAW_WORKING_DIR%"
set "PYTHONPATH=%PROJECT_ROOT%\src;%PYTHONPATH%"
if not exist "%QWENPAW_WORKING_DIR%" mkdir "%QWENPAW_WORKING_DIR%"
echo [qwenpaw-local] Working dir: %QWENPAW_WORKING_DIR%

REM --- Build frontend if not exists ---
set "FRONTEND_DIST=%PROJECT_ROOT%\console\dist"
set "FRONTEND_PKG=%PROJECT_ROOT%\src\qwenpaw\console"
set "CONSOLE_DIR=%PROJECT_ROOT%\console"
set "CONSOLE_NODE_MODULES=%CONSOLE_DIR%\node_modules"
set "CONSOLE_TSC_CMD=%CONSOLE_NODE_MODULES%\.bin\tsc.cmd"
set "CONSOLE_VITE_CMD=%CONSOLE_NODE_MODULES%\.bin\vite.cmd"
set "CONSOLE_TSC_JS=%CONSOLE_NODE_MODULES%\typescript\bin\tsc"
set "CONSOLE_VITE_JS=%CONSOLE_NODE_MODULES%\vite\bin\vite.js"
set "QWENPAW_CONSOLE_STATIC_DIR=%FRONTEND_DIST%"
set "COPAW_CONSOLE_STATIC_DIR=%QWENPAW_CONSOLE_STATIC_DIR%"

if not exist "%FRONTEND_DIST%\index.html" (
    echo [qwenpaw-local] Building frontend...
    echo.
    pushd "%CONSOLE_DIR%"

    where npm >nul 2>&1
    if errorlevel 1 (
        echo [qwenpaw-local] ERROR: npm not found.
        echo [qwenpaw-local] Please install Node.js from https://nodejs.org/
        popd
        pause
        exit /b 1
    )

    call :ensure_console_dependencies
    if errorlevel 1 (
        popd
        pause
        exit /b 1
    )

    call :run_console_build
    if errorlevel 1 (
        echo [qwenpaw-local] ERROR: Frontend build failed.
        popd
        pause
        exit /b 1
    )

    popd

    if not exist "%FRONTEND_PKG%" mkdir "%FRONTEND_PKG%"
    xcopy /s /e /y /q "%FRONTEND_DIST%\*" "%FRONTEND_PKG%\" >nul

    echo [qwenpaw-local] Frontend build complete.
) else (
    echo [qwenpaw-local] Frontend already built, skipping.
)

call :sync_frontend_package
if errorlevel 1 (
    echo [qwenpaw-local] ERROR: Failed to sync frontend assets.
    pause
    exit /b 1
)

goto :start_qwenpaw

:ensure_console_dependencies
if /i "%QWENPAW_FORCE_NPM_CI%"=="1" (
    echo [qwenpaw-local] QWENPAW_FORCE_NPM_CI=1, forcing clean dependency install.
    echo [qwenpaw-local] Running npm ci...
    call npm ci
    if errorlevel 1 (
        echo [qwenpaw-local] ERROR: npm ci failed.
        exit /b 1
    )
    exit /b 0
)

if /i "%QWENPAW_FORCE_NPM_INSTALL%"=="1" (
    echo [qwenpaw-local] QWENPAW_FORCE_NPM_INSTALL=1, refreshing console dependencies.
    echo [qwenpaw-local] Running npm install --no-fund --no-audit...
    call npm install --no-fund --no-audit
    if errorlevel 1 (
        echo [qwenpaw-local] ERROR: npm install failed.
        exit /b 1
    )
    exit /b 0
)

if not exist "%CONSOLE_NODE_MODULES%" (
    echo [qwenpaw-local] console\node_modules missing, bootstrapping dependencies with npm ci...
    call npm ci
    if errorlevel 1 (
        echo [qwenpaw-local] ERROR: npm ci failed.
        exit /b 1
    )
    exit /b 0
)

if not exist "%CONSOLE_TSC_JS%" (
    echo [qwenpaw-local] TypeScript package missing, refreshing console dependencies.
    call npm install --no-fund --no-audit
    if errorlevel 1 (
        echo [qwenpaw-local] ERROR: npm install failed.
        exit /b 1
    )
    exit /b 0
)

if not exist "%CONSOLE_VITE_JS%" (
    echo [qwenpaw-local] Vite package missing, refreshing console dependencies.
    call npm install --no-fund --no-audit
    if errorlevel 1 (
        echo [qwenpaw-local] ERROR: npm install failed.
        exit /b 1
    )
    exit /b 0
)

echo [qwenpaw-local] Reusing cached console dependencies.
echo [qwenpaw-local] Set QWENPAW_FORCE_NPM_INSTALL=1 to refresh or QWENPAW_FORCE_NPM_CI=1 for a clean reinstall.

exit /b 0

:run_console_build
if exist "%CONSOLE_TSC_CMD%" if exist "%CONSOLE_VITE_CMD%" (
    echo [qwenpaw-local] Running npm run build...
    call npm run build
    exit /b %errorlevel%
)

if exist "%CONSOLE_TSC_JS%" if exist "%CONSOLE_VITE_JS%" (
    echo [qwenpaw-local] npm shims missing, running TypeScript and Vite directly...
    call node "%CONSOLE_TSC_JS%" -b
    if errorlevel 1 exit /b %errorlevel%
    call node "%CONSOLE_VITE_JS%" build
    exit /b %errorlevel%
)

echo [qwenpaw-local] Frontend toolchain incomplete, refreshing dependencies.
call npm install --no-fund --no-audit
if errorlevel 1 exit /b %errorlevel%

if exist "%CONSOLE_TSC_CMD%" if exist "%CONSOLE_VITE_CMD%" (
    echo [qwenpaw-local] Running npm run build...
    call npm run build
    exit /b %errorlevel%
)

if exist "%CONSOLE_TSC_JS%" if exist "%CONSOLE_VITE_JS%" (
    echo [qwenpaw-local] npm shims still missing, retrying build via direct node entrypoints...
    call node "%CONSOLE_TSC_JS%" -b
    if errorlevel 1 exit /b %errorlevel%
    call node "%CONSOLE_VITE_JS%" build
    exit /b %errorlevel%
)

echo [qwenpaw-local] ERROR: frontend build tools are still unavailable after dependency refresh.
exit /b 1

:sync_frontend_package
if not exist "%FRONTEND_DIST%\index.html" (
    echo [qwenpaw-local] ERROR: console dist is missing.
    exit /b 1
)

if not exist "%FRONTEND_PKG%" mkdir "%FRONTEND_PKG%"
xcopy /s /e /y /q "%FRONTEND_DIST%\*" "%FRONTEND_PKG%\" >nul
if errorlevel 1 exit /b 1

exit /b 0

:start_qwenpaw
REM --- Start QwenPaw ---
echo.
echo ================================================================
echo      Local QwenPaw starting...
echo.
echo   API port: %QWENPAW_PORT% (default: 8088)
echo   WS  port: %QWENPAW_WS_PORT% (default: 6199)
echo   SIP port: %QWENPAW_SIP_PORT% (default: 5061)
echo.
echo   URL: http://127.0.0.1:%QWENPAW_PORT%
echo ================================================================
echo.

"%CONDA_PYTHON%" -m qwenpaw app --port %QWENPAW_PORT%
set "EXIT_CODE=%errorlevel%"

popd

if %EXIT_CODE% neq 0 (
    echo [qwenpaw-local] QwenPaw exited (code: %EXIT_CODE%)
    pause
)

endlocal
