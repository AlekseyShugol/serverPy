@echo off
REM Переход на две директории вверх
cd ..\..

REM Создание виртуального окружения
python -m venv myenv

REM Активация виртуального окружения
call serverEnv\Scripts\activate


REM Переход в папку config\init
cd start\init


REM Сохранение списка установленных пакетов
pip freeze > requirements.txt

pause


