import pytest
pytest.importorskip('fastapi')
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


class TestDocRagIntegration:
    """Интеграционные тесты для проверки работоспособности DocRag"""
    
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
    
    def test_full_workflow_with_text_file(self, tmp_path):
        """Тест полного рабочего процесса с текстовым файлом"""
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
        assert index_response.status_code == 200
        
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
        assert len(answer_data["sources"]) > 0
        
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
        
        # Тест с пустым файлом
        files = {"files": ("empty.txt", b"")}
        response = client.post(
            "/index", 
            files=files, 
            headers={"X-Tenant-ID": "test-tenant"}
        )
        assert response.status_code == 200
    
    @patch('apps.api.main.get_embeddings')
    @patch('apps.api.main.chat_stream')
    def test_search_functionality(self, mock_chat, mock_embeddings, tmp_path):
        """Тест функциональности поиска"""
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
        assert index_response.status_code == 200
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
