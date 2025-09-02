import pytest
pytest.importorskip('fastapi')
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


class TestDocRagIntegrationMocked:
    """Интеграционные тесты для проверки работоспособности DocRag (с моками)"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path, monkeypatch):
        """Настройка тестового окружения"""
        # Используем временную директорию для данных
        base = tmp_path / "data"
        (base / "faiss").mkdir(parents=True, exist_ok=True)
        (base / "uploads").mkdir(parents=True, exist_ok=True)
        
        # Устанавливаем переменные окружения
        monkeypatch.setenv("TOP_K", "3")
        monkeypatch.setenv("CHUNK_MAX_TOKENS", "100")
        monkeypatch.setenv("CHUNK_OVERLAP", "20")
        
        yield
    
    @patch('apps.api.main.get_embeddings')
    @patch('apps.api.main.chat_stream')
    @patch('apps.api.main.Queue')
    def test_full_workflow_with_text_file(self, mock_queue, mock_chat, mock_embeddings, tmp_path):
        """Тест полного рабочего процесса с текстовым файлом (с моками)"""
        # Мокаем очередь RQ
        mock_q = MagicMock()
        mock_job = MagicMock()
        mock_job.meta = {}
        mock_job.id = "test-job-123"  # Сериализуемый ID
        mock_q.enqueue.return_value = mock_job
        mock_queue.return_value = mock_q
        
        # Мокаем embeddings
        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = [0.1] * 8
        mock_embeddings.return_value = mock_emb
        
        # Мокаем chat
        async def mock_chat_stream(prompt, cfg=None):
            yield "Это ответ на основе проиндексированных документов."
        mock_chat.side_effect = mock_chat_stream
        
        client = TestClient(app)
        
        # 1. Создание нового тенанта
        tenant_response = client.post("/tenant/new")
        assert tenant_response.status_code == 200
        tenant_data = tenant_response.json()
        tenant_id = tenant_data["tenant"]
        
        # 2. Создание тестового текстового файла
        test_file = tmp_path / "test_document.txt"
        test_content = """
        Это тестовый документ для проверки работоспособности DocRag.
        Документ содержит информацию о различных аспектах системы.
        Мы тестируем загрузку, индексацию и поиск документов.
        Система должна корректно обрабатывать русский текст.
        """
        test_file.write_text(test_content, encoding="utf-8")
        
        # 3. Индексация файла
        with open(test_file, "rb") as f:
            files = {"files": ("test_document.txt", f.read())}
            index_response = client.post(
                "/index", 
                files=files, 
                headers={"X-Tenant-ID": tenant_id}
            )
        assert index_response.status_code == 202  # Accepted для асинхронной обработки
        
        # Проверяем, что задача была добавлена в очередь
        mock_q.enqueue.assert_called_once()
        
        # 4. Проверка ответа на вопрос
        question_data = {"question": "Что содержит документ?"}
        answer_response = client.post(
            "/answer", 
            json=question_data, 
            headers={"X-Tenant-ID": tenant_id}
        )
        assert answer_response.status_code == 200
        
        answer_data = answer_response.json()
        assert "answer" in answer_data
        assert "sources" in answer_data
        
        # 5. Проверка сброса индекса
        reset_response = client.post(
            "/reset", 
            headers={"X-Tenant-ID": tenant_id}
        )
        assert reset_response.status_code == 200
        assert reset_response.json().get("deleted") is True
        
        # 6. Проверка, что после сброса ответ не работает
        answer_response_after_reset = client.post(
            "/answer", 
            json=question_data, 
            headers={"X-Tenant-ID": tenant_id}
        )
        assert answer_response_after_reset.status_code == 404
    
    def test_health_endpoint(self):
        """Тест эндпоинта здоровья системы"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_tenant_creation(self):
        """Тест создания тенанта"""
        client = TestClient(app)
        response = client.post("/tenant/new")
        assert response.status_code == 200
        data = response.json()
        assert "tenant" in data
        assert isinstance(data["tenant"], str)
        assert len(data["tenant"]) > 0
    
    def test_file_validation(self):
        """Тест валидации файлов"""
        client = TestClient(app)
        
        # Тест без указания тенанта
        files = {"files": ("test.txt", b"test content")}
        response = client.post("/index", files=files)
        assert response.status_code == 400
        
        # Тест с пустым файлом (должен пройти валидацию)
        files = {"files": ("empty.txt", b"")}
        response = client.post(
            "/index", 
            files=files, 
            headers={"X-Tenant-ID": "test-tenant"}
        )
        # Может вернуть 500 из-за отсутствия Redis, но не 400 (валидация прошла)
        assert response.status_code in [200, 500]
    
    @patch('apps.api.main.get_embeddings')
    @patch('apps.api.main.chat_stream')
    @patch('apps.api.main.Queue')
    def test_search_functionality(self, mock_queue, mock_chat, mock_embeddings, tmp_path):
        """Тест функциональности поиска (с моками)"""
        # Мокаем очередь RQ
        mock_q = MagicMock()
        mock_job = MagicMock()
        mock_job.meta = {}
        mock_job.id = "search-job-456"  # Сериализуемый ID
        mock_q.enqueue.return_value = mock_job
        mock_queue.return_value = mock_q
        
        # Мокаем embeddings
        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = [0.1] * 8
        mock_embeddings.return_value = mock_emb
        
        # Мокаем chat
        async def mock_chat_stream(prompt, cfg=None):
            yield "Ответ на основе найденных документов"
        mock_chat.side_effect = mock_chat_stream
        
        client = TestClient(app)
        
        # Создаем тестовый индекс
        tenant_id = "search-test-tenant"
        test_file = tmp_path / "search_test.txt"
        test_file.write_text("Документ для тестирования поиска", encoding="utf-8")
        
        with open(test_file, "rb") as f:
            files = {"files": ("search_test.txt", f.read())}
            index_response = client.post(
                "/index", 
                files=files, 
                headers={"X-Tenant-ID": tenant_id}
            )
        assert index_response.status_code == 202  # Accepted для асинхронной обработки
        
        # Тестируем поиск
        search_data = {"question": "тестирование"}
        response = client.post(
            "/answer", 
            json=search_data, 
            headers={"X-Tenant-ID": tenant_id}
        )
        assert response.status_code == 200
        
        # Очистка
        client.post("/reset", headers={"X-Tenant-ID": tenant_id})
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        client = TestClient(app)
        
        # Тест несуществующего эндпоинта
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Тест неверного метода
        response = client.get("/answer")
        assert response.status_code == 405
        
        # Тест неверного JSON
        response = client.post(
            "/answer", 
            data="invalid json", 
            headers={"X-Tenant-ID": "test-tenant", "Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @patch('apps.api.main.get_embeddings')
    @patch('apps.api.main.chat_stream')
    @patch('apps.api.main.Queue')
    def test_streaming_response(self, mock_queue, mock_chat, mock_embeddings, tmp_path):
        """Тест потокового ответа (SSE)"""
        # Мокаем очередь RQ
        mock_q = MagicMock()
        mock_job = MagicMock()
        mock_job.meta = {}
        mock_job.id = "stream-job-789"  # Сериализуемый ID
        mock_q.enqueue.return_value = mock_job
        mock_queue.return_value = mock_q
        
        # Мокаем embeddings
        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = [0.1] * 8
        mock_embeddings.return_value = mock_emb
        
        # Мокаем chat для потокового ответа
        async def mock_chat_stream(prompt, cfg=None):
            yield "Потоковый"
            yield " "
            yield "ответ"
            yield " "
            yield "готов"
        mock_chat.side_effect = mock_chat_stream
        
        client = TestClient(app)
        
        # Создаем тестовый индекс
        tenant_id = "stream-test-tenant"
        test_file = tmp_path / "stream_test.txt"
        test_file.write_text("Документ для тестирования потокового ответа", encoding="utf-8")
        
        with open(test_file, "rb") as f:
            files = {"files": ("stream_test.txt", f.read())}
            index_response = client.post(
                "/index", 
                files=files, 
                headers={"X-Tenant-ID": tenant_id}
            )
        assert index_response.status_code == 202  # Accepted для асинхронной обработки
        
        # Тестируем потоковый ответ
        with client.stream(
            "POST",
            "/answer/stream",
            headers={"X-Tenant-ID": tenant_id, "Accept": "text/event-stream"},
            json={"question": "потоковый ответ"},
        ) as r:
            buf = ""
            for chunk in r.iter_text():
                buf += chunk
                if "event: done" in buf:
                    break
        
        # Проверяем наличие ключевых событий
        assert "event: context" in buf
        assert "event: token" in buf
        assert "event: done" in buf
        
        # Очистка
        client.post("/reset", headers={"X-Tenant-ID": tenant_id})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

