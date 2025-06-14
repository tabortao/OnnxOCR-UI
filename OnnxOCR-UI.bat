::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCmDJHqL8EcMBzhmcCuMMnOVJYdR3cHH4OSJukIeRt0qcbPayqSxKeMc5AvtdplN
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSzk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJgZkoaHUrSXA==
::ZQ05rAF9IBncCkqN+0xwdVsEAlXMbSXqZg==
::ZQ05rAF9IAHYFVzEqQIfJhVMYyewcV6TZg==
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCmDJHqL8EcMBzhmcCuMMnOVJYdR3cHHwOSJumI+Zq8KUcHewrHu
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
chcp 65001
pushd %~dp0
echo Current directory is: %cd%
echo The program is starting, please wait...
set PYTHON_PATH=.\.venv\Scripts\python.exe
timeout /t 3 /nobreak > nul 
"%PYTHON_PATH%" main.py
pause