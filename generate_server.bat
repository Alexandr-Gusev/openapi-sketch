call venv\Scripts\activate
cd server
rm -rf generated
call python -m fastapi_code_generator --input ../openapi.yml --output generated -p 3.11
call python -m pytest -vv test_contract.py
pause
