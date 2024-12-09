@echo off

REM Copy everything from innoactive_build_template to _build\windows-x86_64\release
xcopy /s /e /y ".\innoactive_build_template\*" ".\_build\windows-x86_64\release\"

if %errorlevel% == 0 (
    echo Files successfully copied to _build\windows-x86_64\release
) else (
    echo Error copying files to _build\windows-x86_64\release
)

REM Pause to keep the CMD window open after execution
pause
