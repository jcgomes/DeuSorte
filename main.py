import flet as ft
from analizador import LotteryPatternAnalyzer
import asyncio
import time
from datetime import datetime
import threading

class LotteryAnalyzerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "DeuSorte - Analisador de Loterias"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 800
        self.page.window_min_height = 600
        
        self.analyzer = None
        self.current_lottery = None
        self.current_years = None
        self.is_loading = False
        self.loading_message = ""
        self.progress_details = ""
        
        # Controles principais
        self.progress_bar = ft.ProgressBar(width=400, visible=False)
        self.status_text = ft.Text("", color=ft.colors.BLUE)
        self.results_display = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Cabeçalho
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CASINO, size=40, color=ft.colors.BLUE),
                ft.Text("DeuSorte - Analisador de Loterias", size=28, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            padding=ft.padding.all(20),
            bgcolor=ft.colors.BLUE_50,
            border_radius=ft.border_radius.all(10),
        )
        
        # Menu lateral
        menu_items = [
            (ft.icons.HOME, "Início", self.show_home),
            (ft.icons.ANALYTICS, "Análise por Anos", self.show_year_analysis),
            (ft.icons.FLASH_ON, "Análise Rápida", self.show_quick_analysis),  # Corrigido
            (ft.icons.COMPARE_ARROWS, "Comparar Loterias", self.show_comparison),  # Corrigido
            (ft.icons.LIBRARY_BOOKS, "Loterias Suportadas", self.show_supported_lotteries),
            (ft.icons.AUTO_AWESOME, "Gerar Sugestões", self.show_suggestions),  # Corrigido
            (ft.icons.ASSESSMENT, "Relatório Completo", self.show_full_report),  # Corrigido
            (ft.icons.MENU_BOOK, "Manual do Usuário", self.show_user_manual),
            (ft.icons.INFO, "Sobre", self.show_about),
        ]
        
        menu_column = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Icon(icon[0], size=20),
                    ft.Text(icon[1], size=14),
                ], spacing=10),
                padding=ft.padding.symmetric(vertical=10, horizontal=15),
                on_click=icon[2],
                border_radius=ft.border_radius.all(5),
            ) for icon in menu_items
        ], spacing=5)
        
        menu_panel = ft.Container(
            content=menu_column,
            width=250,
            padding=ft.padding.all(15),
            bgcolor=ft.colors.GREY_100,
            border_radius=ft.border_radius.all(10),
        )
        
        # Área principal
        main_content = ft.Container(
            content=ft.Column([
                ft.Row([self.progress_bar, self.status_text]),
                ft.Divider(height=20),
                self.results_display,
            ]),
            expand=True,
            padding=ft.padding.all(20),
        )
        
        # Layout principal
        self.page.add(
            header,
            ft.Row([
                menu_panel,
                ft.VerticalDivider(width=1),
                main_content,
            ], expand=True),
        )
        
        # Mostrar página inicial
        self.show_home(None)

    def get_lottery_display_name(self, lottery_code):
        """Retorna nome amigável da loteria"""
        if not lottery_code:
            return "Loteria"
        
        names = {
            "megasena": "Mega-Sena",
            "lotofacil": "Lotofácil",
            "quina": "Quina",
            "lotomania": "Lotomania",
            "duplasena": "Dupla Sena",
            "diadesorte": "Dia de Sorte",
            "timemania": "Timemania"
        }
        return names.get(lottery_code.lower(), lottery_code.upper())

    async def copy_to_clipboard(self, text):
        """Copia texto para área de transferência"""
        try:
            # Método principal do Flet
            await self.page.set_clipboard_async(text)
            self.show_snackbar("✅ Texto copiado para área de transferência!")
            
        except Exception as e:
            print(f"Erro ao copiar para clipboard: {e}")
            
            # Fallback: Mostra diálogo para copiar manualmente
            self.show_dialog(
                "📋 Copiar para Área de Transferência",
                "Não foi possível copiar automaticamente. Por favor, selecione e copie o texto abaixo:",
                text,
                show_copy_button=False
            )
    
    def show_dialog(self, title, message, content=None, show_copy_button=False):
        """Mostra diálogo com conteúdo"""
        if not hasattr(self, 'page') or not self.page:
            return
            
        # Cria controles do diálogo
        controls = []
        
        if show_copy_button and content:
            controls.append(
                ft.TextButton(
                    "📋 Copiar", 
                    on_click=lambda e: self.page.run_task(self.copy_to_clipboard, content)
                )
            )
        
        controls.append(ft.TextButton("Fechar", on_click=lambda e: self.close_dialog()))
        
        # Conteúdo do diálogo
        dialog_content = ft.Column([
            ft.Text(message, size=14),
        ])
        
        if content:
            dialog_content.controls.extend([
                ft.Divider(height=20),
                ft.Container(
                    content=ft.Text(content, size=12, font_family="monospace", selectable=True),
                    height=200,
                    width=500,
                    padding=ft.padding.all(10),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=ft.border_radius.all(5),
                )
            ])
        
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=dialog_content,
            actions=controls,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_dialog(self):
        """Fecha diálogo atual"""
        if hasattr(self, 'page') and self.page and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def show_snackbar(self, message):
        """Mostra snackbar com mensagem"""
        if not hasattr(self, 'page') or not self.page:
            return
            
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            action="OK",
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()
     
    def cancel_current_operation(self):
        """Cancela a operação atual em andamento"""
        self.is_loading = False
        self.current_operation = "cancelled"
        self.page.update()
    
    def show_loading_with_details(self, message="Processando...", details=""):
        """Mostra indicador de carregamento com detalhes"""
        self.clear_results()
        self.is_loading = True
        self.loading_message = message
        self.progress_details = details
        
        loading_content = ft.Column([
            ft.ProgressRing(),
            ft.Text(message, size=16),
            ft.Container(
                content=ft.Column([
                    ft.Text("Detalhes do Progresso:", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(details, size=12, color=ft.colors.BLUE_GREY),
                ]),
                padding=ft.padding.all(10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(5),
                visible=bool(details)
            ),
            ft.Divider(height=20),
            ft.ElevatedButton(
                text="⏹️ Cancelar",
                on_click=self.cancel_loading,
                width=150,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.add_result(loading_content)
        self.page.update()
    
    def cancel_loading(self, e):
        """Cancela o carregamento"""
        self.cancel_current_operation()
        self.show_home(None)
    
    def update_loading_details(self, details):
        """Atualiza os detalhes do carregamento"""
        self.progress_details = details
        # Atualiza a UI se estiver mostrando loading
        if self.is_loading and self.results_display.controls:
            for control in self.results_display.controls:
                if isinstance(control, ft.Column):
                    for sub_control in control.controls:
                        if isinstance(sub_control, ft.Container) and sub_control.visible:
                            # Atualiza o texto de detalhes
                            sub_control.content.controls[1].value = details
                            self.page.update()
                            break
    
    def clear_results(self):
        """Limpa a área de resultados"""
        self.results_display.controls.clear()
        self.is_loading = False
        self.page.update()
    
    def add_result(self, control):
        """Adiciona um controle à área de resultados"""
        self.results_display.controls.append(control)
        self.page.update()
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        self.clear_results()
        self.add_result(
            ft.Column([
                ft.Icon(ft.icons.ERROR, size=50, color=ft.colors.RED),
                ft.Text("Erro", size=24, color=ft.colors.RED),
                ft.Divider(height=20),
                ft.Text(message, size=16),
                ft.Divider(height=20),
                ft.ElevatedButton(
                    text="Voltar ao Início",
                    on_click=self.show_home,
                    icon=ft.icons.HOME,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    
    def show_home(self, e):
        """Mostra página inicial"""
        self.clear_results()
        self.add_result(
            ft.Column([
                ft.Text("Bem-vindo ao DeuSorte - Analisador de Loterias", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.ANALYTICS, color=ft.colors.BLUE),
                                title=ft.Text("Análise Estatística Completa"),
                                subtitle=ft.Text("Analise resultados históricos de qualquer loteria"),
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.SCHEDULE, color=ft.colors.GREEN),
                                title=ft.Text("Análise por Períodos"),
                                subtitle=ft.Text("Configure análise por anos (1, 2, 3, 5 anos)"),
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.COMPARE, color=ft.colors.ORANGE),
                                title=ft.Text("Comparação entre Loterias"),
                                subtitle=ft.Text("Compare estatísticas entre diferentes loterias"),
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.PURPLE),
                                title=ft.Text("Sugestões Inteligentes"),
                                subtitle=ft.Text("Gere combinações baseadas em diferentes estratégias"),
                            ),
                        ]),
                        padding=ft.padding.all(20),
                    ),
                    elevation=5,
                ),
                ft.Divider(height=30),
                ft.Container(
                    content=ft.Column([
                        ft.Text("⚠️ AVISO IMPORTANTE", size=18, color=ft.colors.RED, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Este software é para estudo estatístico apenas. "
                            "Loterias são jogos de azar e não há padrões que garantam vitórias. "
                            "Jogue com responsabilidade e moderação.",
                            size=14,
                            color=ft.colors.BLUE_GREY,
                        ),
                    ]),
                    padding=ft.padding.all(20),
                    bgcolor=ft.colors.RED_50,
                    border_radius=ft.border_radius.all(10),
                ),
                ft.Divider(height=30),
                ft.Text("Selecione uma opção no menu à esquerda para começar", size=16, italic=True),
            ], spacing=15)
        )
    
    def show_year_analysis(self, e):
        """Mostra interface para análise por anos"""
        self.clear_results()
        
        # Variáveis para armazenar seleções
        self.selected_lottery = None
        self.selected_years = None
        
        # Opções de loterias
        loterias = [
            ("megasena", "Mega-Sena", "2x/semana"),
            ("lotofacil", "Lotofácil", "3x/semana"),
            ("quina", "Quina", "6x/semana"),
            ("lotomania", "Lotomania", "2x/semana"),
            ("duplasena", "Dupla Sena", "3x/semana"),
            ("diadesorte", "Dia de Sorte", "2x/semana"),
            ("timemania", "Timemania", "3x/semana"),
        ]
        
        # Criar Radio buttons
        radio_buttons = []
        for lot in loterias:
            radio_buttons.append(
                ft.Radio(
                    value=lot[0],
                    label=f"{lot[1]} ({lot[2]})"  # Texto direto
                )
            )
        
        # Grupo de rádio
        self.lottery_radio_group = ft.RadioGroup(
            content=ft.Column(radio_buttons, spacing=10),
            on_change=self.on_lottery_changed
        )
        
        # Botões de anos
        self.year_buttons = {}
        year_buttons_row = ft.Row(spacing=10)
        for anos in [1, 2, 3, 5]:
            btn = ft.ElevatedButton(
                text=f"{anos} ano{'s' if anos > 1 else ''}",
                data=anos,
                on_click=self.on_year_clicked,
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.BLUE_100 if anos == 1 else None,
                    color=ft.colors.BLUE if anos == 1 else None,
                )
            )
            self.year_buttons[anos] = btn
            year_buttons_row.controls.append(btn)
            if anos == 1:  # Selecionar 1 ano por padrão
                self.selected_years = 1
        
        # Campo personalizado
        self.custom_year_field = ft.TextField(
            label="Personalizado",
            width=150,
            suffix_text="anos",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self.on_custom_year_changed,
        )
        
        year_buttons_row.controls.append(self.custom_year_field)
        
        # Botão de iniciar análise
        self.start_analysis_btn = ft.ElevatedButton(
            text="Iniciar Análise",
            icon=ft.icons.PLAY_ARROW,
            on_click=self.run_year_analysis,
            disabled=True,  # Inicialmente desabilitado
        )
        
        self.add_result(
            ft.Column([
                ft.Text("📅 Análise por Anos", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                ft.Text("Selecione a loteria:", size=16),
                self.lottery_radio_group,
                ft.Divider(height=30),
                ft.Text("Selecione o período:", size=16),
                year_buttons_row,
                ft.Divider(height=30),
                self.start_analysis_btn,
                ft.Divider(height=20),
            ])
        )
        
        # Verificar se pode habilitar o botão
        self.update_start_button()
    
    def on_lottery_changed(self, e):
        """Quando a loteria é selecionada"""
        self.selected_lottery = e.control.value
        self.update_start_button()
    
    def on_year_clicked(self, e):
        """Quando um botão de ano é clicado"""
        self.selected_years = e.control.data
        
        # Resetar estilo de todos os botões
        for anos, btn in self.year_buttons.items():
            btn.style = None
        
        # Destacar botão selecionado
        e.control.style = ft.ButtonStyle(
            bgcolor=ft.colors.BLUE_100,
            color=ft.colors.BLUE,
        )
        
        # Limpar campo personalizado
        self.custom_year_field.value = ""
        
        self.update_start_button()
        self.page.update()
    
    def on_custom_year_changed(self, e):
        """Quando o campo personalizado é alterado"""
        try:
            if e.control.value and e.control.value.strip():
                self.selected_years = int(e.control.value)
                
                # Resetar estilo dos botões de anos
                for anos, btn in self.year_buttons.items():
                    btn.style = None
            else:
                self.selected_years = None
        except ValueError:
            self.selected_years = None
        
        self.update_start_button()
    
    def update_start_button(self):
        """Atualiza estado do botão de iniciar análise"""
        if self.selected_lottery and self.selected_years:
            self.start_analysis_btn.disabled = False
            self.start_analysis_btn.text = f" Analisar {self.selected_lottery.upper()} ({self.selected_years} ano{'s' if self.selected_years > 1 else ''})"
        else:
            self.start_analysis_btn.disabled = True
            self.start_analysis_btn.text = " Iniciar Análise"
        
        self.page.update()
    
    def run_year_analysis(self, e):
        """Executa análise por anos"""
        if not self.selected_lottery or not self.selected_years:
            return
        
        self.show_loading_with_details(
            f"Configurando análise de {self.selected_years} ano(s) de {self.selected_lottery}...",
            "Inicializando analisador..."
        )
        
        try:
            # Criar analisador
            self.analyzer = LotteryPatternAnalyzer(self.selected_lottery, years=self.selected_years)
            self.current_lottery = self.selected_lottery
            self.current_years = self.selected_years
            
            # Mostrar informações
            info = self.analyzer.get_lottery_info()
            
            self.clear_results()
            self.add_result(
                ft.Column([
                    ft.Text(f"📊 {info['tipo'].upper()} - {self.selected_years} ano(s)", 
                           size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Característica")),
                            ft.DataColumn(ft.Text("Valor")),
                        ],
                        rows=[
                            ft.DataRow(cells=[
                                ft.DataCell(ft.Text("Faixa de números")),
                                ft.DataCell(ft.Text(info['faixa_numeros'])),
                            ]),
                            ft.DataRow(cells=[
                                ft.DataCell(ft.Text("Números por sorteio")),
                                ft.DataCell(ft.Text(str(info['numeros_por_sorteio']))),
                            ]),
                            ft.DataRow(cells=[
                                ft.DataCell(ft.Text("Sorteios por semana")),
                                ft.DataCell(ft.Text(str(info['sorteios_semana']))),
                            ]),
                            ft.DataRow(cells=[
                                ft.DataCell(ft.Text("Concursos a analisar")),
                                ft.DataCell(ft.Text(str(info['concursos_configurados']))),
                            ]),
                        ],
                    ),
                    ft.Divider(height=20),
                    ft.ElevatedButton(
                        text="📥 Buscar Dados da Caixa",
                        icon=ft.icons.DOWNLOAD,
                        on_click=self.fetch_data,
                    ),
                ])
            )
            
        except Exception as ex:
            self.show_error(f"Erro na configuração: {str(ex)}")
    
    def fetch_data(self, e):
        """Busca dados da API com progresso detalhado"""
        if not self.analyzer:
            return
        
        self.current_operation = "fetch_data"
        
        # Configurar callback de progresso
        def progress_callback(message):
            # Usar a função de update diretamente
            self.update_loading_details(message)
        
        self.analyzer.set_progress_callback(progress_callback)
        
        self.show_loading_with_details(
            "Buscando dados da Caixa Econômica...",
            f"📅 Configurado para analisar aproximadamente {self.selected_years} ano(s) "
            f"({self.analyzer.last_n_games} concursos) de {self.selected_lottery}\n"
            f"🔍 Buscando {self.analyzer.last_n_games} concursos "
            f"(≈{self.selected_years} ano(s)) de {self.selected_lottery}..."
        )
        
        try:
            # Executar em thread separada para não bloquear UI
            def fetch_thread():
                try:
                    # Pequeno delay para mostrar a mensagem inicial
                    time.sleep(0.5)
                    
                    if self.current_operation == "cancelled":
                        return
                    
                    # Buscar dados
                    results = self.analyzer.fetch_results()
                    
                    if self.current_operation != "cancelled":
                        # Atualizar UI após conclusão
                        self.page.run_task(self.show_analysis_results_async)
                        
                except Exception as ex:
                    if self.current_operation != "cancelled":
                        self.page.run_task(self.show_error_async, f"Erro ao buscar dados: {str(ex)}")
            
            self.operation_thread = threading.Thread(target=fetch_thread)
            self.operation_thread.start()
            
        except Exception as ex:
            self.show_error(f"Erro ao iniciar busca: {str(ex)}")
    
    async def show_analysis_results_async(self):
        """Mostra resultados da análise (async)"""
        if not self.analyzer or not self.analyzer.results:
            self.show_error("Nenhum dado disponível")
            return
        
        self.clear_results()
        
        try:
            stats = self.analyzer.calculate_basic_statistics()
            patterns = self.analyzer.analyze_patterns()
            
            # Estatísticas básicas
            basic_stats = ft.Column([
                ft.Text("📈 Estatísticas Básicas", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Métrica")),
                        ft.DataColumn(ft.Text("Valor")),
                    ],
                    rows=[
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text("Concursos analisados")),
                            ft.DataCell(ft.Text(str(stats['total_concursos']))),
                        ]),
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text("Frequência média")),
                            ft.DataCell(ft.Text(f"{stats['frequencia_media']:.2f}")),
                        ]),
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text("Desvio padrão")),
                            ft.DataCell(ft.Text(f"{stats['frequencia_desvio']:.2f}")),
                        ]),
                    ],
                ),
            ])
            
            # Números mais frequentes
            frequent_numbers = ft.Column([
                ft.Text("🔥 Números Mais Frequentes", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
            ])
            
            for num, freq in stats['mais_frequentes'][:10]:
                percentage = (freq / stats['total_concursos']) * 100
                frequent_numbers.controls.append(
                    ft.ListTile(
                        leading=ft.Text(f"{num:02d}", size=18, weight=ft.FontWeight.BOLD),
                        title=ft.Text(f"{freq} vezes"),
                        subtitle=ft.ProgressBar(value=percentage/100, width=200),
                        trailing=ft.Text(f"{percentage:.1f}%"),
                    )
                )
            
            # Números mais atrasados
            delayed_numbers = ft.Column([
                ft.Text("⏰ Números Mais Atrasados", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
            ])
            
            for num, delay in patterns['atrasos']['mais_atrasados'][:10]:
                delayed_numbers.controls.append(
                    ft.ListTile(
                        leading=ft.Text(f"{num:02d}", size=18, weight=ft.FontWeight.BOLD),
                        title=ft.Text(f"{delay} concursos sem sair"),
                        subtitle=ft.ProgressBar(
                            value=min(delay / 100, 1.0), 
                            width=200,
                            color=ft.colors.RED if delay > 50 else ft.colors.ORANGE,
                        ),
                    )
                )
            
            # Menu de opções adicionais
            options_row = ft.Row([
                ft.ElevatedButton(
                    text="🎯 Gerar Sugestões",
                    on_click=self.show_suggestions,
                ),
                ft.ElevatedButton(
                    text="📊 Ver Todos Padrões",
                    on_click=self.show_all_patterns,
                ),
                ft.ElevatedButton(
                    text="📄 Relatório Completo",
                    on_click=self.show_full_report,
                ),
            ], spacing=10)
            
            self.add_result(
                ft.Column([
                    ft.Text(f"✅ {len(self.analyzer.results)} concursos carregados", 
                           size=18, color=ft.colors.GREEN),
                    ft.Divider(height=20),
                    basic_stats,
                    ft.Divider(height=30),
                    frequent_numbers,
                    ft.Divider(height=30),
                    delayed_numbers,
                    ft.Divider(height=30),
                    options_row,
                ], spacing=15)
            )
            
        except Exception as ex:
            self.show_error(f"Erro ao processar resultados: {str(ex)}")
    
    async def show_error_async(self, message):
        """Mostra erro (async)"""
        self.show_error(message)
    
    def show_all_patterns(self, e):
        """Mostra todos os padrões identificados"""
        if not self.analyzer:
            return
        
        self.show_loading("Analisando padrões...")
        
        try:
            patterns = self.analyzer.analyze_patterns()
            
            self.clear_results()
            
            patterns_list = ft.Column([
                ft.Text("🎭 Todos os Padrões Identificados", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
            ])
            
            # Pares/Ímpares
            parity = patterns['pares_impares']
            patterns_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Pares vs Ímpares", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Pares", size=14),
                                    ft.Text(f"{parity['media_pares']:.1f}", size=24, color=ft.colors.BLUE),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Ímpares", size=14),
                                    ft.Text(f"{parity['media_impares']:.1f}", size=24, color=ft.colors.RED),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ]),
                        padding=ft.padding.all(15),
                    )
                )
            )
            
            # Baixos/Altos
            low_high = patterns['baixos_altos']
            patterns_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Baixos vs Altos", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Ponto médio: {low_high['ponto_medio']}", size=14),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Baixos", size=14),
                                    ft.Text(f"{low_high['media_baixos']:.1f}", size=24, color=ft.colors.GREEN),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Altos", size=14),
                                    ft.Text(f"{low_high['media_altos']:.1f}", size=24, color=ft.colors.ORANGE),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ]),
                        padding=ft.padding.all(15),
                    )
                )
            )
            
            # Somas
            sums = patterns['somas']
            patterns_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Somas dos Números", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Mínimo", size=14),
                                    ft.Text(str(sums['minimo']), size=20),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Média", size=14),
                                    ft.Text(f"{sums['media']:.1f}", size=20, color=ft.colors.BLUE),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Máximo", size=14),
                                    ft.Text(str(sums['maximo']), size=20),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Text(f"Faixa ideal: {sums['faixa_ideal'][0]:.0f} a {sums['faixa_ideal'][1]:.0f}", 
                                   size=14, color=ft.colors.BLUE_GREY),
                        ]),
                        padding=ft.padding.all(15),
                    )
                )
            )
            
            # Repetição
            repetition = patterns['repeticao_anterior']
            patterns_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Repetição do Concurso Anterior", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Média", size=14),
                                    ft.Text(f"{repetition['media_repeticao']:.1f}", size=24),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Mínimo", size=14),
                                    ft.Text(str(repetition['min_repeticao']), size=20),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Máximo", size=14),
                                    ft.Text(str(repetition['max_repeticao']), size=20),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ]),
                        padding=ft.padding.all(15),
                    )
                )
            )
            
            self.add_result(patterns_list)
            
        except Exception as ex:
            self.show_error(f"Erro ao analisar padrões: {str(ex)}")
    
    def show_suggestions(self, e=None):
        """Mostra interface para gerar sugestões"""
        if not self.analyzer:
            self.show_error("Primeiro execute uma análise")
            return
        
        self.clear_results()
        
        # Estratégias
        strategies = [
            ("balanced", "🎯 Balanceada", "Combinação com múltiplos critérios estatísticos"),
            ("hot", "🔥 Números Quentes", "Apenas números frequentes recentemente"),
            ("cold", "❄️ Números Frios", "Apenas números atrasados"),
            ("mixed", "🔄 Mista", "Mistura de números quentes, frios e aleatórios"),
            ("statistical", "📊 Estatística", "Baseado em distribuição estatística ideal"),
        ]
        
        # Criar Radio buttons
        strategy_radios = []
        for strategy in strategies:
            strategy_radios.append(
                ft.Radio(
                    value=strategy[0],
                    label=f"{strategy[1]} - {strategy[2]}"
                )
            )
        
        # Grupo de rádio para estratégias
        self.strategy_radio_group = ft.RadioGroup(
            content=ft.Column(strategy_radios, spacing=10),
            value="balanced",
            on_change=lambda e: setattr(self, 'selected_strategy', e.control.value),
        )
        
        self.selected_strategy = "balanced"
        
        # Quantidade
        self.quantity_field = ft.TextField(
            label="Quantidade de combinações",
            value="3",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200,
        )
        
        # Container para resultados de sugestões
        self.suggestions_results_container = ft.Container()
        
        self.add_result(
            ft.Column([
                ft.Text("🎯 Gerar Sugestões de Combinações", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                ft.Text("Selecione a estratégia:", size=18),
                self.strategy_radio_group,
                ft.Divider(height=20),
                ft.Row([
                    self.quantity_field,
                    ft.ElevatedButton(
                        text="Gerar Combinações",
                        icon=ft.icons.AUTO_AWESOME,
                        on_click=self.generate_suggestions,                        
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=30),
                self.suggestions_results_container,
            ])
        )
    
    def generate_suggestions(self, e):
        """Gera e mostra sugestões - Atualizado para análise rápida"""
        try:
            # Verificar se temos analisador e dados
            if not self.analyzer or not self.analyzer.results:
                self.show_error("Primeiro execute uma análise")
                return
            
            # Obter quantidade
            qty_text = self.quantity_field.value
            if not qty_text or not qty_text.strip():
                self.show_error("Digite uma quantidade válida")
                return
                
            qty = int(qty_text)
            if qty < 1 or qty > 20:
                self.show_error("Digite um número entre 1 e 20")
                return
        except ValueError:
            self.show_error("Quantidade inválida. Digite um número.")
            return
        
        # Obter estratégia selecionada
        if self.strategy_radio_group.value:
            self.selected_strategy = self.strategy_radio_group.value
        else:
            self.selected_strategy = "balanced"
        
        self.show_loading_with_details(
            f"Gerando {qty} combinação(ões)...",
            f"Estratégia: {self.selected_strategy}\nUsando {len(self.analyzer.results)} concursos"
        )
        
        # Gerar sugestões em thread
        def generate_in_thread():
            try:
                # Pequeno delay para mostrar o loading
                time.sleep(0.5)
                
                if self.current_operation == "cancelled":
                    return
                
                # Gerar as sugestões
                suggestions = self.analyzer.generate_suggested_numbers(
                    strategy=self.selected_strategy,
                    quantity=qty
                )
                
                if self.current_operation != "cancelled":
                    # Mostrar resultados
                    self.page.run_task(self.display_suggestions_async, suggestions, qty)
                    
            except Exception as ex:
                if self.current_operation != "cancelled":
                    self.page.run_task(self.show_error_async, f"Erro ao gerar sugestões: {str(ex)}")
        
        self.current_operation = "generate_suggestions"
        self.operation_thread = threading.Thread(target=generate_in_thread)
        self.operation_thread.start()
    
    async def display_suggestions_async(self, suggestions, qty):
        """Mostra as sugestões geradas (async)"""
        if self.current_operation == "cancelled":
            return
        
        self.clear_results()
        
        suggestions_list = ft.Column([
            ft.Text(f"🔮 {qty} Combinação(ões) Gerada(s)", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(f"Estratégia: {self.selected_strategy}", size=16, color=ft.colors.BLUE_GREY),
            ft.Divider(height=10),
        ])
        
        for i, comb in enumerate(suggestions, 1):
            pares = sum(1 for n in comb if n % 2 == 0)
            soma_total = sum(comb)
            
            # CORREÇÃO: Usar ft.Text dentro do ft.Chip ou usar ft.Container como alternativa
            suggestions_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"Combinação {i}:", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(f"  {comb}", size=20, color=ft.colors.BLUE, selectable=True),
                            # CORREÇÃO: Usar ft.Row com ft.Container em vez de ft.Chip
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(f"Pares/Ímpares: {pares}/{len(comb)-pares}"),
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    bgcolor=ft.colors.BLUE_50,
                                    border_radius=ft.border_radius.all(20),
                                ),
                                ft.Container(
                                    content=ft.Text(f"Soma: {soma_total}"),
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    bgcolor=ft.colors.GREEN_50,
                                    border_radius=ft.border_radius.all(20),
                                ),
                                ft.Container(
                                    content=ft.Text(f"Média: {soma_total/len(comb):.1f}"),
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    bgcolor=ft.colors.ORANGE_50,
                                    border_radius=ft.border_radius.all(20),
                                ),
                            ], spacing=10),
                        ]),
                        padding=ft.padding.all(15),
                    )
                )
            )
        
        suggestions_list.controls.append(
            ft.ElevatedButton(
                text="🔄 Gerar Novamente",
                on_click=self.generate_suggestions,
                width=200,
            )
        )
        
        self.add_result(suggestions_list)
    
    def show_full_report(self, e=None):
        """Mostra relatório completo - CORRIGIDO"""
        # Verificar se temos um analisador com dados
        if not self.analyzer or not hasattr(self.analyzer, 'results') or not self.analyzer.results:
            self.show_error(
                "Nenhuma análise disponível.\n\n"
                "Primeiro execute uma análise usando:\n"
                "• 'Análise por Anos' (menu à esquerda)\n"
                "• 'Análise Rápida' (menu à esquerda)\n"
                "• 'Gerar Sugestões' após uma análise"
            )
            return
        
        self.show_loading_with_details(
            "Gerando relatório completo...",
            "Processando estatísticas e padrões..."
        )
        
        try:
            # Garantir que temos as variáveis current_lottery e current_years
            if not hasattr(self, 'current_lottery') or not self.current_lottery:
                # Tentar obter do analisador
                if hasattr(self.analyzer, 'lottery_type'):
                    self.current_lottery = self.analyzer.lottery_type
                else:
                    self.current_lottery = "megasena"  # Padrão
            
            if not hasattr(self, 'current_years') or not self.current_years:
                # Tentar estimar anos baseado na quantidade de concursos
                if hasattr(self.analyzer, 'results') and self.analyzer.results:
                    # Estimativa: ~100 concursos por ano para Mega-Sena
                    total_concursos = len(self.analyzer.results)
                    self.current_years = max(1, total_concursos // 100)
                else:
                    self.current_years = 1  # Padrão
            
            # Gerar relatório em thread
            def generate_report_thread():
                try:
                    if self.current_operation == "cancelled":
                        return
                    
                    report = self.analyzer.generate_report()
                    
                    if self.current_operation != "cancelled":
                        self.page.run_task(self.display_full_report_async, report)
                        
                except Exception as ex:
                    if self.current_operation != "cancelled":
                        self.page.run_task(self.show_error_async, f"Erro ao gerar relatório: {str(ex)}")
            
            self.current_operation = "full_report"
            self.operation_thread = threading.Thread(target=generate_report_thread)
            self.operation_thread.start()
            
        except Exception as ex:
            self.show_error(f"Erro ao iniciar geração de relatório: {str(ex)}")

    async def display_full_report_async(self, report):
        """Mostra o relatório completo (async)"""
        if self.current_operation == "cancelled":
            return
        
        self.clear_results()
        
        # Garantir que temos valores para current_lottery e current_years
        lottery_name = "LOTERIA"
        years_text = "PERÍODO"
        
        if hasattr(self, 'current_lottery') and self.current_lottery:
            lottery_name = self.current_lottery.upper()
        
        if hasattr(self, 'current_years') and self.current_years:
            years_text = f"{self.current_years} ano(s)"
        
        # Dividir relatório em partes para melhor visualização
        report_lines = report.split('\n')
        
        # Criar conteúdo do relatório
        report_content = ft.Column([
            ft.Text("📄 Relatório Completo", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20),
            
            ft.Row([
                ft.Icon(ft.icons.CASINO, size=30, color=ft.colors.BLUE),
                ft.Text(f"{lottery_name} - {years_text}", 
                       size=18, weight=ft.FontWeight.BOLD),
            ]),
            
            ft.Divider(height=20),
            
            # Estatísticas rápidas (se disponível)
            ft.Container(
                visible=hasattr(self, 'analyzer') and self.analyzer and hasattr(self.analyzer, 'results'),
                content=ft.Row([
                    ft.Column([
                        ft.Text("Concursos", size=12, color=ft.colors.BLUE_GREY),
                        ft.Text(str(len(self.analyzer.results)) if self.analyzer and hasattr(self.analyzer, 'results') else "0", 
                               size=16, weight=ft.FontWeight.BOLD),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=20),
                    ft.Column([
                        ft.Text("Data Inicial", size=12, color=ft.colors.BLUE_GREY),
                        ft.Text(self.analyzer.results[0]['data'][:10] if self.analyzer.results else "N/A", 
                               size=14),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=20),
                    ft.Column([
                        ft.Text("Data Final", size=12, color=ft.colors.BLUE_GREY),
                        ft.Text(self.analyzer.results[-1]['data'][:10] if self.analyzer.results else "N/A", 
                               size=14),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.all(10),
                bgcolor=ft.colors.BLUE_50,
                border_radius=ft.border_radius.all(10),
            ),
            
            ft.Divider(height=20),
            
            # Conteúdo do relatório
            ft.Container(
                content=ft.Column([
                    ft.Text(line, size=12, font_family="monospace", selectable=True) 
                    for line in report_lines
                ], scroll=ft.ScrollMode.AUTO),
                height=400,
                padding=ft.padding.all(10),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(5),
                bgcolor=ft.colors.GREY_50,
            ),
            
            ft.Divider(height=20),
            
            # Botões de ação
            ft.Row([
                ft.ElevatedButton(
                    text="📋 Copiar Relatório",
                    on_click=lambda e: self.page.run_task(self.copy_to_clipboard, report),
                    icon=ft.icons.CONTENT_COPY,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.GREEN,
                        color=ft.colors.WHITE,
                    ),
                ),
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Divider(height=20),
            
            # Botões de navegação
            ft.Row([
                ft.ElevatedButton(
                    text="← Voltar",
                    on_click=lambda e: self.show_analysis_results_async() 
                                      if hasattr(self, 'analyzer') and self.analyzer 
                                      else self.show_home(e),
                    icon=ft.icons.ARROW_BACK,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.GREY_300,
                        color=ft.colors.BLACK,
                    ),
                ),
                ft.ElevatedButton(
                    text="🏠 Início",
                    on_click=self.show_home,
                    icon=ft.icons.HOME,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE_300,
                        color=ft.colors.WHITE,
                    ),
                ),
            ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
        ])
        
        self.add_result(report_content)

    # Também adicione este método auxiliar para obter nome da loteria
    def get_lottery_display_name(self, lottery_code):
        """Retorna nome amigável da loteria"""
        if not lottery_code:
            return "LOTERIA"
        
        names = {
            "megasena": "MEGA-SENA",
            "lotofacil": "LOTOFÁCIL",
            "quina": "QUINA",
            "lotomania": "LOTOMANIA",
            "duplasena": "DUPLA SENA",
            "diadesorte": "DIA DE SORTE",
            "timemania": "TIMEMANIA"
        }
        return names.get(lottery_code.lower(), lottery_code.upper())

    def print_report(self, report):
        """Prepara o relatório para impressão"""
        try:
            # Em ambiente web, usa window.print()
            import js
            # Cria uma nova janela/aba com o relatório formatado para impressão
            print_window = js.window.open("", "_blank")
            
            # HTML formatado para impressão
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Relatório - {self.current_lottery.upper()}</title>
                <style>
                    body {{ font-family: monospace; padding: 20px; }}
                    h1 {{ color: #1a73e8; }}
                    .header {{ margin-bottom: 30px; }}
                    .content {{ white-space: pre-wrap; line-height: 1.4; }}
                    @media print {{
                        body {{ font-size: 12pt; }}
                        button {{ display: none; }}
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📄 Relatório Completo - {self.current_lottery.upper()}</h1>
                    <p><strong>Período:</strong> {self.current_years} ano(s)</p>
                    <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                <div class="content">{report.replace('\n', '<br>')}</div>
                <br><br>
                <button onclick="window.print()">🖨️ Imprimir</button>
                <button onclick="window.close()">❌ Fechar</button>
            </body>
            </html>
            """
            
            print_window.document.write(html_content)
            print_window.document.close()
            
            self.show_snackbar("✅ Janela de impressão aberta")
            
        except:
            # Fallback: mostra em diálogo
            self.show_dialog(
                "🖨️ Imprimir Relatório",
                "Para imprimir, copie o conteúdo abaixo e cole em um editor de texto:",
                report,
                show_copy_button=True
            )
    
    def show_snackbar(self, message):
        """Mostra snackbar com mensagem"""
        if not hasattr(self, 'page') or not self.page:
            return
            
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            action="OK",
            action_color=ft.colors.BLUE,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show_dialog(self, title, message, content=None, show_copy_button=False):
        """Mostra diálogo"""
        dialog_content = ft.Column([
            ft.Text(message, size=14),
            ft.Divider(height=20),
        ])
        
        if content:
            dialog_content.controls.append(
                ft.Container(
                    content=ft.Text(content, size=12, font_family="monospace", selectable=True),
                    height=200,
                    padding=ft.padding.all(10),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=ft.border_radius.all(5),
                )
            )
        
        controls = [ft.TextButton("Fechar", on_click=lambda e: self.close_dialog())]
        
        if show_copy_button and content:
            controls.insert(0, ft.TextButton("📋 Copiar", 
                on_click=lambda e: self.copy_to_clipboard(content)))
        
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=dialog_content,
            actions=controls,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_dialog(self):
        """Fecha diálogo atual"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def show_quick_analysis(self, e):
        """Mostra interface para análise rápida dos últimos 3 anos"""
        self.clear_results()
        
        # Mostrar opções de análise rápida de 3 anos
        self.add_result(
            ft.Column([
                ft.Text("⚡ Análise Rápida (3 Anos)", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Escolha uma loteria para análise dos últimos 3 anos:", 
                    size=16, color=ft.colors.BLUE_GREY),
                ft.Divider(height=20),
                
                # Card de explicação
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.INFO, size=24, color=ft.colors.BLUE),
                                ft.Text("Como funciona:", size=16, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Text(
                                "• Analisa automaticamente os últimos 3 anos de concursos\n"
                                "• Busca dados da API da Caixa Econômica\n"
                                "• Gera relatório estatístico completo\n"
                                "• Permite gerar sugestões de combinações",
                                size=14,
                            ),
                        ]),
                        padding=ft.padding.all(20),
                    ),
                    elevation=3,
                ),
                
                ft.Divider(height=30),
                
                # Botões das loterias para 3 anos
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.EMOJI_EVENTS, size=40, color=ft.colors.BLUE),
                            ft.Text("Mega-Sena", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("3 anos", size=12, color=ft.colors.GREEN),
                            ft.Text("60 números", size=11, color=ft.colors.BLUE_GREY),
                            ft.Text("Sorteios: Qua/Sáb", size=10, color=ft.colors.BLUE_GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=ft.padding.all(15),
                        border=ft.border.all(2, ft.colors.BLUE),
                        border_radius=ft.border_radius.all(10),
                        on_click=lambda e: self.run_quick_3years("megasena"),
                        width=140,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.CASINO, size=40, color=ft.colors.GREEN),
                            ft.Text("Lotofácil", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("3 anos", size=12, color=ft.colors.GREEN),
                            ft.Text("25 números", size=11, color=ft.colors.BLUE_GREY),
                            ft.Text("Sorteios: Seg/Qua/Sex", size=10, color=ft.colors.BLUE_GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=ft.padding.all(15),
                        border=ft.border.all(2, ft.colors.GREEN),
                        border_radius=ft.border_radius.all(10),
                        on_click=lambda e: self.run_quick_3years("lotofacil"),
                        width=140,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.STAR, size=40, color=ft.colors.ORANGE),
                            ft.Text("Quina", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("3 anos", size=12, color=ft.colors.GREEN),
                            ft.Text("80 números", size=11, color=ft.colors.BLUE_GREY),
                            ft.Text("Sorteios: Seg-Sáb", size=10, color=ft.colors.BLUE_GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=ft.padding.all(15),
                        border=ft.border.all(2, ft.colors.ORANGE),
                        border_radius=ft.border_radius.all(10),
                        on_click=lambda e: self.run_quick_3years("quina"),
                        width=140,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.CALENDAR_VIEW_MONTH, size=40, color=ft.colors.PURPLE),
                            ft.Text("Lotomania", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("3 anos", size=12, color=ft.colors.GREEN),
                            ft.Text("100 números", size=11, color=ft.colors.BLUE_GREY),
                            ft.Text("Sorteios: Ter/Sex", size=10, color=ft.colors.BLUE_GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=ft.padding.all(15),
                        border=ft.border.all(2, ft.colors.PURPLE),
                        border_radius=ft.border_radius.all(10),
                        on_click=lambda e: self.run_quick_3years("lotomania"),
                        width=140,
                    ),
                ], spacing=15, alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                
                ft.Divider(height=30),
                
                # Mais loterias
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.FILTER_2, size=40, color=ft.colors.RED),
                            ft.Text("Dupla Sena", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("3 anos", size=12, color=ft.colors.GREEN),
                            ft.Text("50 números", size=11, color=ft.colors.BLUE_GREY),
                            ft.Text("Sorteios: Ter/Qui/Sáb", size=10, color=ft.colors.BLUE_GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=ft.padding.all(15),
                        border=ft.border.all(2, ft.colors.RED),
                        border_radius=ft.border_radius.all(10),
                        on_click=lambda e: self.run_quick_3years("duplasena"),
                        width=140,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.WB_SUNNY, size=40, color=ft.colors.AMBER),
                            ft.Text("Dia de Sorte", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("3 anos", size=12, color=ft.colors.GREEN),
                            ft.Text("31 números", size=11, color=ft.colors.BLUE_GREY),
                            ft.Text("Sorteios: Ter/Sex", size=10, color=ft.colors.BLUE_GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=ft.padding.all(15),
                        border=ft.border.all(2, ft.colors.AMBER),
                        border_radius=ft.border_radius.all(10),
                        on_click=lambda e: self.run_quick_3years("diadesorte"),
                        width=140,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.SCHEDULE, size=40, color=ft.colors.CYAN),
                            ft.Text("Timemania", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("3 anos", size=12, color=ft.colors.GREEN),
                            ft.Text("80 números", size=11, color=ft.colors.BLUE_GREY),
                            ft.Text("Sorteios: Ter/Qui/Sáb", size=10, color=ft.colors.BLUE_GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        padding=ft.padding.all(15),
                        border=ft.border.all(2, ft.colors.CYAN),
                        border_radius=ft.border_radius.all(10),
                        on_click=lambda e: self.run_quick_3years("timemania"),
                        width=140,
                    ),
                ], spacing=15, alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                
                ft.Divider(height=40),
                
                # Nota sobre o processamento
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.HOURGLASS_EMPTY, size=20, color=ft.colors.ORANGE),
                            ft.Text("Tempo estimado de processamento:", size=14, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text("A primeira análise pode levar alguns minutos para buscar todos os dados. "
                            "Os resultados são armazenados em cache para consultas futuras.",
                            size=12, color=ft.colors.BLUE_GREY),
                    ]),
                    padding=ft.padding.all(15),
                    bgcolor=ft.colors.ORANGE_50,
                    border_radius=ft.border_radius.all(10),
                ),
            ], scroll=ft.ScrollMode.AUTO)
        )

    def run_quick_3years(self, lottery):
        """Executa análise rápida de 3 anos da loteria especificada"""
        self.selected_lottery = lottery
        self.selected_years = 3  # SEMPRE 3 anos para análise rápida
        
        # Obter nome amigável da loteria
        lottery_names = {
            "megasena": "Mega-Sena",
            "lotofacil": "Lotofácil", 
            "quina": "Quina",
            "lotomania": "Lotomania",
            "duplasena": "Dupla Sena",
            "diadesorte": "Dia de Sorte",
            "timemania": "Timemania"
        }
        lottery_name = lottery_names.get(lottery, lottery)
        
        self.show_loading_with_details(
            f"Analisando 3 anos de {lottery_name}...",
            f"📊 Configurando análise de {lottery_name.upper()}\n"
            f"📅 Período: 3 anos (últimos concursos)\n"
            f"🔄 Preparando busca de dados..."
        )
        
        def start_3years_analysis():
            try:
                # Criar analisador para 3 anos
                self.analyzer = LotteryPatternAnalyzer(lottery, years=3)
                
                # Configurar callback de progresso detalhado
                def progress_callback(message):
                    self.update_loading_details(f"{message}")
                
                self.analyzer.set_progress_callback(progress_callback)
                
                # Atualizar status
                self.update_loading_details(f"🔍 Buscando dados históricos de {lottery_name}...")
                
                # Buscar dados (com cache)
                self.analyzer.fetch_results(use_cache=True)
                
                # Calcular estatísticas básicas para mostrar informações
                stats = self.analyzer.calculate_basic_statistics()
                
                if self.current_operation != "cancelled":
                    # Mostrar tela de sugestões diretamente
                    self.page.run_task(self.show_quick_analysis_results, lottery_name, stats)
                    
            except Exception as ex:
                if self.current_operation != "cancelled":
                    self.page.run_task(self.show_error_async, f"Erro na análise de 3 anos: {str(ex)}")
        
        # Iniciar thread para análise
        self.current_operation = "3years_analysis"
        threading.Thread(target=start_3years_analysis).start()

    async def show_quick_analysis_results(self, lottery_name, stats):
        """Mostra resultados da análise rápida de 3 anos"""
        if not self.analyzer or not self.analyzer.results:
            self.show_error("Não foi possível carregar dados para análise")
            return
        
        self.clear_results()
        
        # Calcular mais estatísticas se necessário
        patterns = self.analyzer.analyze_patterns()
        
        # Card de resumo
        summary_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=30),
                        ft.Text("✅ Análise Concluída", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Divider(height=10),
                    
                    # Informações principais
                    ft.Row([
                        ft.Column([
                            ft.Text("LOTERIA", size=12, color=ft.colors.BLUE_GREY),
                            ft.Text(lottery_name.upper(), size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.VerticalDivider(width=20),
                        ft.Column([
                            ft.Text("PERÍODO", size=12, color=ft.colors.BLUE_GREY),
                            ft.Text("3 ANOS", size=18, weight=ft.FontWeight.BOLD),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.VerticalDivider(width=20),
                        ft.Column([
                            ft.Text("CONCURSOS", size=12, color=ft.colors.BLUE_GREY),
                            ft.Text(str(stats['total_concursos']), size=18, weight=ft.FontWeight.BOLD),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=15),
                    
                    # Estatísticas rápidas
                    ft.Row([
                        ft.Column([
                            ft.Text("🔥 MAIS QUENTE", size=11, color=ft.colors.BLUE_GREY),
                            ft.Container(
                                content=ft.Text(f"{stats['mais_frequentes'][0][0]:02d}", 
                                            size=24, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
                                padding=ft.padding.all(8),
                                bgcolor=ft.colors.RED_50,
                                border_radius=ft.border_radius.all(20),
                            ),
                            ft.Text(f"{stats['mais_frequentes'][0][1]} vezes", size=11),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        
                        ft.VerticalDivider(width=15),
                        
                        ft.Column([
                            ft.Text("❄️ MAIS FRIO", size=11, color=ft.colors.BLUE_GREY),
                            ft.Container(
                                content=ft.Text(f"{stats['menos_frequentes'][0][0]:02d}", 
                                            size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                                padding=ft.padding.all(8),
                                bgcolor=ft.colors.BLUE_50,
                                border_radius=ft.border_radius.all(20),
                            ),
                            ft.Text(f"{stats['menos_frequentes'][0][1]} vezes", size=11),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        
                        ft.VerticalDivider(width=15),
                        
                        ft.Column([
                            ft.Text("⏰ MAIS ATRASADO", size=11, color=ft.colors.BLUE_GREY),
                            ft.Container(
                                content=ft.Text(f"{patterns['atrasos']['mais_atrasados'][0][0]:02d}", 
                                            size=24, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE),
                                padding=ft.padding.all(8),
                                bgcolor=ft.colors.ORANGE_50,
                                border_radius=ft.border_radius.all(20),
                            ),
                            ft.Text(f"{patterns['atrasos']['mais_atrasados'][0][1]} concursos", size=11),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ]),
                padding=ft.padding.all(20),
            ),
            elevation=5,
        )
        
        # Interface de geração de sugestões (igual ao anterior)
        strategies = [
            ("balanced", "🎯 Balanceada", "Combinação com múltiplos critérios estatísticos"),
            ("hot", "🔥 Números Quentes", "Apenas números frequentes recentemente"),
            ("cold", "❄️ Números Frios", "Apenas números atrasados"),
            ("mixed", "🔄 Mista", "Mistura de números quentes, frios e aleatórios"),
            ("statistical", "📊 Estatística", "Baseado em distribuição estatística ideal"),
        ]
        
        # Criar Radio buttons com descrição
        strategy_radios = []
        for strategy in strategies:
            strategy_radios.append(
                ft.Radio(
                    value=strategy[0],
                    label=f"{strategy[1]} - {strategy[2]}"
                )
            )
        
        self.strategy_radio_group = ft.RadioGroup(
            content=ft.Column(strategy_radios, spacing=15),
            value="balanced",
        )
        
        self.selected_strategy = "balanced"
        
        # Quantidade
        self.quantity_field = ft.TextField(
            label="Quantidade de combinações",
            value="5",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200,
            text_size=16,
        )
        
        # Container para resultados
        self.suggestions_results_container = ft.Container()
        
        # Layout completo
        self.add_result(
            ft.Column([
                ft.Text(f"⚡ {lottery_name.upper()} - Sugestões de Combinações", 
                    size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                summary_card,
                ft.Divider(height=30),
                
                ft.Text("🎯 Selecione a estratégia para gerar combinações:", 
                    size=18, weight=ft.FontWeight.BOLD),
                self.strategy_radio_group,
                
                ft.Divider(height=20),
                
                ft.Text("Quantidade de combinações a gerar:", size=16),
                ft.Container(
                    content=self.quantity_field,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=20)
                ),
                
                ft.Container(
                    content=ft.ElevatedButton(
                        text="✨ Gerar Combinações",
                        icon=ft.icons.AUTO_AWESOME,
                        on_click=self.generate_suggestions,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=30, vertical=15),
                        ),
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=30)
                ),
                
                ft.Divider(height=10),
                self.suggestions_results_container,
                
                # Botões de ação
                ft.Container(
                    content=ft.Row([
                        ft.ElevatedButton(
                            text="📊 Ver Relatório Completo",
                            icon=ft.icons.ANALYTICS,
                            on_click=self.show_full_report,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.GREEN,
                                color=ft.colors.WHITE,
                            ),
                        ),
                        ft.ElevatedButton(
                            text="🔄 Nova Análise",
                            icon=ft.icons.REFRESH,
                            on_click=self.show_quick_analysis,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.ORANGE,
                                color=ft.colors.WHITE,
                            ),
                        ),
                    ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=20),
                ),
            ], scroll=ft.ScrollMode.AUTO)
        )
    
    def run_quick_analysis(self, lottery):
        """Executa análise rápida"""
        self.show_loading_with_details(
            f"Analisando 1 ano de {lottery}...",
            "Inicializando análise rápida..."
        )
        
        try:
            analyzer = LotteryPatternAnalyzer(lottery, years=1)
            
            # Buscar dados em thread
            def fetch_quick_data():
                try:
                    if self.current_operation == "cancelled":
                        return
                    
                    self.update_loading_details("Buscando dados da Caixa...")
                    analyzer.fetch_results()
                    
                    if self.current_operation != "cancelled":
                        stats = analyzer.calculate_basic_statistics()
                        patterns = analyzer.analyze_patterns()
                        
                        self.page.run_task(lambda: self.display_quick_results_async(
                            analyzer, lottery, stats, patterns
                        ))
                        
                except Exception as ex:
                    if self.current_operation != "cancelled":
                        self.page.run_task(self.show_error_async, f"Erro na análise rápida: {str(ex)}")
            
            self.current_operation = "quick_analysis"
            self.operation_thread = threading.Thread(target=fetch_quick_data)
            self.operation_thread.start()
            
        except Exception as ex:
            self.show_error(f"Erro na análise rápida: {str(ex)}")
    
    async def display_quick_results_async(self, analyzer, lottery, stats, patterns):
        """Mostra resultados da análise rápida (async)"""
        self.clear_results()
        
        results_content = ft.Column([
            ft.Text(f"✅ Análise rápida concluída!", size=18, color=ft.colors.GREEN),
            ft.Divider(height=10),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Métrica")),
                    ft.DataColumn(ft.Text("Valor")),
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Concursos analisados")),
                        ft.DataCell(ft.Text(str(stats['total_concursos']))),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Número mais frequente")),
                        ft.DataCell(ft.Text(f"{stats['mais_frequentes'][0][0]} ({stats['mais_frequentes'][0][1]} vezes)")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Número mais atrasado")),
                        ft.DataCell(ft.Text(f"{patterns['atrasos']['mais_atrasados'][0][0]} ({patterns['atrasos']['mais_atrasados'][0][1]} concursos)")),
                    ]),
                ],
            ),
            ft.Divider(height=20),
            ft.ElevatedButton(
                text="🔍 Análise Detalhada",
                on_click=lambda e: self.load_analyzer_for_detailed(analyzer, lottery, 1),
            ),
        ])
        
        self.quick_results_container.content = results_content
        self.page.update()
    
    def load_analyzer_for_detailed(self, analyzer, lottery, years):
        """Carrega analisador para análise detalhada"""
        self.analyzer = analyzer
        self.current_lottery = lottery
        self.current_years = years
        self.show_analysis_results_async()
    
    def show_comparison(self, e):
        """Mostra interface para comparar loterias"""
        self.clear_results()
        
        # Container para resultados de comparação
        self.comparison_results_container = ft.Container()
        
        # Opções de loterias para comparação
        loterias_comparacao = [
            ("megasena", "Mega-Sena", ft.colors.BLUE, "60 números"),
            ("lotofacil", "Lotofácil", ft.colors.GREEN, "25 números"),
            ("quina", "Quina", ft.colors.ORANGE, "80 números"),
            ("lotomania", "Lotomania", ft.colors.PURPLE, "100 números"),
        ]
        
        # Checkboxes para seleção
        self.comparison_checkboxes = {}
        checkboxes_row = ft.Column(spacing=10)
        
        for lottery, name, color, info in loterias_comparacao:
            checkbox = ft.Checkbox(
                label=f"{name} ({info})",
                value=True,  # Selecionado por padrão
                fill_color=color,
            )
            self.comparison_checkboxes[lottery] = checkbox
            checkboxes_row.controls.append(checkbox)
        
        # Opções de período
        self.comparison_period = ft.Dropdown(
            label="Período de análise",
            width=200,
            options=[
                ft.dropdown.Option("1", "1 ano"),
                ft.dropdown.Option("2", "2 anos"),
                ft.dropdown.Option("3", "3 anos"),
                ft.dropdown.Option("5", "5 anos"),
            ],
            value="1",  # Padrão: 1 ano
        )
        
        self.add_result(
            ft.Column([
                ft.Text("🔄 Comparar Loterias", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.COMPARE_ARROWS, size=30, color=ft.colors.BLUE),
                                ft.Text("Como funciona:", size=18, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Text(
                                "Compare estatísticas entre diferentes loterias para identificar padrões "
                                "e características únicas de cada uma.",
                                size=14,
                            ),
                        ]),
                        padding=ft.padding.all(20),
                    ),
                    elevation=3,
                ),
                
                ft.Divider(height=30),
                
                ft.Text("Selecione as loterias para comparar:", size=18, weight=ft.FontWeight.BOLD),
                checkboxes_row,
                
                ft.Divider(height=20),
                
                ft.Text("Selecione o período de análise:", size=16),
                ft.Container(
                    content=self.comparison_period,
                    alignment=ft.alignment.center_left,
                    padding=ft.padding.only(bottom=20)
                ),
                
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Iniciar Comparação",
                        icon=ft.icons.PLAY_ARROW,
                        on_click=self.run_comparison,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=25, vertical=12),
                        ),
                    ),
                    alignment=ft.alignment.center_left,
                    padding=ft.padding.only(bottom=20)
                ),
                
                ft.Divider(height=30),
                self.comparison_results_container,
            ], scroll=ft.ScrollMode.AUTO)
        )

    def run_comparison(self, e):
        """Executa comparação entre loterias selecionadas"""
        # Obter loterias selecionadas
        selected_lotteries = []
        for lottery, checkbox in self.comparison_checkboxes.items():
            if checkbox.value:  # Se está marcado
                selected_lotteries.append(lottery)
        
        if not selected_lotteries:
            self.show_error("Selecione pelo menos uma loteria para comparar")
            return
        
        # Obter período
        try:
            years = int(self.comparison_period.value)
        except:
            years = 1
        
        self.show_loading_with_details(
            "Comparando loterias...",
            f"Preparando análise de {len(selected_lotteries)} loteria(s) por {years} ano(s)..."
        )
        
        # Iniciar comparação em thread
        def comparison_thread():
            results = []
            
            for i, lottery in enumerate(selected_lotteries):
                if self.current_operation == "cancelled":
                    break
                
                try:
                    # Atualizar progresso
                    progress_msg = f"Analisando {lottery} ({i+1}/{len(selected_lotteries)})..."
                    self.update_loading_details(progress_msg)
                    
                    # Criar analisador
                    analyzer = LotteryPatternAnalyzer(lottery, years=years)
                    
                    # Configurar callback de progresso
                    def progress_callback(message):
                        self.update_loading_details(f"{progress_msg}\n{message}")
                    
                    analyzer.set_progress_callback(progress_callback)
                    
                    # Buscar dados
                    analyzer.fetch_results(use_cache=True)
                    
                    # Calcular estatísticas
                    stats = analyzer.calculate_basic_statistics()
                    patterns = analyzer.analyze_patterns()
                    
                    # Armazenar resultados
                    results.append({
                        "loteria": lottery.upper(),
                        "nome": self.get_lottery_display_name(lottery),
                        "concursos": stats['total_concursos'],
                        "freq_media": stats['frequencia_media'],
                        "freq_desvio": stats['frequencia_desvio'],
                        "mais_freq": stats['mais_frequentes'][0] if stats['mais_frequentes'] else ("N/A", 0),
                        "mais_atrasado": patterns['atrasos']['mais_atrasados'][0] if patterns['atrasos']['mais_atrasados'] else ("N/A", 0),
                        "media_pares": patterns['pares_impares']['media_pares'],
                        "media_soma": patterns['somas']['media'],
                        "cor": self.get_lottery_color(lottery),
                        "years": years,
                    })
                    
                except Exception as ex:
                    print(f"Erro ao analisar {lottery}: {ex}")
                    # Continua com as outras loterias
            
            if self.current_operation != "cancelled" and results:
                self.page.run_task(self.display_comparison_results_async, results, years)
        
        self.current_operation = "comparison"
        self.operation_thread = threading.Thread(target=comparison_thread)
        self.operation_thread.start()

    def get_lottery_display_name(self, lottery_code):
        """Retorna o nome amigável da loteria"""
        names = {
            "megasena": "Mega-Sena",
            "lotofacil": "Lotofácil",
            "quina": "Quina",
            "lotomania": "Lotomania",
            "duplasena": "Dupla Sena",
            "diadesorte": "Dia de Sorte",
            "timemania": "Timemania"
        }
        return names.get(lottery_code, lottery_code.upper())

    def get_lottery_color(self, lottery_code):
        """Retorna a cor associada à loteria"""
        colors = {
            "megasena": ft.colors.BLUE,
            "lotofacil": ft.colors.GREEN,
            "quina": ft.colors.ORANGE,
            "lotomania": ft.colors.PURPLE,
            "duplasena": ft.colors.RED,
            "diadesorte": ft.colors.AMBER,
            "timemania": ft.colors.CYAN
        }
        return colors.get(lottery_code, ft.colors.BLUE)

    async def display_comparison_results_async(self, results, years):
        """Mostra resultados da comparação (async)"""
        if not results:
            self.show_error("Nenhum resultado obtido para comparação")
            return
        
        self.clear_results()
        
        comparison_content = ft.Column([
            ft.Text("📈 Resultados da Comparação", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(f"Período analisado: {years} ano(s)", size=16, color=ft.colors.BLUE_GREY),
            ft.Divider(height=20),
        ])
        
        # Tabela comparativa
        table_rows = []
        
        # Cabeçalho da tabela
        table_rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text("Loteria", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text("Concursos", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text("Freq. Média", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text("Nº Mais Quente", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text("Nº Mais Frio", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text("Média Pares", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text("Média Soma", weight=ft.FontWeight.BOLD)),
                ]
            )
        )
        
        # Linhas com dados
        for result in results:
            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(result["nome"], color=result["cor"], weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(str(result["concursos"]))),
                        ft.DataCell(ft.Text(f"{result['freq_media']:.1f}")),
                        ft.DataCell(ft.Text(f"{result['mais_freq'][0]} ({result['mais_freq'][1]}x)")),
                        ft.DataCell(ft.Text(f"{result['mais_atrasado'][0]} ({result['mais_atrasado'][1]} atr.)")),
                        ft.DataCell(ft.Text(f"{result['media_pares']:.1f}")),
                        ft.DataCell(ft.Text(f"{result['media_soma']:.1f}")),
                    ]
                )
            )
        
        comparison_content.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("")),
                            ft.DataColumn(ft.Text(""), numeric=True),
                            ft.DataColumn(ft.Text(""), numeric=True),
                            ft.DataColumn(ft.Text(""), numeric=True),
                            ft.DataColumn(ft.Text(""), numeric=True),
                            ft.DataColumn(ft.Text(""), numeric=True),
                            ft.DataColumn(ft.Text(""), numeric=True),
                        ],
                        rows=table_rows,
                        heading_row_height=50,
                        data_row_min_height=50,
                        horizontal_margin=10,
                    ),
                    padding=ft.padding.all(20),
                ),
                elevation=5,
            )
        )
        
        # Gráfico de comparação (simulado com containers coloridos)
        ft.Divider(height=30),
        
        comparison_content.controls.append(
            ft.Text("📊 Comparação Visual - Frequência Média", size=18, weight=ft.FontWeight.BOLD)
        )
        
        comparison_content.controls.append(
            ft.Text("Altura das barras representa a frequência média dos números", 
                size=12, color=ft.colors.BLUE_GREY)
        )
        
        # Encontrar valor máximo para normalização
        max_freq = max([r["freq_media"] for r in results]) if results else 1
        
        # Criar barras
        bars_container = ft.Row(
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            height=200,
            vertical_alignment=ft.CrossAxisAlignment.END
        )
        
        for result in results:
            bar_height = (result["freq_media"] / max_freq) * 150  # Normalizar para máximo 150px
            bars_container.controls.append(
                ft.Column([
                    ft.Container(
                        content=ft.Text(f"{result['freq_media']:.1f}", 
                                    color=ft.colors.WHITE, size=12),
                        width=60,
                        height=bar_height,
                        bgcolor=result["cor"],
                        border_radius=ft.border_radius.only(top_left=5, top_right=5),
                        alignment=ft.alignment.bottom_center,
                    ),
                    ft.Text(result["nome"], size=12, weight=ft.FontWeight.BOLD),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        
        comparison_content.controls.append(
            ft.Container(
                content=bars_container,
                padding=ft.padding.all(20),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(10),
            )
        )
        
        # Botões de ação
        comparison_content.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        text="🔄 Nova Comparação",
                        icon=ft.icons.REFRESH,
                        on_click=self.show_comparison,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                        ),
                    ),
                    ft.ElevatedButton(
                        text="📥 Exportar Dados",
                        icon=ft.icons.DOWNLOAD,
                        on_click=lambda e: self.export_comparison_data(results),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.GREEN,
                            color=ft.colors.WHITE,
                        ),
                    ),
                ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=30),
            )
        )
        
        self.add_result(comparison_content)

    def export_comparison_data(self, results):
        """Exporta dados da comparação"""
        try:
            import json
            from datetime import datetime
            
            # Criar estrutura de dados
            export_data = {
                "data_geracao": datetime.now().isoformat(),
                "resultados": results
            }
            
            # Converter para JSON
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # Mostrar em diálogo
            self.show_dialog(
                "📥 Exportar Dados da Comparação",
                "Copie os dados abaixo para salvá-los:",
                json_data,
                show_copy_button=True
            )
            
        except Exception as ex:
            self.show_error(f"Erro ao exportar dados: {str(ex)}")
    
    def show_supported_lotteries(self, e):
        """Mostra todas as loterias suportadas"""
        self.clear_results()
        
        # Obter informações das loterias
        loterias_info = []
        
        for lottery in ["megasena", "lotofacil", "quina", "lotomania", "duplasena", "diadesorte", "timemania"]:
            try:
                analyzer = LotteryPatternAnalyzer(lottery, years=1)
                info = analyzer.get_lottery_info()
                loterias_info.append(info)
            except:
                continue
        
        # Criar cards para cada loteria
        lottery_cards = ft.Column([
            ft.Text("📚 Loterias Suportadas", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20),
        ])
        
        for info in loterias_info:
            lottery_cards.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.CASINO, size=30, color=ft.colors.BLUE),
                                ft.Text(info["tipo"].upper(), size=20, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Divider(height=10),
                            ft.Text(info["descricao"], size=14, color=ft.colors.BLUE_GREY),
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Faixa:", size=12),
                                    ft.Text(info["faixa_numeros"], size=14, weight=ft.FontWeight.BOLD),
                                ]),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Por sorteio:", size=12),
                                    ft.Text(str(info["numeros_por_sorteio"]), size=14, weight=ft.FontWeight.BOLD),
                                ]),
                                ft.VerticalDivider(width=20),
                                ft.Column([
                                    ft.Text("Semana:", size=12),
                                    ft.Text(f"{info['sorteios_semana']}x", size=14, weight=ft.FontWeight.BOLD),
                                ]),
                            ]),
                            ft.Divider(height=10),
                            ft.Text(f"1 ano ≈ {info['concursos_configurados']} concursos", 
                                   size=12, color=ft.colors.GREEN),
                        ]),
                        padding=ft.padding.all(20),
                    )
                )
            )
        
        self.add_result(lottery_cards)
    
    def show_about(self, e):
        """Mostra informações sobre o aplicativo"""
        self.clear_results()
        
        self.add_result(
            ft.Column([
                ft.Text("ℹ️ Sobre o DeuSorte - Analisador de Loterias", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.INFO, color=ft.colors.BLUE),
                                title=ft.Text("Versão 2.0"),
                                subtitle=ft.Text("Desenvolvedor: Juliano Gomes\nTipo de Licença: MIT License (pendente de confirmação)"),
                            ),
                            ft.TextButton(
                                text="Acessar Repositório no GitHub",
                                on_click=lambda e: self.page.launch_url("https://github.com/jcgomes/DeuSorte"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.BLUE,
                                    color=ft.colors.WHITE,
                                    padding=ft.padding.symmetric(horizontal=20, vertical=10),  # Padding personalizado
                                    shape=ft.RoundedRectangleBorder(radius=8),  # Bordas arredondadas
                                ),
                            ),
                            ft.Divider(height=10),
                            ft.Text(
                                "Este aplicativo permite analisar estatisticamente os resultados "
                                "históricos das loterias da Caixa Econômica Federal. "
                                "Com ele, você pode identificar padrões, tendências e gerar "
                                "combinações baseadas em dados históricos.",
                                size=14,
                            ),
                            ft.Divider(height=20),
                            ft.Text("🎯 Funcionalidades:", size=16, weight=ft.FontWeight.BOLD),
                            ft.Column([
                                ft.Row([ft.Icon(ft.icons.CHECK), ft.Text("Análise por anos (1, 2, 3, 5 anos)")]),
                                ft.Row([ft.Icon(ft.icons.CHECK), ft.Text("Busca automática de dados da API da Caixa")]),
                                ft.Row([ft.Icon(ft.icons.CHECK), ft.Text("Identificação de números quentes e frios")]),
                                ft.Row([ft.Icon(ft.icons.CHECK), ft.Text("Geração de sugestões com diferentes estratégias")]),
                                ft.Row([ft.Icon(ft.icons.CHECK), ft.Text("Comparação entre diferentes loterias")]),
                                ft.Row([ft.Icon(ft.icons.CHECK), ft.Text("Relatórios completos e exportáveis")]),
                            ], spacing=5),
                            ft.Divider(height=20),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("⚠️ AVISO LEGAL", size=16, color=ft.colors.RED, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        "Este software é para estudo estatístico apenas. Loterias são "
                                        "jogos de azar e não há padrões que garantam vitórias. "
                                        "Jogue com responsabilidade e moderação.",
                                        size=14,
                                        color=ft.colors.BLUE_GREY,
                                    ),
                                ]),
                                padding=ft.padding.all(15),
                                bgcolor=ft.colors.RED_50,
                                border_radius=ft.border_radius.all(10),
                            ),
                        ]),
                        padding=ft.padding.all(20),
                    )
                ),
            ])
        )
    
    def show_user_manual(self, e):
        """Mostra manual do usuário completo e atualizado"""
        self.clear_results()
        
        manual_content = ft.Column([
            ft.Text("📚 Manual do Usuário Completo - DeuSorte", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20),
            
            # Índice
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📋 Sumário", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "1. 🎯 Visão Geral\n"
                            "2. ✨ Funcionalidades\n"
                            "3. 🚀 Primeiros Passos\n"
                            "4. 🎯 Estratégias de Sugestões\n"
                            "5. 📊 Interpretando Resultados\n"
                            "6. ⚙️ Instalação\n"
                            "7. ❓ FAQ Completo\n"
                            "8. 📄 Licenças\n"
                            "9. 🤝 Contribuição",
                            size=14,
                            selectable=True,
                        ),
                    ]),
                    padding=ft.padding.all(20),
                ),
                elevation=3,
            ),
            
            ft.Divider(height=30),
            
            # 1. Visão Geral
            ft.Container(
                content=ft.Column([
                    ft.Text("🎯 Visão Geral", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                    ft.Text(
                        "DeuSorte é um aplicativo desktop para análise estatística avançada "
                        "dos resultados históricos das loterias da Caixa Econômica Federal.\n",
                        size=14,
                    ),
                    ft.Text("🎰 Loterias Suportadas:", size=14, weight=ft.FontWeight.BOLD),
                ]),
                padding=ft.padding.only(bottom=10),
            ),
            
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Loteria")),
                    ft.DataColumn(ft.Text("Números")),
                    ft.DataColumn(ft.Text("Sorteios")),
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Mega-Sena", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("60")),
                        ft.DataCell(ft.Text("Qua/Sáb")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Lotofácil", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("25")),
                        ft.DataCell(ft.Text("Seg/Qua/Sex")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Quina", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("80")),
                        ft.DataCell(ft.Text("Seg-Sáb")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Lotomania", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("100")),
                        ft.DataCell(ft.Text("Ter/Sex")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Dupla Sena", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("50")),
                        ft.DataCell(ft.Text("Ter/Qui/Sáb")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Dia de Sorte", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("31")),
                        ft.DataCell(ft.Text("Ter/Sex")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Timemania", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text("80")),
                        ft.DataCell(ft.Text("Ter/Qui/Sáb")),
                    ]),
                ],
            ),
            
            ft.Divider(height=30),
            
            # 2. Funcionalidades Expandidas
            ft.Text("✨ Funcionalidades Principais", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
            
            ft.Column([
                ft.ListTile(
                    leading=ft.Icon(ft.icons.ANALYTICS, color=ft.colors.BLUE),
                    title=ft.Text("📊 Análise Estatística Avançada"),
                    subtitle=ft.Column([
                        ft.Text("• Frequência de números e estatísticas básicas", size=12),
                        ft.Text("• Identificação de padrões (pares/ímpares, altos/baixos)", size=12),
                        ft.Text("• Análise de atrasos e números 'frios'", size=12),
                        ft.Text("• Distribuição por faixas e dígitos finais", size=12),
                    ]),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.CALENDAR_MONTH, color=ft.colors.GREEN),
                    title=ft.Text("🕰️ Análise por Períodos Flexíveis"),
                    subtitle=ft.Column([
                        ft.Text("• 1 ano (~100-150 concursos)", size=12),
                        ft.Text("• 2 anos (~200-300 concursos)", size=12),
                        ft.Text("• 3 anos RECOMENDADO (~300-450 concursos)", size=12),
                        ft.Text("• 5 anos (~500-750 concursos)", size=12),
                        ft.Text("• Período personalizado", size=12),
                    ]),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.STORAGE, color=ft.colors.ORANGE),
                    title=ft.Text("🔄 Sistema de Cache Inteligente"),
                    subtitle=ft.Column([
                        ft.Text("• Armazenamento local SQLite para uso offline", size=12),
                        ft.Text("• Atualização incremental (apenas novos concursos)", size=12),
                        ft.Text("• Validação automática de dados", size=12),
                        ft.Text("• Limpeza seletiva por loteria", size=12),
                    ]),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.AUTO_AWESOME, color=ft.colors.PURPLE),
                    title=ft.Text("🎯 Geração de Sugestões Multi-Estratégia"),
                    subtitle=ft.Column([
                        ft.Text("• Estratégia Balanceada (recomendada)", size=12),
                        ft.Text("• Números Quentes (frequentes)", size=12),
                        ft.Text("• Números Frios (atrasados)", size=12),
                        ft.Text("• Mista (combinação)", size=12),
                        ft.Text("• Estatística Pura (matemática)", size=12),
                    ]),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.COMPARE_ARROWS, color=ft.colors.RED),
                    title=ft.Text("📈 Comparação entre Loterias"),
                    subtitle=ft.Column([
                        ft.Text("• Tabelas comparativas lado a lado", size=12),
                        ft.Text("• Visualizações gráficas de frequência", size=12),
                        ft.Text("• Exportação de dados em JSON", size=12),
                        ft.Text("• Análise de características únicas", size=12),
                    ]),
                ),
            ]),
            
            ft.Divider(height=30),
            
            # 3. Guia Rápido de Uso (Expandido)
            ft.Text("🚀 Guia Rápido de Uso - Passo a Passo", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE),
            
            # Passo 1
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text("1", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                width=30,
                                height=30,
                                bgcolor=ft.colors.BLUE,
                                border_radius=ft.border_radius.all(15),
                                alignment=ft.alignment.center,
                            ),
                            ft.Text("Escolha o Tipo de Análise", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text("📍 No menu lateral, selecione:", size=14),
                        ft.Column([
                            ft.Text("• 'Análise por Anos' → Personalizada por período", size=13),
                            ft.Text("• 'Análise Rápida' → Padrão de 3 anos", size=13),
                            ft.Text("• 'Comparar Loterias' → Análise comparativa", size=13),
                            ft.Text("• 'Gerar Sugestões' → Após análise prévia", size=13),
                        ]),
                        ft.Container(
                            content=ft.Text("💡 Dica: Comece com 'Análise Rápida' para familiarização", 
                                        size=12, color=ft.colors.BLUE, italic=True),
                            padding=ft.padding.only(top=10),
                        ),
                    ]),
                    padding=ft.padding.all(15),
                )
            ),
            
            ft.Divider(height=10),
            
            # Passo 2
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text("2", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                width=30,
                                height=30,
                                bgcolor=ft.colors.GREEN,
                                border_radius=ft.border_radius.all(15),
                                alignment=ft.alignment.center,
                            ),
                            ft.Text("Selecione a Loteria", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text("🎰 Escolha entre 7 loterias disponíveis:\n", size=14),
                        ft.Column([
                            ft.Text("Mega-Sena: 60 números, sorteios às quartas e sábados", size=13),
                            ft.Text("Lotofácil: 25 números, sorteios às segundas, quartas e sextas", size=13),
                            ft.Text("Quina: 80 números, sorteios de segunda a sábado", size=13),
                            ft.Text("Lotomania: 100 números (0-99), sorteios às terças e sextas", size=13),
                            ft.Text("Dupla Sena: 50 números, sorteios às terças, quintas e sábados", size=13),
                            ft.Text("Dia de Sorte: 31 números, sorteios às terças e sextas", size=13),
                            ft.Text("Timemania: 80 números, sorteios às terças, quintas e sábados", size=13),
                        ]),
                    ]),
                    padding=ft.padding.all(15),
                )
            ),
            
            ft.Divider(height=10),
            
            # Passo 3 (Atualizado com mais detalhes)
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text("3", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                width=30,
                                height=30,
                                bgcolor=ft.colors.ORANGE,
                                border_radius=ft.border_radius.all(15),
                                alignment=ft.alignment.center,
                            ),
                            ft.Text("Configure o Período de Análise", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text("📅 Recomendações por tipo de análise:\n", size=14),
                        ft.Column([
                            ft.Text("• Análise inicial: 1 ano (100-150 concursos)", size=13),
                            ft.Text("• Análise média: 2 anos (200-300 concursos)", size=13),
                            ft.Text("• Análise abrangente: 3 anos ⭐ RECOMENDADO", size=13, weight=ft.FontWeight.BOLD),
                            ft.Text("• Análise histórica: 5 anos (500-750 concursos)", size=13),
                        ]),
                        ft.Text("\n📊 Quantidade aproximada de concursos por loteria:", size=14),
                        ft.Column([
                            ft.Text("• Mega-Sena/Lotomania: ~100/ano", size=13),
                            ft.Text("• Lotofácil/Quina: ~150/ano", size=13),
                            ft.Text("• Demais: ~150-200/ano", size=13),
                        ]),
                    ]),
                    padding=ft.padding.all(15),
                )
            ),
            
            ft.Divider(height=10),
            
            # Passo 4 (Atualizado com tempo estimado)
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text("4", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                width=30,
                                height=30,
                                bgcolor=ft.colors.PURPLE,
                                border_radius=ft.border_radius.all(15),
                                alignment=ft.alignment.center,
                            ),
                            ft.Text("Aguarde a Análise", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text("⏱️ Tempos estimados:\n", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("1. 🔍 Busca de dados (primeira vez): 2-3 minutos", size=13),
                        ft.Text("   - Baixa dados da API da Caixa", size=12),
                        ft.Text("   - Armazena em cache local", size=12),
                        ft.Text("\n2. 📊 Processamento estatístico: 10-30 segundos", size=13),
                        ft.Text("   - Calcula frequências", size=12),
                        ft.Text("   - Identifica padrões", size=12),
                        ft.Text("   - Gera estatísticas", size=12),
                        ft.Text("\n3. 💾 Próximas análises: 10-20 segundos", size=13),
                        ft.Text("   - Usa cache local", size=12),
                        ft.Text("   - Verifica apenas atualizações", size=12),
                    ]),
                    padding=ft.padding.all(15),
                )
            ),
            
            ft.Divider(height=10),
            
            # Passo 5 (Expandido com mais informações)
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text("5", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                width=30,
                                height=30,
                                bgcolor=ft.colors.RED,
                                border_radius=ft.border_radius.all(15),
                                alignment=ft.alignment.center,
                            ),
                            ft.Text("Explore os Resultados", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text("📈 O que você verá:\n", size=14, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text("• Números quentes: Mais frequentes (com %)", size=13),
                            ft.Text("• Números frios: Mais atrasados (dias sem sair)", size=13),
                            ft.Text("• Balanceamento: Pares/ímpares, altos/baixos", size=13),
                            ft.Text("• Estatísticas: Médias, desvios, somas ideais", size=13),
                            ft.Text("• Sugestões: Combinações por estratégia", size=13),
                        ]),
                        ft.Text("\n🔄 Ações disponíveis:", size=14, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text("• Copiar resultados", size=13),
                            ft.Text("• Gerar relatório completo", size=13),
                            ft.Text("• Gerar novas sugestões", size=13),
                            ft.Text("• Comparar com outras loterias", size=13),
                        ]),
                    ]),
                    padding=ft.padding.all(15),
                )
            ),
            
            ft.Divider(height=30),
            
            # 4. Estratégias de Sugestões (Expandido)
            ft.Text("🎯 Estratégias de Sugestões Detalhadas", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE),

            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Estratégia")),
                    ft.DataColumn(ft.Text("Como Funciona")),
                    ft.DataColumn(ft.Text("Quando Usar")),
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("🎯 Balanceada", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE)),
                        ft.DataCell(ft.Text(
                            "• Combina múltiplos critérios\n"
                            "• Proporção ideal pares/ímpares\n"
                            "• Distribuição altos/baixos\n"
                            "• Soma na faixa estatística",
                            size=11,
                        )),
                        ft.DataCell(ft.Text(
                            "✅ Uso geral\n"
                            "✅ Análises iniciais\n"
                            "✅ Maior equilíbrio",
                            size=11,
                            color=ft.colors.GREEN,
                        )),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("🔥 Números Quentes", weight=ft.FontWeight.BOLD, color=ft.colors.RED)),
                        ft.DataCell(ft.Text(
                            "• Foca números mais frequentes\n"
                            "• Baseado em tendências recentes\n"
                            "• Prioriza repetição histórica",
                            size=11,
                        )),
                        ft.DataCell(ft.Text(
                            "✅ Sequências positivas\n"
                            "✅ Números em tendência\n"
                            "✅ Manter 'momentum'",
                            size=11,
                            color=ft.colors.GREEN,
                        )),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("❄️ Números Frios", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE)),
                        ft.DataCell(ft.Text(
                            "• Foca números mais atrasados\n"
                            "• Baseado na 'lei dos atrasos'\n"
                            "• Probabilidade teórica aumentada",
                            size=11,
                        )),
                        ft.DataCell(ft.Text(
                            "✅ Quebrar sequências\n"
                            "✅ Atrasos prolongados\n"
                            "✅ Diversificação",
                            size=11,
                            color=ft.colors.GREEN,
                        )),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("🔄 Mista", weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE)),
                        ft.DataCell(ft.Text(
                            "• Combina quentes e frios\n"
                            "• Adiciona aleatoriedade\n"
                            "• Diversificação estratégica\n"
                            "• 30% quentes + 30% frios + 40% aleatórios",
                            size=11,
                        )),
                        ft.DataCell(ft.Text(
                            "✅ Diversificar\n"
                            "✅ Abordagem conservadora\n"
                            "✅ Cobertura ampla",
                            size=11,
                            color=ft.colors.GREEN,
                        )),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("📊 Estatística", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)),
                        ft.DataCell(ft.Text(
                            "• Base puramente matemática\n"
                            "• Distribuição estatística ideal\n"
                            "• Otimização matemática\n"
                            "• Modelo probabilístico",
                            size=11,
                        )),
                        ft.DataCell(ft.Text(
                            "✅ Usuários avançados\n"
                            "✅ Preferência matemática\n"
                            "✅ Análise acadêmica",
                            size=11,
                            color=ft.colors.GREEN,
                        )),
                    ]),
                ],
            ),
            
            ft.Divider(height=30),
            
            # 5. Instalação e Configuração (NOVA SEÇÃO)
            ft.Text("⚙️ Instalação e Configuração", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.TEAL),
            
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📦 Pré-requisitos", size=16, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text("• Python 3.8 ou superior", size=14),
                            ft.Text("• Conexão com internet (primeira execução)", size=14),
                            ft.Text("• 100MB espaço em disco", size=14),
                            ft.Text("• 4GB RAM recomendado", size=14),
                        ]),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("🚀 Instalação Rápida", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(
                                "# Clone o repositório\ngit clone https://github.com/jcgomes/DeuSorte.git\ncd DeuSorte\n\n"
                                "# Instale dependências\npip install -r requirements.txt\n\n"
                                "# Execute o aplicativo\npython main.py",
                                size=12,
                                font_family="monospace",
                                selectable=True,
                            ),
                            padding=ft.padding.all(10),
                            border=ft.border.all(1, ft.colors.GREY_300),
                            border_radius=ft.border_radius.all(5),
                            bgcolor=ft.colors.BLACK12,
                        ),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("📁 requirements.txt", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(
                                "flet>=0.24.0\nrequests>=2.31.0\npandas>=2.1.0\nnumpy>=1.24.0",
                                size=12,
                                font_family="monospace",
                                selectable=True,
                            ),
                            padding=ft.padding.all(10),
                            border=ft.border.all(1, ft.colors.GREY_300),
                            border_radius=ft.border_radius.all(5),
                            bgcolor=ft.colors.BLACK12,
                        ),
                    ]),
                    padding=ft.padding.all(20),
                )
            ),
            
            ft.Divider(height=30),
            
            # 6. FAQ Expandido (NOVA SEÇÃO)
            ft.Text("❓ FAQ - Perguntas Frequentes Expandido", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO),
            
            # FAQ 1
            ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text("Como funciona a atualização de dados?", 
                                    weight=ft.FontWeight.BOLD),
                        trailing=ft.Icon(ft.icons.ADD),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📊 Sistema de Cache Inteligente:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Column([
                                ft.Text("• Primeira execução: Baixa TODOS os concursos do período", size=12),
                                ft.Text("• Execuções subsequentes: Verifica apenas NOVOS concursos", size=12),
                                ft.Text("• Dados armazenados em SQLite local", size=12),
                                ft.Text("• Atualização forçada: Exclua lottery_cache.db", size=12),
                                ft.Text("", size=12),
                                ft.Text("💾 Tamanho do cache:", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text("• Por loteria: ~1-2MB por ano", size=12),
                                ft.Text("• Total (todas loterias 5 anos): ~10-20MB", size=12),
                            ]),
                        ]),
                        padding=ft.padding.only(left=16, right=16, bottom=16),
                        visible=False,
                    ),
                ]),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(5),
                padding=ft.padding.all(5),
                on_click=lambda e: self.toggle_faq(e, 0),
            ),
            
            ft.Divider(height=10),
            
            # FAQ 2
            ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text("Posso usar o aplicativo offline?", 
                                    weight=ft.FontWeight.BOLD),
                        trailing=ft.Icon(ft.icons.ADD),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📡 Modos de Operação:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Column([
                                ft.Text("✅ Totalmente offline APÓS primeira análise:", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text("   • Análises estatísticas", size=12),
                                ft.Text("   • Geração de sugestões", size=12),
                                ft.Text("   • Relatórios completos", size=12),
                                ft.Text("   • Exportação de dados", size=12),
                                ft.Text("", size=12),
                                ft.Text("🌐 Requer internet PARA:", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text("   • Primeira análise de cada período/loteria", size=12),
                                ft.Text("   • Busca de concursos novos", size=12),
                                ft.Text("   • Atualizações de cache", size=12),
                                ft.Text("", size=12),
                                ft.Text("💡 Dica: Faça uma análise completa uma vez, depois use offline!", size=12, color=ft.colors.BLUE, italic=True),
                            ]),
                        ]),
                        padding=ft.padding.only(left=16, right=16, bottom=16),
                        visible=False,
                    ),
                ]),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(5),
                padding=ft.padding.all(5),
                on_click=lambda e: self.toggle_faq(e, 1),
            ),
            
            ft.Divider(height=10),
            
            # FAQ 3
            ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text("Os dados são confiáveis e atualizados?", 
                                    weight=ft.FontWeight.BOLD),
                        trailing=ft.Icon(ft.icons.ADD),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🔐 Fontes e Validação:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Column([
                                ft.Text("✅ Fonte oficial: API da Caixa Econômica Federal", size=12, color=ft.colors.GREEN),
                                ft.Text("✅ Validação: Verificação de integridade automática", size=12, color=ft.colors.GREEN),
                                ft.Text("✅ Backup: Sistema de fallback com dados de exemplo", size=12, color=ft.colors.GREEN),
                                ft.Text("✅ Atualização: Verificação automática de novos concursos", size=12, color=ft.colors.GREEN),
                                ft.Text("", size=12),
                                ft.Text("🔄 Frequência de atualização:", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text("• Concurso novo: Disponível em até 2 horas", size=12),
                                ft.Text("• Verificação automática: A cada execução", size=12),
                                ft.Text("• Cache: Mantido por 24 horas (atualizável)", size=12),
                                ft.Text("", size=12),
                                ft.Text("⚠️ Se API falhar: Usa dados de exemplo para demonstração", size=12, color=ft.colors.ORANGE),
                            ]),
                        ]),
                        padding=ft.padding.only(left=16, right=16, bottom=16),
                        visible=False,
                    ),
                ]),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(5),
                padding=ft.padding.all(5),
                on_click=lambda e: self.toggle_faq(e, 2),
            ),
            
            ft.Divider(height=10),
            
            # FAQ 4
            ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text("Posso exportar os resultados?", 
                                    weight=ft.FontWeight.BOLD),
                        trailing=ft.Icon(ft.icons.ADD),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📤 Opções de Exportação:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Column([
                                ft.Text("✅ Copiar para área de transferência:", size=12, color=ft.colors.GREEN),
                                ft.Text("   • Relatórios completos", size=12),
                                ft.Text("   • Tabelas de resultados", size=12),
                                ft.Text("   • Sugestões de combinações", size=12),
                                ft.Text("", size=12),
                                ft.Text("✅ Exportação estruturada (JSON):", size=12, color=ft.colors.GREEN),
                                ft.Text("   • Dados de comparação entre loterias", size=12),
                                ft.Text("   • Estatísticas completas", size=12),
                                ft.Text("   • Padrões identificados", size=12),
                                ft.Text("", size=12),
                                ft.Text("💡 Formatos futuros planejados:", size=12, color=ft.colors.BLUE),
                                ft.Text("   • CSV/Excel", size=12),
                                ft.Text("   • PDF", size=12),
                                ft.Text("   • Imagens de gráficos", size=12),
                            ]),
                        ]),
                        padding=ft.padding.only(left=16, right=16, bottom=16),
                        visible=False,
                    ),
                ]),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(5),
                padding=ft.padding.all(5),
                on_click=lambda e: self.toggle_faq(e, 3),
            ),
            
            ft.Divider(height=10),
            
            # FAQ 5
            ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text("Qual é o aviso legal importante?", 
                                    weight=ft.FontWeight.BOLD),
                        trailing=ft.Icon(ft.icons.ADD),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("⚠️ AVISO LEGAL OBRIGATÓRIO:", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
                            ft.Column([
                                ft.Text("Este software é para ESTUDO ESTATÍSTICO APENAS.", size=12),
                                ft.Text("", size=12),
                                ft.Text("🚫 NÃO É:", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text("• Garantia de ganhos", size=12),
                                ft.Text("• Sistema infalível", size=12),
                                ft.Text("• Consultoria financeira", size=12),
                                ft.Text("• Promessa de lucro", size=12),
                                ft.Text("", size=12),
                                ft.Text("🎰 Loterias são jogos de azar regulamentados.", size=12),
                                ft.Text("", size=12),
                                ft.Text("✅ Use com:", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text("• Responsabilidade", size=12),
                                ft.Text("• Moderação", size=12),
                                ft.Text("• Respeito aos limites financeiros", size=12),
                                ft.Text("", size=12),
                                ft.Text("📞 Em caso de problemas com jogo:", size=12),
                                ft.Text("Ligue 153 (CVV) ou procure ajuda profissional.", size=12),
                            ]),
                        ]),
                        padding=ft.padding.only(left=16, right=16, bottom=16),
                        visible=False,
                    ),
                ]),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=ft.border_radius.all(5),
                padding=ft.padding.all(5),
                on_click=lambda e: self.toggle_faq(e, 4),
            ),
            
            ft.Divider(height=30),
            
            # 7. Licenças (NOVA SEÇÃO)
            ft.Text("📄 Informações sobre Licenças", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BROWN),
            
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🏷️ Licença deste Projeto", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.COPYRIGHT, size=20, color=ft.colors.BLUE),
                                    ft.Text("MIT License", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                                ]),
                                ft.Column([
                                    ft.Text("✅ Permissiva e amplamente aceita", size=14),
                                    ft.Text("✅ Pode usar, modificar, distribuir", size=14),
                                    ft.Text("✅ Requer apenas atribuição", size=14),
                                    ft.Text("✅ Amigável para uso comercial", size=14),
                                    ft.Text("", size=12),
                                    ft.Text("📋 Texto completo em: LICENSE", size=14),
                                ]),
                            ]),
                            padding=ft.padding.all(10),
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=ft.border_radius.all(5),
                        ),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("🔗 Repositório Oficial", size=16, weight=ft.FontWeight.BOLD),
                        ft.TextButton(
                            text="🌐 https://github.com/jcgomes/DeuSorte",
                            on_click=lambda e: self.page.launch_url("https://github.com/jcgomes/DeuSorte"),
                            style=ft.ButtonStyle(
                                color=ft.colors.BLUE,
                            ),
                        ),
                    ]),
                    padding=ft.padding.all(20),
                )
            ),
            
            ft.Divider(height=30),
            
            # 8. Botões de Ação (Atualizados)
            ft.Row([
                ft.ElevatedButton(
                    text="🏠 Voltar ao Início",
                    on_click=self.show_home,
                    icon=ft.icons.HOME,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE,
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    ),
                ),
                ft.ElevatedButton(
                    text="🚀 Começar Análise",
                    on_click=self.show_quick_analysis,
                    icon=ft.icons.PLAY_ARROW,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.GREEN,
                        color=ft.colors.WHITE,
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    ),
                ),
                ft.ElevatedButton(
                    text="📋 Copiar Manual",
                    on_click=lambda e: self.page.run_task(
                        self.copy_to_clipboard, 
                        "Manual completo disponível em: https://github.com/jcgomes/DeuSorte"
                    ),
                    icon=ft.icons.CONTENT_COPY,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.PURPLE,
                        color=ft.colors.WHITE,
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    ),
                ),
            ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Divider(height=30),
            
            # Rodapé
            ft.Container(
                content=ft.Column([
                    ft.Text("📅 Última atualização: Fevereiro 2024", size=12, color=ft.colors.BLUE_GREY),
                    ft.Text("🐍 Python 3.8+ | 📱 Interface: Flet", size=12, color=ft.colors.BLUE_GREY),
                    ft.Text("👨‍💻 Desenvolvedor: Juliano Gomes", size=12, color=ft.colors.BLUE_GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(10),
            ),
        ], scroll=ft.ScrollMode.AUTO)
        
        self.add_result(manual_content) 

    def toggle_faq(self, e, faq_index):
        """Alterna a visibilidade da resposta da FAQ"""
        # Encontra o container clicado
        container = e.control
        
        # Encontra os controles dentro do container
        for control in container.content.controls:
            if isinstance(control, ft.Container):
                # Alterna a visibilidade da resposta
                control.visible = not control.visible
                
                # Atualiza o ícone
                for other_control in container.content.controls:
                    if isinstance(other_control, ft.ListTile):
                        # Muda o ícone de + para - ou vice-versa
                        if control.visible:
                            other_control.trailing = ft.Icon(ft.icons.REMOVE, color=ft.colors.BLUE)
                        else:
                            other_control.trailing = ft.Icon(ft.icons.ADD, color=ft.colors.BLUE)
                        break
        
        # Atualiza a página
        self.page.update() 

def main(page: ft.Page):
    """Função principal do aplicativo Flet"""
    page.window_maximized = True
    app = LotteryAnalyzerApp(page)

# Executar aplicativo
if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        assets_dir="assets",
    )