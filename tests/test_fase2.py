"""Contratos da Fase 2, sem GPU nem microfone."""
import base64
import unittest
from unittest import mock
from tests.test_regressao import memory, jarvis_commands, initializer
import jarvis_vision


class ChatTest(unittest.TestCase):
    def setUp(self):
        memory.clear_history()
        self.reply = mock.Mock()
        self.reply.json.return_value = {'message': {'content': 'Resposta.'}}
        self.patch = mock.patch.object(memory.session, 'post', return_value=self.reply)
        self.post = self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(memory.clear_history)

    def test_chat_e_historico(self):
        memory.llama_query('Minha cor favorita é azul')
        memory.llama_query('Qual é a minha cor?')
        data = self.post.call_args.kwargs['json']
        self.assertTrue(self.post.call_args.args[0].endswith('/api/chat'))
        self.assertFalse(data['think'])
        self.assertEqual([m['role'] for m in data['messages']], ['system','user','assistant','user'])
        self.assertEqual(len(memory.memory_context), 2)

    def test_auxiliares_e_api_isolados(self):
        memory.remember_turn('segredo', 'azul')
        for kwargs in ({'mode':'site'}, {'direct_mode':True}, {'mode':'code'}):
            memory.llama_query('teste', **kwargs)
            self.assertEqual(len(self.post.call_args.kwargs['json']['messages']), 2)
        self.assertEqual(memory.memory_context, [('segredo','azul')])

    def test_limite_memoria(self):
        for i in range(12):
            memory.llama_query(str(i))
        self.assertEqual(len(memory.memory_context), memory.MAX_CONTEXT)
        self.assertEqual(memory.memory_context[0][0], '7')

    def test_falha_e_vazio_nao_entram_na_memoria(self):
        self.reply.json.return_value = {'message': {'content': ''}}
        self.assertIsNone(memory.llama_query('vazio'))
        self.reply.json.return_value = {'error': 'falhou'}
        self.assertIsNone(memory.llama_query('erro'))
        self.assertEqual(memory.memory_context, [])

    def test_reserva_so_apos_recusa_de_codigo(self):
        self.reply.json.side_effect = [
            {'message': {'content': 'Não posso gerar esse código.'}},
            {'message': {'content': '```python\ndef hello_world():\n    return 1\n```'}}]
        result = memory.llama_query('Crie uma função em Python', mode='code')
        self.assertIn('hello_world', result)
        self.assertIn('\n    return', result)
        self.assertEqual(self.post.call_count, 2)
        self.assertEqual(self.post.call_args.kwargs['json']['model'], memory.DEFAULT_MODEL_CODE)

    def test_reserva_indisponivel_preserva_resposta_principal(self):
        failed = mock.Mock()
        failed.raise_for_status.side_effect = ConnectionError('modelo ausente')
        self.reply.json.return_value = {'message': {'content': 'Não posso gerar esse código.'}}
        self.post.side_effect = [self.reply, failed]
        self.assertEqual(memory.llama_query('Escreva código', mode='code'), 'Não posso gerar esse código.')
        self.assertEqual(self.post.call_count, 2)

    def test_resposta_normal_nao_aciona_reserva(self):
        memory.llama_query('Escreva código', mode='code')
        self.assertEqual(self.post.call_count, 1)

    def test_erro_http_nao_aciona_reserva(self):
        self.post.side_effect = ConnectionError('offline')
        self.assertIsNone(memory.llama_query('Escreva código', mode='code'))
        self.assertEqual(self.post.call_count, 1)

    def test_visao_base64(self):
        with mock.patch.object(jarvis_vision.Path, 'stat') as stat, mock.patch.object(jarvis_vision.Path, 'read_bytes', return_value=b'imagem'):
            stat.return_value.st_size = 6
            jarvis_vision.describe_image('teste.png', 'Qual a cor?')
        message = self.post.call_args.kwargs['json']['messages'][-1]
        self.assertEqual(message['images'], [base64.b64encode(b'imagem').decode()])
        self.assertEqual(message['content'], 'Qual a cor?')
        self.assertEqual(memory.memory_context, [])

    def test_voz_nao_usa_cache_por_texto(self):
        with mock.patch.object(jarvis_commands, 'TOOL_ROUTER_ENABLED', False), mock.patch.object(jarvis_commands, 'shutdown_command', return_value=True), mock.patch.object(jarvis_commands, 'handle_weather_query', return_value=False), mock.patch.object(jarvis_commands, 'run_command_handlers', return_value=(False,None)), mock.patch.object(jarvis_commands, 'generate_response', return_value='Nova resposta') as generate, mock.patch.object(jarvis_commands, 'log_interaction'), mock.patch.object(jarvis_commands, 'should_save_to_file', return_value=False):
            jarvis_commands.response_cache['teste'] = 'Velha'
            jarvis_commands.process_command('teste')
            generate.assert_called_once()

    def test_fluxo_voz_e_api(self):
        with mock.patch.object(jarvis_commands, 'is_query_time_sensitive', return_value=False):
            jarvis_commands.generate_response('Explique gravidade')
            self.assertEqual(len(memory.memory_context), 1)
            jarvis_commands.generate_response('Explain gravity', api=True)
            self.assertEqual(len(memory.memory_context), 1)
            self.assertEqual(len(self.post.call_args.kwargs['json']['messages']), 2)

    def test_warmup_usa_mesmo_contexto(self):
        with mock.patch.object(initializer.requests, 'post') as post:
            initializer.warmup_model(memory.DEFAULT_MODEL)
        data = post.call_args.kwargs['json']
        self.assertEqual(data['options']['num_ctx'], memory.OLLAMA_NUM_CTX)
        self.assertEqual(data['messages'], [])

if __name__ == '__main__':
    unittest.main()
