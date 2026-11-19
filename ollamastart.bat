@echo off
REM ============================================================
REM  start-ollama-network.bat
REM  Starts Ollama and exposes it on your local network so other
REM  devices (or your recruitment app running elsewhere) can call it.
REM ============================================================

echo Configuring Ollama to listen on all network interfaces...
set OLLAMA_HOST=0.0.0.0:11434
setx OLLAMA_HOST "0.0.0.0:11434" >nul

echo.
echo Starting Ollama server in a new window...
start "Ollama Server" cmd /k "ollama serve"

echo Waiting for the server to come up...
timeout /t 4 /nobreak >nul

echo.
echo Making sure llama2:latest is pulled...
ollama pull llama2:latest

echo.
echo ============================================================
echo  Ollama is running and reachable from other devices at:
echo ============================================================
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4 Address"') do (
    for /f "tokens=1" %%b in ("%%a") do echo    http://%%b:11434
)
echo.
echo  On THIS machine, use:      http://localhost:11434
echo  API endpoint to call:      http://YOUR_IP:11434/api/generate
echo  List available models:     http://YOUR_IP:11434/api/tags
echo ============================================================
echo.
echo NOTE: If other devices still can't connect, allow the port
echo through Windows Firewall (run as Administrator):
echo   netsh advfirewall firewall add rule name="Ollama" dir=in action=allow protocol=TCP localport=11434
echo.
pause