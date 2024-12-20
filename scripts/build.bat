@echo off
setlocal enabledelayedexpansion

g++ --version

for %%f in ("%~dp0..") do set root=%%~ff
echo Got root of repository: %root%
if not exist %root%\build mkdir %root%\build

echo Building main.exe
set params=-Wall -std=c++20
if "%1"=="debug" (
    set params=!params! -g -D DEBUG
    echo Building in debug mode

) else (
    set params=!params! -O3
    echo Building normally
)

set command=g++ %params% -D A_STAR %root%/src/main.cpp -o %root%/build/a_star.exe
echo Running "%command%"
%command%

set command=g++ %params% -D BFS %root%/src/main.cpp -o %root%/build/bfs.exe
echo Running "%command%"
%command%
