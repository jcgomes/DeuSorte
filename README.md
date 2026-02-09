# 📊 DeuSorte - Analisador de Loterias

## 📋 Sumário
- [Visão Geral](#visão-geral)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Manual do Usuário](#manual-do-usuário)
- [Configuração e Instalação](#configuração-e-instalação)
- [Estratégias de Análise](#estratégias-de-análise)
- [FAQ - Perguntas Frequentes](#faq---perguntas-frequentes)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Contato](#contato)

## 🎯 Visão Geral

**DeuSorte** é um aplicativo desktop desenvolvido em Python para análise estatística avançada dos resultados históricos das loterias da Caixa Econômica Federal. A ferramenta combina técnicas de ciência de dados, cache inteligente e interface gráfica intuitiva para fornecer insights valiosos sobre padrões e tendências das loterias brasileiras.

### 🎰 Loterias Suportadas
- **Mega-Sena** (60 números, sorteios: quartas e sábados)
- **Lotofácil** (25 números, sorteios: segundas, quartas e sextas)
- **Quina** (80 números, sorteios: segunda a sábado)
- **Lotomania** (100 números, sorteios: terças e sextas)
- **Dupla Sena** (50 números, sorteios: terças, quintas e sábados)
- **Dia de Sorte** (31 números, sorteios: terças e sextas)
- **Timemania** (80 números, sorteios: terças, quintas e sábados)

## ✨ Funcionalidades Principais

### 📊 Análise Estatística Avançada
- **Estatísticas básicas**: frequência de números, médias, desvios padrão
- **Identificação de padrões**: pares/ímpares, altos/baixos, sequências
- **Análise de atrasos**: números mais "frios" (não sorteados há tempo)
- **Distribuição estatística**: análise por faixas e dígitos finais
- **Correlações**: repetição entre concursos consecutivos

### 🕰️ Análise por Períodos Flexíveis
- **1 ano**: Análise básica (~100-150 concursos)
- **2 anos**: Análise de médio prazo (~200-300 concursos)
- **3 anos**: Análise abrangente (recomendada, ~300-450 concursos)
- **5 anos**: Análise histórica completa (~500-750 concursos)
- **Personalizado**: Qualquer período desejado

### 🔄 Sistema de Cache Inteligente
- **Armazenamento local SQLite** para consultas offline
- **Atualização incremental**: baixa apenas concursos novos
- **Validação de dados**: verificação automática de integridade
- **Limpeza seletiva**: cache por loteria ou completo

### 🎯 Geração de Sugestões
- **Estratégia Balanceada**: Combinação de múltiplos critérios estatísticos
- **Números Quentes**: Foco nos números mais frequentes
- **Números Frios**: Foco nos números mais atrasados
- **Mista**: Combinação de diferentes abordagens
- **Estatística Pura**: Baseado em distribuição estatística ideal

### 📈 Comparação entre Loterias
- **Tabelas comparativas**: estatísticas lado a lado
- **Visualizações gráficas**: barras comparativas de frequência
- **Exportação de dados**: resultados em formato JSON

## 🏗️ Arquitetura do Sistema

### 📁 Estrutura de Arquivos
```
DeuSorte/
├── analizador.py          # Classe principal de análise
├── api_client.py          # Cliente da API da Caixa
├── cache_manager.py       # Gerenciador de cache SQLite
├── main.py               # Interface gráfica (Flet)
├── lottery_cache.db      # Banco de dados de cache (gerado)
└── README.md            # Documentação
```

### 🔧 Componentes Técnicos

1. **LotteryPatternAnalyzer** (analizador.py)
   - Motor principal de análise estatística
   - Implementa 12 diferentes análises de padrões
   - Gerenciamento de cache integrado
   - Suporte a múltiplas estratégias

2. **LotteryAPIClient** (api_client.py)
   - Comunicação com API oficial da Caixa
   - Tratamento de erros e timeouts
   - Processamento de respostas em JSON

3. **LotteryCacheManager** (cache_manager.py)
   - Banco de dados SQLite local
   - Consultas otimizadas com índices
   - Estatísticas de uso do cache

4. **LotteryAnalyzerApp** (main.py)
   - Interface gráfica moderna com Flet
   - Navegação intuitiva por menu lateral
   - Feedback visual em tempo real
   - Suporte a múltiplas abas/páginas

### 💾 Banco de Dados de Cache
```sql
-- Tabela principal de concursos
CREATE TABLE concursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lottery_type TEXT NOT NULL,
    concurso INTEGER NOT NULL,
    data TEXT NOT NULL,
    numeros TEXT NOT NULL,  -- JSON array
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lottery_type, concurso)
);

-- Tabela de estatísticas de cache
CREATE TABLE cache_stats (
    lottery_type TEXT PRIMARY KEY,
    ultimo_concurso INTEGER,
    total_concursos INTEGER,
    data_ultima_atualizacao TIMESTAMP,
    data_primeiro_concurso TIMESTAMP
);
```

## 📖 Manual do Usuário

### 🚀 Primeiros Passos

#### Passo 1: Escolha o Tipo de Análise
No menu lateral, selecione uma das opções:
- **🏠 Início**: Visão geral do aplicativo
- **📊 Análise por Anos**: Análise personalizada por período
- **⚡ Análise Rápida**: Análise padrão de 3 anos
- **🔄 Comparar Loterias**: Análise comparativa

#### Passo 2: Selecione a Loteria
Escolha uma das 7 loterias disponíveis:
- **Mega-Sena**: 60 números, sorteios às quartas e sábados
- **Lotofácil**: 25 números, sorteios às segundas, quartas e sextas
- **Quina**: 80 números, sorteios de segunda a sábado
- **Lotomania**: 100 números (0-99), sorteios às terças e sextas
- **Dupla Sena**: 50 números, sorteios às terças, quintas e sábados
- **Dia de Sorte**: 31 números, sorteios às terças e sextas
- **Timemania**: 80 números, sorteios às terças, quintas e sábados

#### Passo 3: Configure o Período
Para análise personalizada:
- **1 ano**: Aproximadamente 100-150 concursos
- **2 anos**: Análise de médio prazo (200-300 concursos)
- **3 anos**: Análise abrangente (recomendada, 300-450 concursos)
- **5 anos**: Análise histórica completa (500-750 concursos)

#### Passo 4: Aguarde a Análise
O aplicativo irá:
1. 🔍 Buscar dados da API da Caixa
2. 📊 Processar estatísticas
3. 🎭 Identificar padrões
4. 📄 Gerar relatórios

**⏱️ Tempo estimado**: 1-3 minutos na primeira execução

#### Passo 5: Explore os Resultados
- **Números mais frequentes**: Com frequência e porcentagem
- **Números mais atrasados**: Tempo desde o último sorteio
- **Estatísticas de pares/ímpares**: Proporções médias
- **Padrões de soma**: Faixas ideais e distribuição
- **Sugestões de combinações**: Baseadas em diferentes estratégias

### 🎯 Como Usar as Sugestões

#### Estratégias Disponíveis:
1. **🎯 Balanceada** (Recomendada)
   - Combina múltiplos critérios estatísticos
   - Proporção equilibrada de pares/ímpares
   - Distribuição adequada de altos/baixos
   - Soma dentro da faixa ideal

2. **🔥 Números Quentes**
   - Foca nos números mais frequentes
   - Baseado em tendências recentes
   - Ideal para sequências de repetição

3. **❄️ Números Frios**
   - Foca nos números mais atrasados
   - Para quebrar sequências de ausência
   - Baseado na "lei dos atrasos"

4. **🔄 Mista**
   - Combinação de números quentes e frios
   - Adiciona aleatoriedade controlada
   - Diversificação estratégica

5. **📊 Estatística**
   - Baseado puramente em distribuição matemática
   - Otimização estatística ideal
   - Para usuários avançados

### 📊 Interpretando os Resultados

#### 🔥 Números Quentes (Frequentes)
- **O que são**: Números que aparecem com maior frequência
- **Interpretação**: Tendência de repetição
- **Uso estratégico**: Manter em combinações quando em sequência positiva

#### ❄️ Números Frios (Atrasados)
- **O que são**: Números que não saem há muitos concursos
- **Interpretação**: Probabilidade teórica de sair aumenta
- **Uso estratégico**: Incluir para diversificação

#### ⚖️ Balanceamento Ideal
- **Pares/Ímpares**: Proporção próxima de 50/50
- **Altos/Baixos**: Distribuição equilibrada
- **Soma total**: Dentro da faixa estatística ideal
- **Sequências**: Evitar muitas sequências consecutivas

### 📈 Análise Comparativa

#### Comparando Loterias:
1. **Frequência média**: Quantas vezes cada número aparece em média
2. **Distribuição**: Como os números se distribuem por faixas
3. **Volatilidade**: Desvio padrão das frequências
4. **Padrões**: Diferenças entre as características de cada loteria

#### Insights Comparativos:
- **Lotofácil**: Maior frequência média (mais números sorteados)
- **Mega-Sena**: Menor frequência média (apenas 6 números)
- **Lotomania**: Faixa mais ampla (0-99)
- **Quina**: Maior número de sorteios semanais

## ⚙️ Configuração e Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Conexão com internet (para primeira execução)
- 100MB de espaço em disco (para cache)

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/jcgomes/DeuSorte.git
cd DeuSorte

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute o aplicativo
python main.py
```

### requirements.txt
```txt
flet>=0.24.0
requests>=2.31.0
pandas>=2.1.0
numpy>=1.24.0
```

### Estrutura de Pastas Recomendada
```
DeuSorte/
├── src/                    # Código fonte
│   ├── analizador.py
│   ├── api_client.py
│   ├── cache_manager.py
│   └── main.py
├── data/                   # Dados e cache
│   └── lottery_cache.db
├── docs/                   # Documentação
├── assets/                 # Recursos visuais
├── tests/                  # Testes unitários
└── requirements.txt
```

## 🎮 Estratégias de Análise Detalhadas

### 1. Análise de Frequência
```python
# Algoritmo implementado
frequencias = Counter(todos_numeros)
mais_frequentes = frequencias.most_common(10)
menos_frequentes = frequencias.most_common()[-10:]
```

### 2. Análise de Atrasos
```python
# Para cada número no range da loteria
atraso = 0
for concurso in reversed(concursos):
    if numero in concurso['numeros']:
        break
    atraso += 1
```

### 3. Análise de Padrões
- **Pares vs Ímpares**: Proporção ideal baseada na quantidade de números
- **Altos vs Baixos**: Divisão pelo ponto médio da faixa
- **Somas**: Faixa estatística ideal (média ± desvio padrão)
- **Sequências**: Números consecutivos sorteados juntos

### 4. Geração de Combinações
```python
# Estratégia balanceada
1. Definir proporções ideais (pares/ímpares, altos/baixos)
2. Selecionar números seguindo distribuição estatística
3. Verificar soma dentro da faixa ideal
4. Minimizar sequências consecutivas
```

## ❓ FAQ - Perguntas Frequentes

### 🤔 Como funciona a atualização de dados?
- **Primeira execução**: Baixa todos os concursos do período selecionado
- **Execuções subsequentes**: Verifica e baixa apenas concursos novos
- **Cache**: Dados armazenados localmente em SQLite
- **Atualização forçada**: Exclua o arquivo `lottery_cache.db`

### 📊 Os dados são confiáveis?
- **Fonte**: API oficial da Caixa Econômica Federal
- **Validação**: Verificação de integridade dos dados
- **Backup**: Sistema de fallback com dados de exemplo
- **Atualização**: Verificação automática de novos concursos

### 🎯 Posso confiar nas sugestões geradas?
- **Base estatística**: Todas as sugestões têm fundamento matemático
- **Transparência**: Cada estratégia é claramente explicada
- **Contexto**: As sugestões são para estudo, não garantia
- **Responsabilidade**: Use com moderação e bom senso

### 💾 Quanto espaço ocupa o cache?
- **Por loteria**: ~1-2MB por ano de concursos
- **Total estimado**: ~10-20MB para todas as loterias (5 anos)
- **Limpeza**: Disponível no menu de configurações
- **Personalização**: Pode limitar período armazenado

### 📱 Funciona offline?
- **Análises**: Sim, após primeira execução (dados em cache)
- **Atualizações**: Requer internet para buscar novos concursos
- **Exportação**: Funciona completamente offline
- **Relatórios**: Geração local sem necessidade de internet

### ⚠️ Aviso Legal Importante
> **ATENÇÃO**: Este software é para estudo estatístico apenas. Loterias são jogos de azar regulamentados e não há padrões que garantam vitórias. O desenvolvedor não se responsabiliza por perdas financeiras. Jogue com responsabilidade e moderação, respeitando seus limites financeiros.

## 🤝 Contribuição

### Como Contribuir
1. **Fork** o repositório
2. Crie uma **branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

### Áreas para Melhoria
- [ ] Novos algoritmos de análise
- [ ] Visualizações gráficas avançadas
- [ ] Exportação para Excel/PDF
- [ ] Suporte a mais loterias internacionais
- [ ] Análise preditiva com machine learning

### Padrões de Código
- **PEP 8**: Seguir convenções do Python
- **Type hints**: Anotações de tipo obrigatórias
- **Docstrings**: Documentação em Google Style
- **Testes**: Adicionar testes unitários para novas funcionalidades

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

**Exceção**: Alguns componentes podem estar sob licenças diferentes. Verifique os arquivos individuais.

## 📞 Contato

### Desenvolvedor
- **Nome**: Juliano Gomes
- **GitHub**: [@jcgomes](https://github.com/jcgomes)
- **Repositório**: [https://github.com/jcgomes/DeuSorte](https://github.com/jcgomes/DeuSorte)

### Relatar Problemas
- **Issues**: [GitHub Issues](https://github.com/jcgomes/DeuSorte/issues)
- **Contribuições**: Pull Requests são bem-vindos!

---

## ⭐ Suporte ao Projeto

Se este projeto foi útil para você:
1. **Dê uma estrela** no GitHub ⭐
2. **Compartilhe** com amigos interessados
3. **Contribua** com melhorias
4. **Reporte bugs** para ajudar a melhorar

## 🔮 Roadmap Futuro

### Versão 2.1
- [ ] Análise de grupos de números
- [ ] Padrões temporais (dias/meses)
- [ ] Exportação avançada (CSV, Excel, PDF)

### Versão 3.0
- [ ] Dashboard web
- [ ] API REST para integração
- [ ] Aplicativo mobile
- [ ] Análise preditiva com IA

---

**Última atualização**: Fevereiro 2024  
**Versão do software**: 2.0  
**Python requerido**: 3.8+  
**Licença**: MIT License
