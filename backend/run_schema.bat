@echo off
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root --password=seekrit < schema.sql
echo EXITCODE=%ERRORLEVEL%
