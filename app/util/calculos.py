def calcular_prestacao_price(valor_reais: float, taxa_juros_percentual: float, meses: int) -> float:
    """Calcula o valor da parcela usando a Tabela Price."""
    if taxa_juros_percentual <= 0:
        return valor_reais / meses
        
    i = taxa_juros_percentual / 100
    pmt = valor_reais * (i * (1 + i)**meses) / ((1 + i)**meses - 1)
    return pmt

def calcular_margem_comprometida(parcela_reais: float, renda_reais: float) -> float:
    """Retorna o percentual da renda comprometido pela parcela."""
    if renda_reais <= 0:
        return 100.0
    return (parcela_reais / renda_reais) * 100