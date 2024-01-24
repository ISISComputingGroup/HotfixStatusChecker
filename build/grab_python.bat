@echo off
setlocal

REM Set the source and destination paths
set "sourceDir=\\isis\inst$\Kits$\CompGroup\ICP\genie_python_3\BUILD-2613"
set "destinationDir=C:\HotfixStatusChecker\Python3"

REM Copy python3 directory
copy /E /D "%sourceDir%\Python\python3" "%destinationDir%\Python3\python3.exe"

REM Copy pip3.exe
copy /Y "%sourceDir%\Scripts\pip3.exe" "%destinationDir%\pip3.exe"

echo Copy completed successfully.
