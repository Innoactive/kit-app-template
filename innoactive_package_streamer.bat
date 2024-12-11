@echo off

REM Check if the release folder already exists
if exist ".\_build\windows-x86_64\release" (
    echo Error: The folder ".\_build\windows-x86_64\release" already exists.
    pause
    exit /b 1
)

REM Rename the release_composer folder to release
if exist ".\_build\windows-x86_64\release_streamer" (
    rename ".\_build\windows-x86_64\release_streamer" "release"
    echo Renamed folder: .\_build\windows-x86_64\release_streamer to .\_build\windows-x86_64\release
) else (
    echo Error: Folder not found: .\_build\windows-x86_64\release_streamer
    pause
    exit /b 1
)


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
call .\repo.bat package --name innoactive_streamer

REM Undo the rename action
if exist ".\_build\windows-x86_64\release" (
    rename ".\_build\windows-x86_64\release" "innoactive_streamer"
    echo Renamed folder back to: .\_build\windows-x86_64\innoactive_streamer
) else (
    echo Warning: Folder not found for reverting rename: .\_build\windows-x86_64\release
)

REM Pause to keep the CMD window open after execution
pause
