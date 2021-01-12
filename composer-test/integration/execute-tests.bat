@echo off

rem ###################################################################
rem #Script Name	:execute-tests.bat
rem #Description	:Script file used to configure and execute integration tests
rem #Args           :
rem #Author         :Damian McDonald
rem #Credits        :Damian McDonald
rem #License        :GPL
rem #Version        :1.0.0
rem #Maintainer     :Damian McDonald
rem #Status         :Development
rem ###################################################################

rem # set python specific variables
set PYTHONPATH=D:\Devel\source\composer-dag-ds\

rem # set pytest specific environment variables
set TEST_BUCKET=test-composer
set TEST_GIT_URL=https://github.com/damianmcdonald/composer-dag-dsl.git
set TEST_GIT_FILE_PATH=composer-test/integration/api/static/dag_workflow_simple.py

rem # set application specific environment variables
set LOG_LEVEL=DEBUG
set GIT_PYTHON_GIT_EXECUTABLE=D:/Devel/apps/PortableGit/bin/git.exe
set PROJECT_ID=playground-s-11-6997d22b
set GCP_LOCATION=europe-west3
set COMPOSER_ENVIRONMENT=composer
rem # GOOGLE_APPLICATION_CREDENTIALS is the minified and base64 encoded version of a GCP service account key in JSON format
set GOOGLE_APPLICATION_CREDENTIALS=eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6InBsYXlncm91bmQtcy0xMS02OTk3ZDIyYiIsInByaXZhdGVfa2V5X2lkIjoiMzI1ZmZiNjc0NjM5MzUzYjk1MjBkYjFlMWE0MGI5MTgwZGQ2YTI3MyIsInByaXZhdGVfa2V5IjoiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdndJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLa3dnZ1NsQWdFQUFvSUJBUUMyaXFUK1ptZWlxTVN5XG5VUXZhVGduNkFMbVdWS3FnNnZGMm5NY01OUmJrK1BHSTBzZTNYUXZyZEhZb25TOTRrMjYvZnp6T2d2OEc1d24yXG5YSHhqdG5JVnplQTJYUElDenpJQ0J1ODFTYkVPNmllQkd1L21PTFNPRjB3WnBWZXM2OS9jckI3ZUNScUd5T1BvXG40cnlQZjFKSDZGNVBzV3NyNHVCRzNCVDFMYmlJZXBMREtXQytGbEZXdnpTb2hFaEZzMitWeTgvejNmcHNmTGllXG56ZlAxa3pzOG05dUhsTitOQVZPeFlINWpMeFFvaDIxMVJwZjZKeUEzWmZwUXI2enNub2lFUmNsQjRZWVJ4QjRrXG5BQ2l5TFNnNVBxbG9OVEdweEFLQmxDVE53NURtZnFwOEd4N203SXZURC9qbFdZMGMyUTFobm1YRExDVlBYY1p6XG5SR0s2eWdUekFnTUJBQUVDZ2dFQUV0U2o4ZjBpWjhIbjQwcVZERzkzSnF2TnpxenI3OW0zWmJoYW1FUjBiaWtpXG4wWU15U0dvaTFxYVc5eTJhazJKY3p3aG9mMjA5WGJycnZpeGdSZkVHUFNyckhFWGpwQUtOSFc4VnNpRG9wbFNRXG5GVjRhclZ5SzA3V2lOaFc3d1FJOEtsN2ZJdmM4SGZka3BodVlhV2ZiQWNGVGZxa2JiZFdPWHF1ZXhkbHlRSWNuXG56OC8xTjlrWnNyME5GSnB0c0YxZ3JKNi82M2sydjhvSlozNnpvTDBVN0M1bjRKdXkrYWZzOVVYS1d0Q1pzSXBSXG5EZFBkTDF2RTRIdG9RQm5zU1BUdGh0cjFaVEorVlVrVUViL1FoZlJjSDFIcnEvOVY4Y3dNYlE5ekJYVVRuN3dUXG5PR0tYUTI2R1dUYXBnSVkrdis2SVpGY2pTaE9UMTFua2x6VXF4MklnRVFLQmdRRGxnR25ZeFcwUmF0Yk9iZHo4XG5HRGRGa2sxdUViRE1SWmpTWlRCOWpzdWlybVV4d1NHZ0c2UUZiR0xXVDVxRXZFYVNucWxFMms3NGdNN2lHWFpRXG5yK3EraVk1cGlLWHFuZ1ZFclo3bWljd0p4eGhXQ3RBV1cvMi9MOFlQS0pmL21zRmdPcWtpK2tmYUdKYXIzZnNzXG5UQkwrRW9icy96SkhCMkVERGhiRU43RU9ad0tCZ1FETG5qRGMrYldXQW9YNnh6c2tGZGRvUS8wak9DUGJWckt0XG52eUI4dFZ6Z2VuK0Q2OVBTZHFHeG9wNHlsOHc2d3ZkbzlQbEFIcXdZWitUTEZxY1U0NnZMSmhlcnB0d0FJa0UxXG5md1NOU3ZTZDl6d1pWUE5WZVVVdWdHOTk4YzYwUjFWR0REWnlWK25TSUY3K3BzdGlYN3VTUGZnQnBMRHFnOEFIXG5QQjJEbE1KbGxRS0JnUUNxQWlwbXJqbFJnYmVHUzlRNzJ5UjJvUjVDdjFBY3dpR25HZGFGN0ZYbE9STTFmRUFRXG5mdWxPS3pBOFdkTzVLRStQSllGMnc5RmtQT2NFanFBYXZYWkRsMXFyeXRJOXJybHdXcjB2UWp5bnNaalJoRWtKXG5oek85Z1FKVEVGc291ZGN1RmNaZFp0SDdPZVBEaFRrZlkydGVVeE1vVlJORmtxM0d1WlViM2JXSFdRS0JnUURJXG53ejdXZ25laVl2YUxYMmxXbVJwOHVaeWIzenlyaFg1RGhkR1laSklnMjJkalFXRG5nUVRJeXRoRWRodHVUTkg0XG44S0hac09ScVkvWFlzSXNwTTVvdGdXK1JWY0pSZDNUb05FYmVzV3NqWGFRcUxmS0c4ajFlTGxDLzAyM0ZueGZiXG5LeXQ3N21halFqdW54ZmwvRTNrMEpsbWo5U2hpOG1paU9ZbTROVEsvU1FLQmdRRERJSXhNRDFPRk41dTZ3Rm5SXG5za3FXZExHR3k2UzlFc3hCd3ppTFM3SkVsYVJZR2swbUI0azF2V0p5NUNLaVVKSGtOdDhTTm45aEc5eEhabThGXG5RTXA2a2Q1VU5mNGVWUGUzWlhiOCtsQmloK0xiRGJzcTFQS0lleElxNFFyVExEbU1LbEhkdlNTNG5NSjQwRElIXG5qUWxwaHl3MUc3NHJxa3AraHFHSTBrd053dz09XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLCJjbGllbnRfZW1haWwiOiJzYS1jb21wb3NlckBwbGF5Z3JvdW5kLXMtMTEtNjk5N2QyMmIuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCJjbGllbnRfaWQiOiIxMDQ1OTEwNTY5MDc4NzM0OTIzMTkiLCJhdXRoX3VyaSI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwidG9rZW5fdXJpIjoiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCJhdXRoX3Byb3ZpZGVyX3g1MDlfY2VydF91cmwiOiJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLCJjbGllbnRfeDUwOV9jZXJ0X3VybCI6Imh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvc2EtY29tcG9zZXIlNDBwbGF5Z3JvdW5kLXMtMTEtNjk5N2QyMmIuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20ifQ==

rem # executes the full test suite
python -m pytest --disable-pytest-warnings -rP

rem # executes a specific test class
rem # python -m pytest --disable-pytest-warnings -rP airflow/airflow_service_test.py

rem # executes a specific test case within a specific test class
rem # python -m pytest --disable-pytest-warnings -rP api/api_test.py::test_trigger_dag