@echo off
REM Переход на две директории вверх
cd ..\..

REM Проверка наличия виртуального окружения
if not exist "serverEnv\Scripts\activate" (
    echo Создание виртуального окружения...
    python -m venv serverEnv
)

REM Активация виртуального окружения
call serverEnv\Scripts\activate

REM Обновление pip
py -m pip install --upgrade pip

REM Переход в папку config\init
cd start\init

REM Установка библиотек из requirements.txt
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo Файл requirements.txt не найден!
)

pause