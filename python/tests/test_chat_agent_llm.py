import os
import unittest
from unittest.mock import patch

from uagents.experimental.chat_agent.llm import LLMConfig


class TestOrcaRouterConfig(unittest.TestCase):
    def test_orcarouter_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            LLMConfig.orcarouter()

    def test_orcarouter_defaults(self):
        with patch.dict(os.environ, {"ORCAROUTER_API_KEY": "sk-orca-test"}, clear=True):
            config = LLMConfig.orcarouter()
        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.model, "orcarouter/auto")
        self.assertEqual(config.url, "https://api.orcarouter.ai/v1")
        self.assertEqual(config.api_key, "sk-orca-test")

    def test_orcarouter_base_url_and_model_overrides(self):
        with patch.dict(
            os.environ,
            {
                "ORCAROUTER_API_KEY": "sk-orca-test",
                "ORCAROUTER_BASE_URL": "https://proxy.example.com/v1",
            },
            clear=True,
        ):
            config = LLMConfig.orcarouter(model="deepseek/deepseek-v4-flash")
        self.assertEqual(config.model, "deepseek/deepseek-v4-flash")
        self.assertEqual(config.url, "https://proxy.example.com/v1")
        self.assertEqual(config.api_key, "sk-orca-test")
