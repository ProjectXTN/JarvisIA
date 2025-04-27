import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from brain.weatherAPI import get_weather

def test_get_weather_default_city():
    """
    Testa a função de previsão do tempo para a cidade padrão (São Paulo).
    """
    print("[TEST] Rodando teste: Previsão para cidade padrão...")
    result = get_weather()
    print(f"Resultado: {result}")
    assert isinstance(result, str), "A resposta deve ser uma string."
    assert "São Paulo" in result or "clima" in result.lower(), "A resposta deve conter informações de clima."

def test_get_weather_custom_city():
    """
    Testa a função de previsão do tempo para uma cidade específica.
    """
    print("[TEST] Rodando teste: Previsão para cidade customizada (Rio de Janeiro)...")
    result = get_weather("Rio de Janeiro")
    print(f"Resultado: {result}")
    assert isinstance(result, str), "A resposta deve ser uma string."
    assert "Rio de Janeiro" in result or "clima" in result.lower(), "A resposta deve mencionar a cidade ou clima."
    
def test_get_weather_lexy():
    """
    Testa a função de previsão do tempo para a cidade de Lexy, França.
    """
    print("[TEST] Rodando teste: Previsão para Lexy, França...")
    result = get_weather("Lexy")
    print(f"Resultado: {result}")
    assert isinstance(result, str), "A resposta deve ser uma string."
    assert "Lexy" in result or "clima" in result.lower() or "frança" in result.lower(), "A resposta deve mencionar Lexy ou clima."

def test_get_weather_invalid_city():
    """
    Testa a função para uma cidade inválida para ver se lida corretamente com o erro.
    """
    print("[TEST] Rodando teste: Previsão para cidade inválida...")
    result = get_weather("CidadeInventada123")
    print(f"Resultado: {result}")
    assert "não consegui" in result.lower() or "erro" in result.lower(), "Deve retornar erro ou não encontrado."

def test_get_weather_forecast():
    """
    Testa a previsão para a próxima semana (forecast) para uma cidade.
    """
    print("[TEST] Rodando teste: Previsão para a próxima semana (Lexy)...")
    result = get_weather("Lexy", forecast=True)
    print(f"Resultado: {result}")
    assert isinstance(result, str), "A resposta deve ser uma string."
    assert "previsão para os próximos dias" in result.lower(), "Deve mencionar que é uma previsão para os próximos dias."
    
    # Verifica se contém datas no formato DD-MM
    pattern = r"\d{2}-\d{2}"
    assert re.search(pattern, result), "Deve conter datas no formato dia-mês."

if __name__ == "__main__":
    test_get_weather_default_city()
    test_get_weather_custom_city()
    test_get_weather_invalid_city()
    test_get_weather_lexy()
    test_get_weather_forecast()
    print("\n✅ Todos os testes passaram!")
