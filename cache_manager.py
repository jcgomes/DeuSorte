# cache_manager.py - Gerenciador de cache SQLite para dados da loteria
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import hashlib

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
            max(concursos),
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
        
        last_update = datetime.fromisoformat(stats['data_ultima_atualizacao'])
        return (datetime.now() - last_update) > timedelta(hours=max_age_hours)