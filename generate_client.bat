call venv\Scripts\activate
cd client
rm -rf generated
call python -m openapi_python_client generate --path ../openapi.yml --output-path generated --meta none --overwrite
pause
