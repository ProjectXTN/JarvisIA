import unittest
from unittest import mock
from tests.test_regressao import memory
from brain.websearch import news
from brain.pipeline import super_jarvis


class NewsTest(unittest.TestCase):
    def setUp(self):
        self.items = [{'title':'Título retornado', 'description':'Resumo da fonte',
                       'url':'https://example.org/noticia','date':'há uma hora'}]

    def test_noticias_pulam_rag_e_paginas(self):
        with mock.patch.object(super_jarvis,'news_response',return_value='Manchetes') as answer, mock.patch.object(super_jarvis,'query_rag') as rag, mock.patch.object(super_jarvis,'search_web') as web:
            self.assertEqual(super_jarvis.super_jarvis_query('procure sobre as notícias do dia', conversation=True),'Manchetes')
            answer.assert_called_once_with('procure sobre as notícias do dia',lang='pt',conversation=True)
            rag.assert_not_called()
            web.assert_not_called()

    def test_modelo_lento_devolve_titulos_e_guarda_turno(self):
        with mock.patch.object(news,'fetch_news',return_value=self.items), mock.patch.object(news,'llama_query',return_value=None) as llm, mock.patch.object(news,'remember_turn') as remember:
            answer = news.news_response('notícias do dia',conversation=True)
        self.assertIn('Título retornado',answer)
        self.assertIn('resumo não ficou pronto',answer)
        remember.assert_called_once_with('notícias do dia',answer)
        self.assertEqual(llm.call_args.kwargs['mode'],'news')

    def test_sem_resultados_nao_inventa_nem_chama_llm(self):
        with mock.patch.object(news,'fetch_news',return_value=[]), mock.patch.object(news,'llama_query') as llm:
            answer = news.news_response('notícias do dia')
        self.assertIn('Não consegui obter',answer)
        llm.assert_not_called()

    def test_busca_limitada_com_params_e_recencia(self):
        reply = mock.Mock(status_code=200)
        reply.json.return_value = {'results':[{'title':'<b>Título</b>','description':'x'*3000,'url':f'https://example.org/{i}'} for i in range(10)]}
        with mock.patch.object(news,'BRAVE_API_KEY','test'), mock.patch.object(news.requests,'get',return_value=reply) as get:
            items = news.fetch_news('procure sobre as notícias do dia')
        self.assertEqual(len(items),3)
        self.assertEqual(items[0]['title'],'Título')
        self.assertEqual(len(items[0]['description']),500)
        self.assertEqual(get.call_args.kwargs['params']['freshness'],'pd')
        self.assertEqual(get.call_args.kwargs['params']['q'],'as notícias do dia')
        self.assertEqual(get.call_args.kwargs['timeout'],(3,10))

    def test_historico_nao_forca_ultimas_24h(self):
        reply = mock.Mock(status_code=200)
        reply.json.return_value = {'results':[]}
        with mock.patch.object(news,'BRAVE_API_KEY','test'), mock.patch.object(news.requests,'get',return_value=reply) as get:
            news.fetch_news('notícias de janeiro de 2020')
        self.assertNotIn('freshness',get.call_args.kwargs['params'])

    def test_timeout_e_saida_curtos_no_resumo(self):
        reply = mock.Mock()
        reply.json.return_value = {'message':{'content':'Resumo'}}
        with mock.patch.object(memory.session,'post',return_value=reply) as post:
            self.assertEqual(memory.llama_query('Material',mode='news',direct_mode=True),'Resumo')
        self.assertLessEqual(post.call_args.kwargs['timeout'][1],45)
        self.assertEqual(post.call_args.kwargs['json']['options']['num_predict'],192)

    def test_indice_news_indisponivel_usa_web(self):
        blocked = mock.Mock(status_code=403)
        reply = mock.Mock(status_code=200)
        reply.json.return_value = {'web':{'results':[{'title':'Uma notícia','url':'https://example.org/1'}]}}
        with mock.patch.object(news,'BRAVE_API_KEY','test'), mock.patch.object(news.requests,'get',side_effect=[blocked,reply]) as get:
            self.assertEqual(len(news.fetch_news('notícias do dia')),1)
        self.assertTrue(get.call_args.args[0].endswith('/web/search'))

if __name__ == '__main__':
    unittest.main()
