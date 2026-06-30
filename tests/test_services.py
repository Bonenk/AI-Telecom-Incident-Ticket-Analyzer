import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import patch, MagicMock, mock_open

from app.services.summarizer import summarize_ticket, compute_priority
from app.services.s3_service import S3Service
from app.services.llm_service import LLMFactory


class TestSummarizer:
    @patch("app.services.summarizer.LLMFactory.get_llm")
    def test_summarize_ticket(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.return_value = "Network outage ticket requiring immediate attention."
        mock_llm.invoke.return_value = "Network outage ticket requiring immediate attention."
        mock_get_llm.return_value = mock_llm

        result = summarize_ticket({
            "subject": "Fiber cut",
            "description": "Major fiber cut affecting 500 customers",
            "category": "Network",
            "severity": "Critical",
        })
        assert "Network" in result or "outage" in result.lower()

    @patch("app.services.summarizer.LLMFactory.get_llm")
    def test_compute_priority(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.return_value = '{"score": 85, "reason": "Service outage"}'
        mock_llm.invoke.return_value = '{"score": 85, "reason": "Service outage"}'
        mock_get_llm.return_value = mock_llm

        result = compute_priority({
            "category": "Network",
            "severity": "Critical",
            "description": "Full outage",
        })
        assert result["score"] == 85
        assert "Service outage" in result["reason"]

    @patch("app.services.summarizer.LLMFactory.get_llm")
    def test_compute_priority_fallback(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.return_value = "bad json"
        mock_llm.invoke.return_value = "bad json"
        mock_get_llm.return_value = mock_llm

        result = compute_priority({
            "category": "Network",
            "severity": "Critical",
            "description": "Full outage",
        })
        assert result["score"] == 50
        assert "fallback" in result["reason"]


class TestS3Service:
    @patch("app.services.s3_service.boto3.client")
    def test_upload_file(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        s3 = S3Service()
        # Reset bucket check calls since __init__ calls _ensure_bucket
        s3.client.upload_file.return_value = None

        key = s3.upload_file(Path("/tmp/test.pdf"), "pdfs/test.pdf")
        assert key == "pdfs/test.pdf"
        s3.client.upload_file.assert_called_once()

    @patch("app.services.s3_service.boto3.client")
    def test_list_files(self, mock_boto_client):
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [{"Key": "pdfs/a.pdf"}, {"Key": "pdfs/b.pdf"}]
        }
        mock_boto_client.return_value = mock_client

        s3 = S3Service()
        files = s3.list_files("pdfs/")
        assert files == ["pdfs/a.pdf", "pdfs/b.pdf"]

    @patch("app.services.s3_service.boto3.client")
    def test_file_exists_true(self, mock_boto_client):
        mock_client = MagicMock()
        mock_client.head_object.return_value = {}
        mock_boto_client.return_value = mock_client

        s3 = S3Service()
        assert s3.file_exists("pdfs/test.pdf") is True

    @patch("app.services.s3_service.boto3.client")
    def test_file_exists_false(self, mock_boto_client):
        mock_client = MagicMock()
        mock_client.head_object.side_effect = Exception("Not found")
        mock_boto_client.return_value = mock_client

        s3 = S3Service()
        assert s3.file_exists("pdfs/test.pdf") is False


class TestLLMFactory:
    def test_get_llm_openai(self):
        with (
            patch("app.services.llm_service.LLMConfig") as MockConfig,
            patch("app.services.llm_service.ChatOpenAI") as MockChat,
        ):
            cfg = MagicMock()
            cfg.provider = "openai"
            cfg.openai_model = "gpt-4o"
            cfg.openai_api_key = "sk-test"
            MockConfig.return_value = cfg

            mock_instance = MagicMock()
            MockChat.return_value = mock_instance

            LLMFactory._instances.clear()
            llm = LLMFactory.get_llm(temperature=0.0, max_tokens=256)
            assert llm == mock_instance
            MockChat.assert_called_once_with(
                model="gpt-4o", temperature=0.0, max_tokens=256, api_key="sk-test"
            )

    def test_get_llm_openrouter(self):
        with (
            patch("app.services.llm_service.LLMConfig") as MockConfig,
            patch("app.services.llm_service.ChatOpenAI") as MockChat,
        ):
            cfg = MagicMock()
            cfg.provider = "openrouter"
            cfg.openrouter_model = "openai/gpt-4o"
            cfg.openrouter_api_key = "sk-or-test"
            cfg.openrouter_base_url = "https://openrouter.ai/api/v1"
            cfg.openrouter_site_url = "https://example.com"
            cfg.openrouter_site_name = "Test App"
            MockConfig.return_value = cfg

            mock_instance = MagicMock()
            MockChat.return_value = mock_instance

            LLMFactory._instances.clear()
            llm = LLMFactory.get_llm(temperature=0.0, max_tokens=256)
            assert llm == mock_instance
            MockChat.assert_called_once_with(
                model="openai/gpt-4o",
                temperature=0.0,
                max_tokens=256,
                api_key="sk-or-test",
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://example.com",
                    "X-Title": "Test App",
                },
            )

    def test_get_llm_unsupported(self):
        with patch("app.services.llm_service.LLMConfig") as MockConfig:
            cfg = MagicMock()
            cfg.provider = "unknown"
            MockConfig.return_value = cfg

            LLMFactory._instances.clear()
            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                LLMFactory.get_llm()
