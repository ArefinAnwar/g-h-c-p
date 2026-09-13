@echo off
REM Commit + push this repo (70-pilot at root, Ring500 at ring500/).
REM Pages serves root at / and Ring500 at /ring500/.
setlocal
set BRANCH=main
cd /d %~dp0
git add -A
git diff --cached --quiet
if %errorlevel%==0 (
  echo nothing new to commit
) else (
  git commit -m "Add ring500: 500 ring layouts, 5x100 disjoint reviewer sets + manifest"
)
git push origin %BRANCH%
endlocal
