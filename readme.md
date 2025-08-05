# FluxGuard

FluxGuard — это библиотека для автоматического мониторинга и адаптации асинхронного кода в Python. Она анализирует runtime-потоки (flows), выявляет проблемы вроде deadlocks, race conditions и bottlenecks, генерирует отчёты и предлагает автофиксы. Поддерживает asyncio, trio и gevent. Идеально для веб-приложений (FastAPI, Django) и долгоживущих проектов, где код "стареет" и нуждается в оптимизации.

## Ключевые фичи:

* Динамический граф потоков с выявлением проблем.
* Автофиксы через "guards" (мини-функции для предотвращения issues).
* Хранение истории и "обучение" на прошлых запусках.
* Логирование отчётов в файл (fluxguard.log) с деталями эндпоинтов.
* Минимальный overhead, настраиваемые thresholds.

## Быстрый старт

### 1. Через PyPI

```bash
    pip install fluxguard
```

### 2. Из whl (локальная установка)
```bash
    pip install fluxguard-0.1.0-py3-none-any.whl
```

## Как использовать
FluxGuard проста в использовании: оберните асинхронную функцию декоратором @guard_coroutine, и она начнёт мониторинг. Библиотека автоматически собирает данные, анализирует и логирует отчёты в fluxguard.log. Вот пошаговое руководство с примерами.

### Базовое использование (asyncio)
Оберните функцию для мониторинга. Библиотека проанализирует runtime и сгенерирует отчёт.

```python
    import asyncio
    import fluxguard

    @fluxguard.guard_coroutine
    async def my_async_func():
        await asyncio.sleep(1.5)  # Симулируем bottleneck для анализа
        print("Task completed")

    if __name__ == "__main__":
        asyncio.run(my_async_func())  # Запуск: Отчёт в fluxguard.log
```

### Использование с Gevent
Если ваш код использует gevent (greenlets), библиотека автоматически активирует адаптер и мониторит spawn.

```python
    import gevent
    import fluxguard

    @fluxguard.guard_coroutine
    async def my_gevent_func():
        def sub_task():
            gevent.sleep(1.0)  # Симулируем задачу
            print("Sub-task done")

        greenlet = gevent.spawn(sub_task)  # Мониторится автоматически
        greenlet.join()
        print("Main task done")

    if __name__ == "__main__":
        import asyncio
        asyncio.run(my_gevent_func())  # Отчёт в fluxguard.log с данными от greenlet
```

### Интеграция с FastAPI (веб-приложения)
Оберните эндпоинты для мониторинга API-запросов.

```python
    from fastapi import FastAPI
    import fluxguard
    import asyncio

    app = FastAPI()

    @app.get("/")
    @fluxguard.guard_coroutine
    async def root():
        await asyncio.sleep(1.0)  # Для анализа
        return {"message": "Hello World"}

    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

```

## Интерпретация отчётов

* Summary: node_count (узлы в графе), issue_count (проблемы), fix_count (предложения).
* Graph Summary: Узлы с durations, depends_on, resources (для race/deadlock).
* Detected Issues: Список (e.g., 'bottleneck' если duration > threshold, 'race_condition' при overlapping access).
* Suggested Fixes: Код-сниппеты для исправления (из guards.py).
* Если отчёт пустой: Добавьте async-операции (sleep/gather/locks) или log_event вручную для сбора данных.

## Тестирование

* Запустите ваш сервер: python main.py (или uvicorn main:app --reload).
* Выполните запросы (POST/GET) — проверьте fluxguard.log на наличие полных отчётов с именами эндпоинтов и данными от gevent (если используете gevent.spawn в коде).

## Если проблемы
* Ошибки сборки: Пришлите лог (вывод python -m build) — часто из-за отсутствующих импортов в setup.py или неправильной структуры (файлы не в подпапке fluxguard/).
* Версия Python: Убедитесь в Python 3.7+ (python --version).
* Gevent: Установите pip install gevent в venv, если используете его в тестовом коде.

# Контакты
* GitHub: https://github.com/ksen145/fluxguard
* Email: ksen10405@gmail.com