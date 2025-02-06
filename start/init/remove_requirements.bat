@echo off
REM Переход на две директории вверх
cd ..\..


REM Активация виртуального окружения
call serverEnv\Scripts\activate

REM Обновление pip

REM Переход в папку config\init
cd start\init

REM Удаление библиотек из requirements.txt
if exist requirements.txt (
    echo Удаление библиотек из requirements.txt...
    pip uninstall -r requirements.txt -y
) else (
    echo Файл requirements.txt не найден!
)


pause