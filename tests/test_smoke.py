from __future__ import annotations

import importlib
import os
from pathlib import Path
import pkgutil
import tempfile
import unittest
from unittest.mock import patch

import pycoding_agent
from pycoding_agent.domain.messages import AssistantMessage, CustomMessage, DefaultMessageConverter, ToolCall, ToolResultMessage
from pycoding_agent.domain.models import ModelContext, ModelSpec
from pycoding_agent.providers.fake import FakeProvider
from pycoding_agent.providers.openai_compatible import OpenAICompatibleProvider
from pycoding_agent.runtime.agent import Agent, AgentState
from pycoding_agent.tools import EditTool, ReadTool, ToolRegistry
from pycoding_agent.web import STATIC_DIR, WebConfig, create_app


class PackageSmokeTests(unittest.TestCase):
    def test_runtime_modules_import(self):
        imported = []
        for module in pkgutil.walk_packages(pycoding_agent.__path__, 'pycoding_agent.'):
            if module.name.endswith('.__main__'):
                continue
            importlib.import_module(module.name)
            imported.append(module.name)
        self.assertGreater(len(imported), 40)

    def test_static_resources_present(self):
        for name in ('index.html', 'app.js', 'styles.css', 'marked-18.0.14.umd.js',
                     'dompurify-3.4.16.min.js', 'marked-LICENSE.txt', 'dompurify-LICENSE.txt'):
            self.assertTrue((STATIC_DIR / name).is_file(), name)

    def test_web_startup_and_course_without_model(self):
        from fastapi.testclient import TestClient
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / 'workspace'
            workspace.mkdir()
            (workspace / '.git').mkdir()
            isolated_home = root / 'user'
            isolated_home.mkdir()
            with patch('pathlib.Path.home', return_value=isolated_home), patch.dict(os.environ, {
                'RAG_EMBEDDING_PROVIDER': 'hashing', 'RAG_RERANK_PROVIDER': 'feature',
            }):
                app = create_app(WebConfig(workspace=workspace, environment_scan=False,
                                          trust_project=False, event_log=False))
                with TestClient(app) as client:
                    self.assertEqual(client.get('/').status_code, 200)
                    self.assertEqual(client.get('/api/health').status_code, 200)
                    self.assertGreaterEqual(len(app.state.runtime.knowledge.list_documents()), 6)

    def test_provider_payload_and_message_filter(self):
        converter = DefaultMessageConverter()
        context = ModelContext('system', converter.convert((
            CustomMessage('memory', 'project constraint', display=False),
            CustomMessage('checkpoint', 'private state', include_in_context=False),
        )), ToolRegistry([ReadTool()]).definitions())
        provider = OpenAICompatibleProvider(base_url='http://127.0.0.1:11434/v1')
        payload = provider._payload(ModelSpec('openai-compatible', 'smoke'), context, stream=True)
        self.assertEqual(payload['messages'][0]['role'], 'system')
        self.assertEqual(len(payload['messages']), 2)
        self.assertEqual(payload['tools'][0]['function']['name'], 'read')


class AgentSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_read_edit_feedback_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'config.py'
            target.write_text('PORT = 8000\n', encoding='utf-8')
            provider = FakeProvider([
                AssistantMessage(tool_calls=(ToolCall('r1', 'read', {'path': 'config.py'}),), stop_reason='tool_calls'),
                AssistantMessage(tool_calls=(ToolCall('e1', 'edit', {
                    'path': 'config.py', 'old_text': 'PORT = 8000', 'new_text': 'PORT = 8123',
                }),), stop_reason='tool_calls'),
                AssistantMessage(content='finished'),
            ])
            agent = Agent(state=AgentState(ModelSpec('fake', 'smoke'), 'test'), provider=provider,
                          tools=ToolRegistry([ReadTool(), EditTool()]), workspace=root,
                          enable_coding_evidence=True)
            result = await agent.prompt('Set the project port to 8123.')
            self.assertEqual(result.content, 'finished')
            self.assertEqual(target.read_text(encoding='utf-8'), 'PORT = 8123\n')
            self.assertEqual(len(provider.requests), 3)
            results = [m for m in agent.state.messages if isinstance(m, ToolResultMessage)]
            self.assertEqual(len(results), 2)
            self.assertTrue(all(not item.is_error for item in results))


if __name__ == '__main__':
    unittest.main()
