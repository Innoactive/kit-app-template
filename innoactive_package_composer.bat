@echo off

REM Delete the specified folder and its contents
if exist ".\_build\windows-x86_64\release\root" (
    rmdir /s /q ".\_build\windows-x86_64\release\root"
    echo Deleted folder: .\_build\windows-x86_64\release\root
) else (
    echo Folder not found: .\_build\windows-x86_64\release\root
)

REM Delete the specified file
if exist ".\_build\windows-x86_64\release\Portal-Omniverse-Wrapper.log" (
    del ".\_build\windows-x86_64\release\Portal-Omniverse-Wrapper.log"
    echo Deleted file: .\_build\windows-x86_64\release\Portal-Omniverse-Wrapper.log
) else (
    echo File not found: .\_build\windows-x86_64\release\Portal-Omniverse-Wrapper.log
)

REM Run the packaging command
cmd /k .\repo.bat package --name innoactive_composer

REM Pause to keep the CMD window open after execution
pause
