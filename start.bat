@echo off
echo Lancement de l'application d'extraction de prospects...
echo.
echo 1. Activation de l'environnement virtuel...
call venv\Scripts\activate

echo 2. Lancement de l'application Flask...
python src\web_interface.py

pause
