"""Testes para SegmentacaoService."""
import pytest
from app.services.segmentacao_service import SegmentacaoService


def test_obter_mensagem_boas_vindas_start():
    """Testa obtenção de mensagem de boas-vindas para Start."""
    mensagem = SegmentacaoService.obter_mensagem_boas_vindas("Start")
    
    assert "Start" in mensagem
    assert len(mensagem) > 0


def test_obter_mensagem_boas_vindas_hub():
    """Testa obtenção de mensagem de boas-vindas para Hub."""
    mensagem = SegmentacaoService.obter_mensagem_boas_vindas("Hub")
    
    assert "Hub" in mensagem
    assert len(mensagem) > 0


def test_obter_mensagem_massiva_start():
    """Testa obtenção de mensagem massiva para Start."""
    mensagem = SegmentacaoService.obter_mensagem_massiva("Start")
    
    assert "Start" in mensagem
    assert len(mensagem) > 0


def test_obter_mensagem_massiva_hub():
    """Testa obtenção de mensagem massiva para Hub."""
    mensagem = SegmentacaoService.obter_mensagem_massiva("Hub")
    
    assert "Hub" in mensagem
    assert len(mensagem) > 0


def test_personalizar_mensagem():
    """Testa personalização de mensagem."""
    template = "Olá {nome}, bem-vindo à {empresa}!"
    dados = {"nome": "João", "empresa": "XYZ"}
    
    mensagem = SegmentacaoService.personalizar_mensagem(template, dados)
    
    assert "João" in mensagem
    assert "XYZ" in mensagem
    assert "{nome}" not in mensagem
    assert "{empresa}" not in mensagem


def test_personalizar_mensagem_sem_dados():
    """Testa personalização sem dados."""
    template = "Mensagem padrão"
    mensagem = SegmentacaoService.personalizar_mensagem(template)
    
    assert mensagem == template

