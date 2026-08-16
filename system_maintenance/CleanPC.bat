@echo off
title Enterprise System Maintenance Tool
color 0A

:: --- 1. Privilege Escalation (Admin Check) ---
IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
>nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
) ELSE (
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
)

IF %ERRORLEVEL% NEQ 0 (
    echo Requesting Administrative Privileges...
    goto UACPrompt
) ELSE ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

:: --- 2. Setup Logging Environment ---
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOG_DATE=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%
set LOG_TIME=%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%

set LOG_DIR=D:\System_Maintenance_Logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\Maintenance_Log_%LOG_DATE%_%LOG_TIME%.txt

:: --- 3. Execution Phase ---
cls
echo ===================================================
echo       SYSTEM OPTIMIZATION AND CLEANUP TOOL
echo ===================================================
echo.
echo Initializing maintenance run...
echo Log directory active: %LOG_DIR%
echo.

echo =================================================== > "%LOG_FILE%"
echo SYSTEM MAINTENANCE LOG - %LOG_DATE% %LOG_TIME% >> "%LOG_FILE%"
echo =================================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo [1/4] Clearing Application and System Temp Files...
echo [*] Clearing Application and System Temp Files... >> "%LOG_FILE%"
del /s /f /q "%temp%\*.*" >> "%LOG_FILE%" 2>&1
for /d %%p in ("%temp%\*") do rd /s /q "%%p" >> "%LOG_FILE%" 2>&1
del /s /f /q "C:\Windows\Temp\*.*" >> "%LOG_FILE%" 2>&1
for /d %%p in ("C:\Windows\Temp\*") do rd /s /q "%%p" >> "%LOG_FILE%" 2>&1
echo  - Temp files cleared.
echo  - Temp files cleared. >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo [2/4] Emptying the Recycle Bin...
echo [*] Emptying the Recycle Bin... >> "%LOG_FILE%"
rd /s /q %systemdrive%\$Recycle.bin >> "%LOG_FILE%" 2>&1
echo  - Recycle Bin emptied.
echo  - Recycle Bin emptied. >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo [3/4] Flushing DNS Cache for Network Stability...
echo [*] Flushing DNS Cache for Network Stability... >> "%LOG_FILE%"
ipconfig /flushdns >> "%LOG_FILE%" 2>&1
echo  - DNS Cache flushed.
echo  - DNS Cache flushed. >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo [4/4] Verifying Core System File Integrity...
echo [*] Verifying Core System File Integrity... >> "%LOG_FILE%"
echo  - Running SFC Scan (This may take a few minutes)...
sfc /scannow >> "%LOG_FILE%" 2>&1
echo  - SFC Scan completed.
echo. >> "%LOG_FILE%"

echo =================================================== >> "%LOG_FILE%"
echo END OF LOG >> "%LOG_FILE%"
echo =================================================== >> "%LOG_FILE%"

echo.
echo ===================================================
echo                 MAINTENANCE COMPLETE
echo ===================================================
echo Your system has been safely cleaned and verified.
echo.
echo View your detailed report here: 
echo %LOG_FILE%
echo.
pause
