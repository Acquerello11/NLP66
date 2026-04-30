@echo off
cd /d C:\Users\427\Desktop\660550GH\NLP66
if exist .venv\Scripts\activate.bat (
	call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
	call venv\Scripts\activate.bat
) else (
	echo No virtual environment activation script found. Continuing without activation.
)
start /min python start.py