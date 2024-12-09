@echo off

REM Run the build command
call .\repo.bat build

REM Apply the template
call .\innoactive_apply_template.bat

REM Pause to keep the CMD window open after execution
pause
