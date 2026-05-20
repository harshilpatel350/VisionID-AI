@echo off
setlocal

echo [VisionID AI] Setting up backend...
cd /d %~dp0..\backend
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [VisionID AI] Setting up frontend...
cd /d %~dp0..\frontend
call npm install

echo [VisionID AI] Done.
endlocal
