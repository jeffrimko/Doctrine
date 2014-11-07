:: Removes all generated project files.
:: **Dependencies**: None

::=============================================================::
:: COPYRIGHT 2013, REVISED 2013, Jeff Rimko.                   ::
::=============================================================::

:: Set up environment.
@set TITLE=%~n0 "%~dp0"
@cd /d %~dp0 && echo off && title %TITLE%

::=============================================================::
:: SECTION: Main Body                                          ::
::=============================================================::

rd /S /Q __output__ 2>NUL
del /S /Q *.log 2>NUL
del /S /Q *.pyc 2>NUL
