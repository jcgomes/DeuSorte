# api_client.py
import requests
import time
import json

class LotteryAPIClient:
    def __init__(self):
        self.base_url = "https://loteriascaixa-api.herokuapp.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def buscar_ultimos_resultados(self, loteria: str, limite: int = 100):
        """Buscar últimos resultados - CORRIGIDO para API real"""
        print(f"🔍 Buscando até {limite} concursos de {loteria}...")
        
        # Mapear nomes para formato CORRETO da API
        loteria_map = {
            "Mega-Sena": "megasena",
            "Lotofácil": "lotofacil",
            "Quina": "quina",
            "Lotomania": "lotomania",
            "Dupla Sena": "duplasena",
            "Dia de Sorte": "diadesorte",
            "Timemania": "timemania"
        }
        
        api_name = loteria_map.get(loteria)
        if not api_name:
            print(f"❌ Loteria {loteria} não mapeada")
            return []
        
        # URL CORRETA: sem /latest, apenas nome da loteria
        url = f"{self.base_url}/{api_name}"
        print(f"🔗 URL: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # A API retorna TODOS os concursos em uma lista
                if isinstance(data, list):
                    # Pegar os mais recentes (primeiros da lista)
                    resultados_recentes = data[:limite]
                    resultados_processados = []
                    
                    for item in resultados_recentes:
                        resultado = self._processar_resultado(item, loteria)
                        if resultado:
                            resultados_processados.append(resultado)
                    
                    print(f"✅ {len(resultados_processados)} resultados processados")
                    return resultados_processados
                else:
                    print(f"❌ Formato inesperado: {type(data)}")
                    return []
            else:
                print(f"❌ HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return []
    
    def _processar_resultado(self, item, loteria: str):
        """Processar um item da API"""
        try:
            # Extrair dados
            concurso = item.get('concurso', 0)
            data = item.get('data', '')
            
            # Extrair dezenas
            dezenas = item.get('dezenas', [])
            if not dezenas:
                # Tentar campo alternativo
                dezenas = item.get('dezenasSorteadasOrdemSorteio', [])
            
            # Converter para inteiros se necessário
            dezenas_int = []
            for d in dezenas:
                try:
                    dezenas_int.append(int(d))
                except:
                    # Se for string com zeros à esquerda
                    if isinstance(d, str) and d.isdigit():
                        dezenas_int.append(int(d))
            
            return {
                'loteria': loteria,
                'concurso': concurso,
                'data': data,
                'dezenas': sorted(dezenas_int),
                'premiacao': item.get('premiacoes', {})
            }
            
        except Exception as e:
            print(f"⚠️  Erro ao processar item: {e}")
            return None
    
    def buscar_novos_resultados(self, loteria: str, ultimo_concurso_local: int):
        """Buscar apenas concursos novos"""
        resultados = self.buscar_ultimos_resultados(loteria, limite=50)
        if not resultados:
            return []
        
        # Filtrar concursos mais novos
        novos = [r for r in resultados if r['concurso'] > ultimo_concurso_local]
        novos.sort(key=lambda x: x['concurso'])
        
        print(f"📥 {len(novos)} novos concursos para {loteria}")
        return novos
    
    def obter_ultimo_concurso_api(self, loteria: str):
        """Obter número do último concurso"""
        resultados = self.buscar_ultimos_resultados(loteria, limite=1)
        return resultados[0]['concurso'] if resultados else None