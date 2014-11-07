:: Builds a Windows EXE from the Python scripts.
:: **Dependencies**:
:: PyInstaller must have a wrapper batch file on the PATH.

::=============================================================::
:: COPYRIGHT 2013, REVISED 2013, Jeff Rimko.                   ::
::=============================================================::

:: Set up environment.
@set TITLE=%~n0 "%~dp0"
@cd /d %~dp0 && echo off && title %TITLE%

::=============================================================::
:: SECTION: Global Definitions                                 ::
::=============================================================::

:: Output directory for build.
set OUTDIR=__output__

:: Set up optional PAUSE.
if "%1" equ "nopause" (set PAUSE=) else (set PAUSE=pause)

::=============================================================::
:: SECTION: Main Body                                          ::
::=============================================================::

mkdir %OUTDIR% 2>NUL
pyinstaller doctrine.spec
mv *.log %OUTDIR% 2>NUL
mv build %OUTDIR% 2>NUL
mv dist %OUTDIR% 2>NUL
%PAUSE%
exit /b 0
