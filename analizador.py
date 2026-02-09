# analizador.py - Analisador de Loterias com cache
import requests
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json
from typing import List, Dict, Tuple, Set
import warnings
import time
import sqlite3
import os

warnings.filterwarnings('ignore')

class LotteryCacheManager:
    def __init__(self, db_path: str = "lottery_cache.db"):
        """Inicializa o gerenciador de cache"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela para armazenar concursos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS concursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lottery_type TEXT NOT NULL,
            concurso INTEGER NOT NULL,
            data TEXT NOT NULL,
            numeros TEXT NOT NULL,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lottery_type, concurso)
        )
        ''')
        
        # Tabela para estatísticas de cache
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_stats (
            lottery_type TEXT PRIMARY KEY,
            ultimo_concurso INTEGER,
            total_concursos INTEGER,
            data_ultima_atualizacao TIMESTAMP,
            data_primeiro_concurso TIMESTAMP
        )
        ''')
        
        # Índices para melhor performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lottery_concurso ON concursos(lottery_type, concurso)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lottery_type ON concursos(lottery_type)')
        
        conn.commit()
        conn.close()
    
    def get_cached_results(self, lottery_type: str, start_concurso: int, end_concurso: int) -> List[Dict]:
        """Busca concursos no cache"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT concurso, data, numeros 
        FROM concursos 
        WHERE lottery_type = ? AND concurso BETWEEN ? AND ?
        ORDER BY concurso
        ''', (lottery_type, start_concurso, end_concurso))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'concurso': row['concurso'],
                'data': row['data'],
                'numeros': json.loads(row['numeros']),
                'numeros_ordenados': sorted(json.loads(row['numeros']))
            })
        
        conn.close()
        return results
    
    def save_results(self, lottery_type: str, results: List[Dict]):
        """Salva resultados no cache"""
        if not results:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute('''
            INSERT OR REPLACE INTO concursos (lottery_type, concurso, data, numeros)
            VALUES (?, ?, ?, ?)
            ''', (
                lottery_type,
                result['concurso'],
                result['data'],
                json.dumps(result['numeros'])
            ))
        
        # Atualiza estatísticas
        concursos = [r['concurso'] for r in results]
        datas = [r['data'] for r in results if r['data']]
        
        cursor.execute('''
        INSERT OR REPLACE INTO cache_stats 
        (lottery_type, ultimo_concurso, total_concursos, data_ultima_atualizacao, data_primeiro_concurso)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            lottery_type,
            max(concursos) if concursos else 0,
            cursor.execute('SELECT COUNT(*) FROM concursos WHERE lottery_type = ?', (lottery_type,)).fetchone()[0],
            datetime.now().isoformat(),
            min(datas) if datas else datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_missing_concursos(self, lottery_type: str, start_concurso: int, end_concurso: int) -> List[int]:
        """Retorna lista de concursos faltantes no cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT concurso FROM concursos 
        WHERE lottery_type = ? AND concurso BETWEEN ? AND ?
        ''', (lottery_type, start_concurso, end_concurso))
        
        cached = set(row[0] for row in cursor.fetchall())
        all_concursos = set(range(start_concurso, end_concurso + 1))
        missing = sorted(list(all_concursos - cached))
        
        conn.close()
        return missing
    
    def get_cache_stats(self, lottery_type: str) -> Dict:
        """Retorna estatísticas do cache"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cache_stats WHERE lottery_type = ?', (lottery_type,))
        row = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) FROM concursos WHERE lottery_type = ?', (lottery_type,))
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(concurso), MAX(concurso) FROM concursos WHERE lottery_type = ?', (lottery_type,))
        min_max = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                'lottery_type': lottery_type,
                'ultimo_concurso': row['ultimo_concurso'],
                'total_concursos': row['total_concursos'],
                'data_ultima_atualizacao': row['data_ultima_atualizacao'],
                'data_primeiro_concurso': row['data_primeiro_concurso'],
                'min_concurso': min_max[0],
                'max_concurso': min_max[1]
            }
        else:
            return {
                'lottery_type': lottery_type,
                'total_concursos': 0,
                'status': 'vazio'
            }
    
    def clear_cache(self, lottery_type: str = None):
        """Limpa o cache (tudo ou de uma loteria específica)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if lottery_type:
            cursor.execute('DELETE FROM concursos WHERE lottery_type = ?', (lottery_type,))
            cursor.execute('DELETE FROM cache_stats WHERE lottery_type = ?', (lottery_type,))
        else:
            cursor.execute('DELETE FROM concursos')
            cursor.execute('DELETE FROM cache_stats')
        
        conn.commit()
        conn.close()
    
    def is_cache_stale(self, lottery_type: str, max_age_hours: int = 24) -> bool:
        """Verifica se o cache está desatualizado"""
        stats = self.get_cache_stats(lottery_type)
        if 'data_ultima_atualizacao' not in stats:
            return True
        
        try:
            last_update = datetime.fromisoformat(stats['data_ultima_atualizacao'])
            return (datetime.now() - last_update) > timedelta(hours=max_age_hours)
        except:
            return True

class LotteryPatternAnalyzer:
    def __init__(self, lottery_type: str = "megasena", last_n_games: int = None, years: int = None):
        """
        Analisador de padrões para loterias da Caixa com cache
        
        Args:
            lottery_type: Tipo de loteria (megasena, lotofacil, quina, etc.)
            last_n_games: Quantidade de concursos a analisar (sobrescreve years se ambos fornecidos)
            years: Quantidade de anos a analisar (calcula automaticamente os concursos)
        """
        self.lottery_type = lottery_type
        
        # Configurações detalhadas por loteria
        self.lottery_config = {
            "megasena": {
                "range": range(1, 61), 
                "draw_size": 6, 
                "weekly_draws": 2,
                "description": "Mega-Sena: 60 números, sorteios às quartas e sábados"
            },
            "lotofacil": {
                "range": range(1, 26), 
                "draw_size": 15, 
                "weekly_draws": 3,
                "description": "Lotofácil: 25 números, sorteios às segundas, quartas e sextas"
            },
            "quina": {
                "range": range(1, 81), 
                "draw_size": 5, 
                "weekly_draws": 6,
                "description": "Quina: 80 números, sorteios de segunda a sábado"
            },
            "lotomania": {
                "range": range(0, 100), 
                "draw_size": 20, 
                "weekly_draws": 2,
                "description": "Lotomania: 100 números (0-99), sorteios às terças e sextas"
            },
            "duplasena": {
                "range": range(1, 51), 
                "draw_size": 6, 
                "weekly_draws": 3,
                "description": "Dupla Sena: 50 números, sorteios às terças, quintas e sábados"
            },
            "diadesorte": {
                "range": range(1, 32), 
                "draw_size": 7, 
                "weekly_draws": 2,
                "description": "Dia de Sorte: 31 números, sorteios às terças e sextas"
            },
            "timemania": {
                "range": range(1, 81), 
                "draw_size": 7, 
                "weekly_draws": 3,
                "description": "Timemania: 80 números, sorteios às terças, quintas e sábados"
            }
        }
        
        # Calcula quantidade de concursos baseado em anos se fornecido
        if years is not None and last_n_games is None:
            last_n_games = self._calculate_games_from_years(years)
            self.years = years
            print(f"📅 Configurado para analisar aproximadamente {years} ano(s) "
                  f"({last_n_games} concursos) de {lottery_type}")
        elif last_n_games is None:
            last_n_games = 100  # Valor padrão
            self.years = None
        else:
            self.years = None
            
        self.last_n_games = last_n_games
        self.results = []
        self.numbers_range = self._get_numbers_range()
        self.draw_size = self._get_draw_size()
        
        # Inicializa gerenciador de cache
        self.cache_manager = LotteryCacheManager()
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Define uma função de callback para atualizar progresso"""
        self.progress_callback = callback
    
    def _calculate_games_from_years(self, years: int) -> int:
        """Calcula quantidade aproximada de concursos baseado em anos"""
        config = self.lottery_config.get(self.lottery_type)
        if not config:
            return 100  # Valor padrão se loteria não encontrada
            
        weekly_draws = config["weekly_draws"]
        
        # Cálculo: semanas por ano (52) × sorteios por semana × anos
        # Considera que a maioria dos sorteios ocorre, exceto em feriados
        games_per_year = weekly_draws * 52
        total_games = int(games_per_year * years)
        
        # Ajuste para concursos disponíveis na API
        # A API pode não ter todos os concursos históricos
        if total_games > 3000:  # Limite prático
            total_games = 3000
            print(f"⚠️  Limitando a {total_games} concursos (máximo prático para API)")
            
        return total_games
    
    def _get_numbers_range(self) -> range:
        """Define o range de números baseado no tipo de loteria"""
        config = self.lottery_config.get(self.lottery_type)
        if config:
            return config["range"]
        return range(1, 61)  # Default para Mega-Sena
    
    def _get_draw_size(self) -> int:
        """Quantidade de números sorteados por concurso"""
        config = self.lottery_config.get(self.lottery_type)
        if config:
            return config["draw_size"]
        return 6  # Default para Mega-Sena
    
    def get_lottery_info(self) -> Dict:
        """Retorna informações detalhadas sobre a loteria configurada"""
        config = self.lottery_config.get(self.lottery_type, {})
        return {
            "tipo": self.lottery_type,
            "faixa_numeros": f"{self.numbers_range[0]}-{self.numbers_range[-1]}",
            "quantidade_numeros": len(list(self.numbers_range)),
            "numeros_por_sorteio": self.draw_size,
            "sorteios_semana": config.get("weekly_draws", 0),
            "descricao": config.get("description", ""),
            "concursos_configurados": self.last_n_games,
            "anos_equivalentes": self.years
        }
    
    def fetch_results(self, num_games: int = None, use_cache: bool = True) -> List[Dict]:
        """Busca resultados da API da Caixa com cache"""
        if num_games is None:
            num_games = self.last_n_games
        
        base_url = "https://servicebus2.caixa.gov.br/portaldeloterias/api"
        all_results = []
        
        # Mostra informações sobre a busca
        if self.years:
            print(f"🔍 Buscando {num_games} concursos (≈{self.years} ano(s)) de {self.lottery_type}...")
        else:
            print(f"🔍 Buscando {num_games} concursos de {self.lottery_type}...")
        
        # Busca o último concurso primeiro
        try:
            response = requests.get(f"{base_url}/{self.lottery_type}", timeout=15)
            latest = response.json()
            last_number = latest['numero']
            
            # Verifica se há concursos suficientes disponíveis
            if last_number < num_games:
                print(f"⚠️  Apenas {last_number} concursos disponíveis na API")
                num_games = last_number
            
            # Busca concursos anteriores
            start = max(1, last_number - num_games + 1)
            
            print(f"📥 Concursos {start} a {last_number} ({num_games} total)")
            
            if use_cache:
                # Verifica cache primeiro
                cached_results = self.cache_manager.get_cached_results(self.lottery_type, start, last_number)
                cached_count = len(cached_results)
                
                if cached_count > 0:
                    print(f"💾 {cached_count} concursos encontrados no cache")
                    all_results.extend(cached_results)
                
                # Identifica concursos faltantes
                missing = self.cache_manager.get_missing_concursos(self.lottery_type, start, last_number)
                
                if missing:
                    print(f"⬇️  Baixando {len(missing)} concursos faltantes...")
                    missing_results = self._fetch_missing_concursos(missing, last_number)
                    
                    if missing_results:
                        # Salva no cache
                        self.cache_manager.save_results(self.lottery_type, missing_results)
                        all_results.extend(missing_results)
                    
                    print(f"✅ Total: {len(all_results)} concursos ({cached_count} do cache + {len(missing_results)} baixados)")
                else:
                    print(f"✅ Todos os {cached_count} concursos já estão em cache")
            else:
                # Busca tudo da API (sem cache)
                print("🔄 Ignorando cache, baixando todos os concursos...")
                all_results = self._fetch_all_concursos(start, last_number)
                
                # Salva no cache
                self.cache_manager.save_results(self.lottery_type, all_results)
                print(f"✅ {len(all_results)} concursos baixados e salvos no cache")
                    
        except Exception as e:
            print(f"Erro ao buscar dados: {e}")
            print("Usando dados de exemplo para demonstração...")
            # Fallback: usar dados de exemplo se API falhar
            all_results = self._generate_sample_data()
        
        # Ordena por concurso
        all_results.sort(key=lambda x: x['concurso'])
        self.results = all_results
        return all_results
    
    def _fetch_missing_concursos(self, missing: List[int], last_number: int) -> List[Dict]:
        """Busca apenas os concursos faltantes"""
        results = []
        base_url = "https://servicebus2.caixa.gov.br/portaldeloterias/api"
        
        for i, concurso in enumerate(missing, 1):
            try:
                if self.progress_callback:
                    self.progress_callback(f"Baixando concurso {concurso}/{last_number} ({i}/{len(missing)})")
                
                url = f"{base_url}/{self.lottery_type}/{concurso}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    numbers = [int(num) for num in data.get('dezenasSorteadasOrdemSorteio', [])]
                    
                    if numbers:
                        results.append({
                            'concurso': concurso,
                            'data': data.get('dataApuracao', ''),
                            'numeros': numbers,
                            'numeros_ordenados': sorted(numbers)
                        })
                
                # Progresso a cada 10 concursos
                if i % 10 == 0 or i == len(missing):
                    print(f"   {i}/{len(missing)} concursos baixados...")
                
                # Pequena pausa para não sobrecarregar o servidor
                time.sleep(0.05)
                
            except Exception as e:
                print(f"Erro no concurso {concurso}: {e}")
                continue
        
        return results
    
    def _fetch_all_concursos(self, start: int, end: int) -> List[Dict]:
        """Busca todos os concursos da API"""
        results = []
        base_url = "https://servicebus2.caixa.gov.br/portaldeloterias/api"
        
        total = end - start + 1
        print(f"📥 Concursos {start} a {end} ({total} total)")
        
        for i, concurso in enumerate(range(start, end + 1), 1):
            try:
                if self.progress_callback:
                    self.progress_callback(f"Baixando concurso {concurso}/{end} ({i}/{total})")
                
                url = f"{base_url}/{self.lottery_type}/{concurso}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    numbers = [int(num) for num in data.get('dezenasSorteadasOrdemSorteio', [])]
                    
                    if numbers:
                        results.append({
                            'concurso': concurso,
                            'data': data.get('dataApuracao', ''),
                            'numeros': numbers,
                            'numeros_ordenados': sorted(numbers)
                        })
                
                # Progresso a cada 10 concursos
                if i % 10 == 0 or i == total:
                    progress_msg = f"   {i}/{total} concursos baixados..."
                    print(progress_msg)
                    if self.progress_callback:
                        self.progress_callback(progress_msg)
                
                # Pequena pausa para não sobrecarregar o servidor
                time.sleep(0.05)
                
            except Exception as e:
                error_msg = f"Erro no concurso {concurso}: {e}"
                print(error_msg)
                if self.progress_callback:
                    self.progress_callback(error_msg)
                continue
        
        print(f"✅ {len(results)} concursos carregados com sucesso!")
        if self.progress_callback:
            self.progress_callback(f"✅ {len(results)} concursos carregados com sucesso!")
        
        return results
    
    def _generate_sample_data(self) -> List[Dict]:
        """Gera dados de exemplo para testes"""
        np.random.seed(42)  # Para reproducibilidade
        sample_data = []
        
        print("📊 Gerando dados de exemplo para demonstração...")
        
        for i in range(1, self.last_n_games + 1):
            numbers = sorted(np.random.choice(
                list(self.numbers_range), 
                self.draw_size, 
                replace=False
            ))
            sample_data.append({
                'concurso': i,
                'data': f"{(datetime.now() - timedelta(days=i)).strftime('%d/%m/%Y')}",
                'numeros': numbers,
                'numeros_ordenados': numbers
            })
        
        print(f"✅ {len(sample_data)} concursos de exemplo gerados")
        return sample_data
    
    def calculate_basic_statistics(self) -> Dict:
        """Calcula estatísticas básicas"""
        if not self.results:
            self.fetch_results()
        
        all_numbers = []
        for result in self.results:
            all_numbers.extend(result['numeros'])
        
        num_counter = Counter(all_numbers)
        total_draws = len(self.results)
        
        # Frequência de cada número
        frequencies = {num: count for num, count in num_counter.items()}
        
        # Números mais e menos sorteados
        most_common = num_counter.most_common(10)
        least_common = num_counter.most_common()[-10:]
        
        return {
            'total_concursos': total_draws,
            'frequencias': frequencies,
            'mais_frequentes': most_common,
            'menos_frequentes': least_common,
            'frequencia_media': np.mean(list(frequencies.values())),
            'frequencia_desvio': np.std(list(frequencies.values())),
            'periodo_analisado': f"{self.years} ano(s)" if self.years else f"{total_draws} concursos"
        }
    
    def analyze_patterns(self) -> Dict:
        """Analisa diversos padrões estatísticos"""
        
        patterns = {
            'pares_impares': self._analyze_parity(),
            'baixos_altos': self._analyze_low_high(),
            'somas': self._analyze_sums(),
            'sequencias': self._analyze_sequences(),
            'atrasos': self._analyze_delays(),
            'consecutivos': self._analyze_consecutive(),
            'distribuicao': self._analyze_distribution(),
            'repeticao_anterior': self._analyze_repetition(),
            'finais': self._analyze_last_digits()
        }
        
        return patterns
    
    def _analyze_parity(self) -> Dict:
        """Analisa proporção de pares vs ímpares"""
        stats = []
        for result in self.results:
            pares = sum(1 for n in result['numeros'] if n % 2 == 0)
            impares = len(result['numeros']) - pares
            stats.append({'pares': pares, 'impares': impares})
        
        avg_pares = np.mean([s['pares'] for s in stats])
        avg_impares = np.mean([s['impares'] for s in stats])
        
        return {
            'media_pares': avg_pares,
            'media_impares': avg_impares,
            'proporcao_ideal': f"{self.draw_size//2}:{self.draw_size - self.draw_size//2}",
            'historico': stats[-10:]  # Últimos 10 concursos
        }
    
    def _analyze_low_high(self) -> Dict:
        """Analisa números baixos vs altos"""
        if self.lottery_type == "lotomania":
            mid = 50
        else:
            mid = max(self.numbers_range) // 2
        
        stats = []
        for result in self.results:
            baixos = sum(1 for n in result['numeros'] if n <= mid)
            altos = len(result['numeros']) - baixos
            stats.append({'baixos': baixos, 'altos': altos})
        
        avg_baixos = np.mean([s['baixos'] for s in stats])
        avg_altos = np.mean([s['altos'] for s in stats])
        
        return {
            'ponto_medio': mid,
            'media_baixos': avg_baixos,
            'media_altos': avg_altos,
            'historico': stats[-10:]
        }
    
    def _analyze_sums(self) -> Dict:
        """Analisa as somas dos números sorteados"""
        sums = []
        for result in self.results:
            total = sum(result['numeros'])
            sums.append(total)
        
        min_sum = min(sums)
        max_sum = max(sums)
        avg_sum = np.mean(sums)
        std_sum = np.std(sums)
        
        # Distribuição das somas
        hist, bins = np.histogram(sums, bins=10)
        
        return {
            'minimo': min_sum,
            'maximo': max_sum,
            'media': avg_sum,
            'desvio_padrao': std_sum,
            'faixa_ideal': [avg_sum - std_sum, avg_sum + std_sum],
            'distribuicao': list(zip(bins[:-1], hist))
        }
    
    def _analyze_sequences(self) -> Dict:
        """Analisa sequências de números consecutivos"""
        seq_stats = []
        for result in self.results:
            sorted_nums = sorted(result['numeros'])
            sequences = []
            current_seq = [sorted_nums[0]]
            
            for i in range(1, len(sorted_nums)):
                if sorted_nums[i] == sorted_nums[i-1] + 1:
                    current_seq.append(sorted_nums[i])
                else:
                    if len(current_seq) > 1:
                        sequences.append(current_seq)
                    current_seq = [sorted_nums[i]]
            
            if len(current_seq) > 1:
                sequences.append(current_seq)
            
            seq_stats.append({
                'total_sequencias': len(sequences),
                'sequencias': sequences,
                'maior_sequencia': max([len(seq) for seq in sequences]) if sequences else 0
            })
        
        avg_sequences = np.mean([s['total_sequencias'] for s in seq_stats])
        
        return {
            'media_sequencias_por_sorteio': avg_sequences,
            'historico_sequencias': seq_stats[-5:],
            'maior_sequencia_registrada': max([s['maior_sequencia'] for s in seq_stats])
        }
    
    def _analyze_delays(self) -> Dict:
        """Analisa atraso de números não sorteados"""
        if not self.results:
            return {}
        
        last_draw = set(self.results[-1]['numeros'])
        delays = {}
        
        for num in self.numbers_range:
            delay = 0
            for result in reversed(self.results[:-1]):
                if num in result['numeros']:
                    break
                delay += 1
            delays[num] = delay
        
        # Números mais atrasados
        most_delayed = sorted(delays.items(), key=lambda x: x[1], reverse=True)[:15]
        
        return {
            'atrasos': delays,
            'mais_atrasados': most_delayed,
            'media_atraso': np.mean(list(delays.values())),
            'atraso_maximo': max(delays.values())
        }
    
    def _analyze_consecutive(self) -> Dict:
        """Analisa frequência de números consecutivos aparecendo juntos"""
        pair_counts = defaultdict(int)
        
        for result in self.results:
            sorted_nums = sorted(result['numeros'])
            for i in range(len(sorted_nums) - 1):
                for j in range(i + 1, len(sorted_nums)):
                    diff = abs(sorted_nums[j] - sorted_nums[i])
                    if diff <= 3:  # Considera "próximos" se diferença <= 3
                        pair = tuple(sorted([sorted_nums[i], sorted_nums[j]]))
                        pair_counts[pair] += 1
        
        # Pares mais frequentes
        most_common_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'pares_proximos_frequentes': most_common_pairs,
            'total_pares_unicos': len(pair_counts)
        }
    
    def _analyze_distribution(self) -> Dict:
        """Analisa distribuição dos números por faixas"""
        num_ranges = []
        max_num = max(self.numbers_range)
        
        # Divide em 5 faixas
        range_size = max_num // 5
        for i in range(5):
            start = i * range_size + 1
            end = (i + 1) * range_size
            if i == 4:  # Última faixa pega até o final
                end = max_num
            num_ranges.append((start, end))
        
        distribution = {f"{start}-{end}": 0 for start, end in num_ranges}
        
        for result in self.results:
            for num in result['numeros']:
                for start, end in num_ranges:
                    if start <= num <= end:
                        distribution[f"{start}-{end}"] += 1
                        break
        
        # Normaliza por quantidade de concursos
        total_draws = len(self.results)
        normalized = {k: v/total_draws for k, v in distribution.items()}
        
        return {
            'distribuicao_absoluta': distribution,
            'distribuicao_normalizada': normalized,
            'faixas': num_ranges
        }
    
    def _analyze_repetition(self) -> Dict:
        """Analisa repetição de números do concurso anterior"""
        if len(self.results) < 2:
            return {}
        
        repetitions = []
        for i in range(1, len(self.results)):
            prev_set = set(self.results[i-1]['numeros'])
            curr_set = set(self.results[i]['numeros'])
            repeated = len(prev_set.intersection(curr_set))
            repetitions.append(repeated)
        
        return {
            'media_repeticao': np.mean(repetitions),
            'max_repeticao': max(repetitions),
            'min_repeticao': min(repetitions),
            'distribuicao_repeticao': dict(Counter(repetitions)),
            'ultima_repeticao': repetitions[-1] if repetitions else 0
        }
    
    def _analyze_last_digits(self) -> Dict:
        """Analisa padrões nos últimos dígitos"""
        last_digits_dist = {str(i): 0 for i in range(10)}
        
        for result in self.results:
            for num in result['numeros']:
                last_digit = str(num)[-1]
                last_digits_dist[last_digit] += 1
        
        total_numbers = sum(last_digits_dist.values())
        normalized = {k: v/total_numbers for k, v in last_digits_dist.items()}
        
        return {
            'distribuicao_absoluta': last_digits_dist,
            'distribuicao_normalizada': normalized,
            'digitos_mais_comuns': sorted(last_digits_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    def generate_suggested_numbers(self, strategy: str = "balanced", quantity: int = 10) -> List[List[int]]:
        """
        Gera combinações sugeridas baseadas em diferentes estratégias
        
        Args:
            strategy: 'balanced', 'hot', 'cold', 'mixed', 'statistical'
            quantity: Quantidade de combinações a gerar
        """
        
        stats = self.calculate_basic_statistics()
        patterns = self.analyze_patterns()
        
        suggestions = []
        
        for _ in range(quantity):
            if strategy == "balanced":
                # Estratégia balanceada baseada em estatísticas
                suggestion = self._generate_balanced_combination(stats, patterns)
            elif strategy == "hot":
                # Apenas números quentes (frequentes recentemente)
                suggestion = self._generate_hot_combination(stats)
            elif strategy == "cold":
                # Apenas números frios/atrasados
                suggestion = self._generate_cold_combination(patterns['atrasos'])
            elif strategy == "mixed":
                # Mistura de estratégias
                suggestion = self._generate_mixed_combination(stats, patterns)
            elif strategy == "statistical":
                # Baseado puramente em distribuição estatística
                suggestion = self._generate_statistical_combination(stats, patterns)
            else:
                suggestion = self._generate_balanced_combination(stats, patterns)
            
            suggestions.append(sorted(suggestion))
        
        return suggestions
    
    def _generate_balanced_combination(self, stats: Dict, patterns: Dict) -> List[int]:
        """Gera combinação balanceada usando múltiplos critérios"""
        np.random.seed()  # Nova seed aleatória
        
        combination = set()
        
        # 1. Pares vs Ímpares (proporção balanceada)
        target_parity = patterns['pares_impares']['media_pares']
        pares_needed = int(round(target_parity))
        
        # 2. Baixos vs Altos
        low_high = patterns['baixos_altos']
        baixos_needed = int(round(low_high['media_baixos']))
        
        # Listas de números disponíveis
        all_numbers = list(self.numbers_range)
        np.random.shuffle(all_numbers)
        
        # Seleciona números seguindo critérios
        pares = [n for n in all_numbers if n % 2 == 0]
        impares = [n for n in all_numbers if n % 2 == 1]
        baixos = [n for n in all_numbers if n <= low_high['ponto_medio']]
        altos = [n for n in all_numbers if n > low_high['ponto_medio']]
        
        # Adiciona números seguindo proporções
        while len(combination) < self.draw_size:
            # Decide qual critério priorizar
            if len([n for n in combination if n % 2 == 0]) < pares_needed:
                candidates = [n for n in pares if n not in combination]
            else:
                candidates = [n for n in impares if n not in combination]
            
            if not candidates:
                candidates = [n for n in all_numbers if n not in combination]
            
            # Prefere números não muito atrasados
            delays = patterns['atrasos']['atrasos']
            candidates.sort(key=lambda x: delays.get(x, 0))
            
            # Escolhe aleatoriamente entre os primeiros 20%
            idx = min(len(candidates) - 1, int(len(candidates) * 0.2))
            if idx > 0:
                candidate = candidates[np.random.randint(0, idx)]
            else:
                candidate = candidates[0] if candidates else np.random.choice(all_numbers)
            
            combination.add(candidate)
        
        return list(combination)
    
    def _generate_hot_combination(self, stats: Dict) -> List[int]:
        """Gera combinação com números frequentes"""
        hot_numbers = [num for num, _ in stats['mais_frequentes'][:20]]
        np.random.shuffle(hot_numbers)
        return sorted(hot_numbers[:self.draw_size])
    
    def _generate_cold_combination(self, delays_info: Dict) -> List[int]:
        """Gera combinação com números atrasados"""
        cold_numbers = [num for num, _ in delays_info['mais_atrasados'][:20]]
        np.random.shuffle(cold_numbers)
        return sorted(cold_numbers[:self.draw_size])
    
    def _generate_mixed_combination(self, stats: Dict, patterns: Dict) -> List[int]:
        """Combinação mista de diferentes estratégias"""
        np.random.seed()
        
        # 30% números quentes, 30% frios, 40% aleatórios
        hot_count = int(self.draw_size * 0.3)
        cold_count = int(self.draw_size * 0.3)
        random_count = self.draw_size - hot_count - cold_count
        
        hot_numbers = [num for num, _ in stats['mais_frequentes'][:30]]
        cold_numbers = [num for num, _ in patterns['atrasos']['mais_atrasados'][:30]]
        all_numbers = list(self.numbers_range)
        
        combination = set()
        
        # Adiciona números quentes
        np.random.shuffle(hot_numbers)
        for num in hot_numbers[:hot_count]:
            combination.add(num)
        
        # Adiciona números frios
        np.random.shuffle(cold_numbers)
        for num in cold_numbers[:cold_count]:
            combination.add(num)
        
        # Completa com aleatórios
        while len(combination) < self.draw_size:
            candidate = np.random.choice(all_numbers)
            combination.add(candidate)
        
        return sorted(list(combination))
    
    def _generate_statistical_combination(self, stats: Dict, patterns: Dict) -> List[int]:
        """Combinação baseada em distribuição estatística ideal"""
        np.random.seed()
        
        # Calcula distribuição ideal baseada em médias históricas
        parity_ratio = patterns['pares_impares']
        low_high_ratio = patterns['baixos_altos']
        sum_range = patterns['somas']['faixa_ideal']
        
        all_numbers = list(self.numbers_range)
        max_attempts = 1000
        
        for attempt in range(max_attempts):
            combination = sorted(np.random.choice(all_numbers, self.draw_size, replace=False))
            
            # Verifica critérios estatísticos
            pares = sum(1 for n in combination if n % 2 == 0)
            impares = self.draw_size - pares
            
            baixos = sum(1 for n in combination if n <= low_high_ratio['ponto_medio'])
            altos = self.draw_size - baixos
            
            total_sum = sum(combination)
            
            # Verifica se atende aos critérios
            parity_ok = abs(pares - parity_ratio['media_pares']) <= 1
            low_high_ok = abs(baixos - low_high_ratio['media_baixos']) <= 1
            sum_ok = sum_range[0] <= total_sum <= sum_range[1]
            
            if parity_ok and low_high_ok and sum_ok:
                return combination
        
        # Se não encontrou combinação ideal, retorna uma aleatória
        return sorted(np.random.choice(all_numbers, self.draw_size, replace=False))
    
    def generate_report(self) -> str:
        """Gera um relatório completo da análise"""
        stats = self.calculate_basic_statistics()
        patterns = self.analyze_patterns()
        
        report = []
        report.append("=" * 70)
        report.append(f"📊 ANÁLISE ESTATÍSTICA - {self.lottery_type.upper()}")
        report.append("=" * 70)
        
        # Informações sobre o período analisado
        if self.years:
            periodo_info = f"{self.years} ano(s) ({len(self.results)} concursos)"
        else:
            periodo_info = f"{len(self.results)} concursos"
            
        report.append(f"📅 Período analisado: {periodo_info}")
        report.append(f"🎯 Último concurso: #{self.results[-1]['concurso'] if self.results else 'N/A'}")
        report.append("")
        
        # Estatísticas básicas
        report.append("📈 ESTATÍSTICAS BÁSICAS:")
        report.append(f"• Média de frequência por número: {stats['frequencia_media']:.2f}")
        report.append(f"• Desvio padrão da frequência: {stats['frequencia_desvio']:.2f}")
        report.append(f"• Teórico esperado: {self.draw_size*len(self.results)/len(list(self.numbers_range)):.1f}")
        report.append("")
        
        # Números mais e menos frequentes
        report.append("🔥 NÚMEROS MAIS FREQUENTES:")
        for num, freq in stats['mais_frequentes']:
            porcentagem = freq/len(self.results)*100
            report.append(f"  Número {num:2d}: {freq:3d} vezes ({porcentagem:.1f}%)")
        
        report.append("")
        report.append("❄️  NÚMEROS MENOS FREQUENTES:")
        for num, freq in stats['menos_frequentes']:
            porcentagem = freq/len(self.results)*100
            report.append(f"  Número {num:2d}: {freq:3d} vezes ({porcentagem:.1f}%)")
        
        report.append("")
        report.append("⏰ NÚMEROS MAIS ATRASADOS:")
        for num, delay in patterns['atrasos']['mais_atrasados'][:10]:
            report.append(f"  Número {num:2d}: {delay} concursos sem sair")
        
        # Padrões
        report.append("")
        report.append("🎭 PADRÕES IDENTIFICADOS:")
        report.append(f"• Proporção média Pares/Ímpares: {patterns['pares_impares']['media_pares']:.1f}/{patterns['pares_impares']['media_impares']:.1f}")
        report.append(f"• Proporção média Baixos/Altos: {patterns['baixos_altos']['media_baixos']:.1f}/{patterns['baixos_altos']['media_altos']:.1f}")
        report.append(f"• Média da soma: {patterns['somas']['media']:.1f} ± {patterns['somas']['desvio_padrao']:.1f}")
        report.append(f"• Repetição média do anterior: {patterns['repeticao_anterior']['media_repeticao']:.1f} números")
        
        # Sugestões
        report.append("")
        report.append("🎯 SUGESTÕES DE COMBINAÇÕES (apenas para estudo):")
        
        strategies = ['balanced', 'hot', 'cold', 'mixed']
        for strategy in strategies:
            suggestions = self.generate_suggested_numbers(strategy=strategy, quantity=2)
            report.append(f"\nEstratégia '{strategy}':")
            for i, comb in enumerate(suggestions, 1):
                report.append(f"  Combinação {i}: {comb}")
        
        report.append("")
        report.append("=" * 70)
        report.append("⚠️  AVISO LEGAL: Este é um estudo estatístico. Loterias são")
        report.append("   jogos de azar e não há padrões que garantam vitórias.")
        report.append("   Jogue com responsabilidade.")
        report.append("=" * 70)
        
        return "\n".join(report)


# ============================================================================
# FUNÇÕES AUXILIARES PARA USO EXTERNO
# ============================================================================

def quick_analysis(lottery_type: str = "megasena", years: int = 1):
    """Análise rápida para um tipo de loteria por anos"""
    
    analyzer = LotteryPatternAnalyzer(lottery_type, years=years)
    analyzer.fetch_results()
    
    info = analyzer.get_lottery_info()
    
    print(f"\n🔍 Análise Rápida - {lottery_type.upper()} ({years} ano(s))")
    print("-" * 50)
    print(f"Período: {years} ano(s) ≈ {info['concursos_configurados']} concursos")
    print(f"Faixa de números: {info['faixa_numeros']}")
    print(f"Números por sorteio: {info['numeros_por_sorteio']}")
    print(f"Sorteios por semana: {info['sorteios_semana']}")
    print("-" * 50)
    
    stats = analyzer.calculate_basic_statistics()
    
    print(f"\n📊 Concursos analisados: {stats['total_concursos']}")
    
    print(f"\n🔥 TOP 5 NÚMEROS QUENTES (frequentes):")
    for num, freq in stats['mais_frequentes'][:5]:
        print(f"  {num:2d} → {freq:4d} vezes ({freq/stats['total_concursos']*100:.1f}% dos sorteios)")
    
    print(f"\n❄️  TOP 5 NÚMEROS FRIOS (atrasados):")
    patterns = analyzer.analyze_patterns()
    for num, delay in patterns['atrasos']['mais_atrasados'][:5]:
        print(f"  {num:2d} → {delay:4d} concursos sem sair")
    
    print(f"\n🎲 SUGESTÃO BALANCEADA:")
    suggestion = analyzer.generate_suggested_numbers(strategy="balanced", quantity=1)[0]
    print(f"  {suggestion}")
    
    # Verificação da sugestão
    pares = sum(1 for n in suggestion if n % 2 == 0)
    soma_total = sum(suggestion)
    print(f"    Pares/Ímpares: {pares}/{len(suggestion)-pares}")
    print(f"    Soma: {soma_total}")

def main_example():
    """Exemplo de uso do analisador com anos"""
    
    print("🚀 Inicializando Analisador de Loterias - Versão por Anos")
    print("=" * 60)
    
    # 1. Criar analisador para Mega-Sena (3 anos)
    analyzer = LotteryPatternAnalyzer(
        lottery_type="megasena",  # ou "lotofacil", "quina", etc.
        years=3                   # Analisa aproximadamente 3 anos de concursos
    )
    
    # 2. Buscar dados
    print("📥 Buscando dados históricos...")
    results = analyzer.fetch_results()
    print(f"✅ {len(results)} concursos carregados")
    
    # 3. Gerar relatório completo
    print("\n📊 Gerando relatório estatístico...")
    report = analyzer.generate_report()
    print(report)
    
    # 4. Gerar sugestões
    print("\n🎯 Gerando combinações sugeridas...")
    
    strategies = ['balanced', 'hot', 'cold', 'mixed']
    for strategy in strategies:
        suggestions = analyzer.generate_suggested_numbers(
            strategy=strategy, 
            quantity=3
        )
        print(f"\nEstratégia: {strategy.upper()}")
        for i, comb in enumerate(suggestions, 1):
            # Analisa a combinação gerada
            pares = sum(1 for n in comb if n % 2 == 0)
            soma_total = sum(comb)
            print(f"  Combinação {i}: {comb}")
            print(f"    Pares/Ímpares: {pares}/{len(comb)-pares}")
            print(f"    Soma: {soma_total}")
    
    print("\n" + "=" * 60)
    print("⚠️  LEMBRETE IMPORTANTE:")
    print("Este algoritmo é para estudo estatístico apenas.")
    print("Não garante ganhos. Loterias são jogos de azar.")
    print("Jogue com responsabilidade e moderação.")
    print("=" * 60)


def show_lottery_types():
    """Mostra todos os tipos de loteria suportados"""
    print("\n🎰 LOTERIAS SUPORTADOS:")
    print("=" * 50)
    
    loterias = [
        ("megasena", "Mega-Sena", "60 números, sorteios às quartas e sábados"),
        ("lotofacil", "Lotofácil", "25 números, sorteios às segundas, quartas e sextas"),
        ("quina", "Quina", "80 números, sorteios de segunda a sábado"),
        ("lotomania", "Lotomania", "100 números (0-99), sorteios às terças e sextas"),
        ("duplasena", "Dupla Sena", "50 números, sorteios às terças, quintas e sábados"),
        ("diadesorte", "Dia de Sorte", "31 números, sorteios às terças e sextas"),
        ("timemania", "Timemania", "80 números, sorteios às terças, quintas e sábados")
    ]
    
    for codigo, nome, descricao in loterias:
        print(f"\n📋 {nome.upper()} ({codigo})")
        print(f"   {descricao}")
        
        # Mostra exemplos de anos
        analyzer = LotteryPatternAnalyzer(codigo, years=1)
        concursos_1_ano = analyzer.last_n_games
        print(f"   1 ano ≈ {concursos_1_ano} concursos")
        print(f"   3 anos ≈ {concursos_1_ano * 3} concursos")
        print(f"   5 anos ≈ {concursos_1_ano * 5} concursos")
    
    print("\n" + "=" * 50)
    print("💡 Use: analyzer = LotteryPatternAnalyzer('loteria', years=X)")

def set_progress_callback(self, callback):
    """Define uma função de callback para atualizar progresso"""
    self.progress_callback = callback