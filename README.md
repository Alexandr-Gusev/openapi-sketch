# openapi-sketch

Пример OpenAPI-клиента и сервера на FastAPI.

## Требования

- Windows
- Node.js
- Python 3.11

## Порядок запуска

Из корня репозитория:

1. `create_venv.bat` — создать виртуальное окружение Python 3.11
2. `install_packages.bat` — установить npm- и pip-зависимости
3. `lint.bat` — проверить `openapi.yml` через Spectral
4. `generate_server.bat` — сгенерировать серверный код и прогнать contract-тест
5. `generate_client.bat` — сгенерировать клиентский код
6. `start_server.bat` — запустить API (`http://localhost/api/1.0`, debugpy на порту 5678)
7. `start_cient.bat` — запустить клиентский пример
