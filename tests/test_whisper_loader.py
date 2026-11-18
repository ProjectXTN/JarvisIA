import contextlib
import io
import unittest
from unittest import mock
from brain import whisper_loader


class WhisperLoaderTest(unittest.TestCase):
    def test_cache_incompleto_volta_cpu_sem_dica_errada_de_cuda(self):
        output = io.StringIO()
        cpu = mock.Mock()
        with mock.patch.object(whisper_loader,'cuda_available',return_value=True), mock.patch.object(whisper_loader,'WHISPER_ALLOW_DOWNLOAD',False), mock.patch.object(whisper_loader.faster_whisper,'WhisperModel',side_effect=[RuntimeError('Unable to open model.bin'),cpu]) as factory, contextlib.redirect_stdout(output):
            model, description = whisper_loader.load_whisper('large-v3-turbo','medium')
        self.assertIs(model,cpu)
        self.assertIn('CPU',description)
        self.assertIn('prepare_whisper',output.getvalue())
        self.assertNotIn('pip install',output.getvalue())
        for call in factory.call_args_list:
            self.assertTrue(call.kwargs['local_files_only'])

    def test_dll_ausente_mostra_dica_cuda(self):
        output = io.StringIO()
        with mock.patch.object(whisper_loader,'cuda_available',return_value=True), mock.patch.object(whisper_loader.faster_whisper,'WhisperModel',side_effect=[RuntimeError('cudnn DLL not found'),mock.Mock()]), contextlib.redirect_stdout(output):
            whisper_loader.load_whisper('base','base')
        self.assertIn('pip install',output.getvalue())

    def test_gpu_valida_percorre_segmentos(self):
        gpu = mock.Mock()
        segments = mock.MagicMock()
        gpu.transcribe.return_value = (segments,None)
        with mock.patch.object(whisper_loader,'cuda_available',return_value=True), mock.patch.object(whisper_loader.faster_whisper,'WhisperModel',return_value=gpu):
            result, description = whisper_loader.load_whisper('base','base')
        self.assertIs(result,gpu)
        self.assertIn('GPU',description)
        segments.__iter__.assert_called_once()

if __name__ == '__main__':
    unittest.main()
