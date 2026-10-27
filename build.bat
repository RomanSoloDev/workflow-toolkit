@echo off
rem Builds the app into dist\WorkflowToolkit\WorkflowToolkit.exe
rem Run from the project folder with the virtual environment active.
pyinstaller --noconfirm --windowed --name WorkflowToolkit --icon assets\icon.png --add-data "assets;assets" src\main.py