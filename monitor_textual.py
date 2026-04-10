import psutil
from textual.app import App, ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Header, Footer, DataTable, Label, ProgressBar
from textual.color import Color

# Tenta importar GPUtil
try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

def formatar_bytes(tamanho):
    """Converte bytes para um formato legível (KB, MB, GB)."""
    for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
        if tamanho < 1024.0:
            return f"{tamanho:.2f} {unidade}"
        tamanho /= 1024.0

class MetricCard(Vertical):
    """Um componente customizado para exibir métricas (CPU, RAM, GPU)."""
    
    def __init__(self, title: str, id: str):
        super().__init__(id=id)
        self.title_text = title

    def compose(self) -> ComposeResult:
        yield Label(self.title_text, classes="card-title")
        yield Label("0%", id=f"{self.id}-value", classes="card-value")
        yield ProgressBar(total=100, show_eta=False, id=f"{self.id}-bar")
        yield Label("-", id=f"{self.id}-details", classes="card-details")

class SystemMonitorApp(App):
    
    
    TITLE = "Diagnóstico do Sistema "
    BINDINGS = [("q", "quit", "Sair do Monitor")]

    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #metrics-grid {
        layout: grid;
        grid-size: 3; /* 3 colunas */
        height: 12;
        padding: 1;
        grid-gutter: 1 2;
    }
    
    MetricCard {
        border: solid $accent;
        padding: 1;
        background: $panel;
    }
    
    .card-title {
        text-style: bold;
        width: 100%;
        content-align: center middle;
    }
    
    .card-value {
        text-style: bold;
        color: $success;
        width: 100%;
        content-align: center middle;
        padding-top: 1;
    }
    
    .card-details {
        color: $text-muted;
        width: 100%;
        content-align: center middle;
    }

    #bottom-section {
        padding: 0 1;
        height: 1fr;
    }

    #info-bar {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $warning;
    }
    """

    def compose(self) -> ComposeResult:
        """Monta a interface de usuário."""
        yield Header(show_clock=True)
        
        # Grid superior com os 3 cards
        yield Grid(
            MetricCard(" Uso de CPU", id="cpu"),
            MetricCard(" Memória RAM", id="ram"),
            MetricCard(" Placa de Vídeo", id="gpu"),
            id="metrics-grid"
        )
        
        # Tabela e Informações na parte inferior
        with Vertical(id="bottom-section"):
            yield Label("Bateria: -- | Disco: --", id="info-bar")
            yield DataTable(id="process-table")
            
        yield Footer()

    def on_mount(self) -> None:
        """Roda assim que a tela é montada."""
        # Configura a tabela
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("PID", "Nome do Processo", "Memória (RAM)")

        # Configura as atualizações de tempo em tempo (como as Threads no Flet)
        self.set_interval(1.0, self.update_fast_metrics)
        self.set_interval(4.0, self.update_slow_metrics)

    def update_fast_metrics(self) -> None:
        """Atualiza CPU, RAM e GPU rapidamente."""
        # --- CPU ---
        cpu_p = psutil.cpu_percent(interval=None)
        self.query_one("#cpu-value", Label).update(f"{cpu_p:.1f}%")
        self.query_one("#cpu-bar", ProgressBar).progress = cpu_p
        self.query_one("#cpu-details", Label).update(f"Lógicos: {psutil.cpu_count()}")

        # --- RAM ---
        mem = psutil.virtual_memory()
        self.query_one("#ram-value", Label).update(f"{mem.percent}%")
        self.query_one("#ram-bar", ProgressBar).progress = mem.percent
        self.query_one("#ram-details", Label).update(f"{formatar_bytes(mem.used)} / {formatar_bytes(mem.total)}")

        # --- GPU ---
        if HAS_GPUTIL:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self.query_one("#gpu-value", Label).update(f"{int(gpu.load * 100)}%")
                self.query_one("#gpu-bar", ProgressBar).progress = gpu.load * 100
                self.query_one("#gpu-details", Label).update(f"{gpu.name} | {gpu.temperature}°C")
            else:
                self.query_one("#gpu-details", Label).update("Nenhuma GPU detectada")
        else:
            self.query_one("#gpu-details", Label).update("GPUtil ausente")

    def update_slow_metrics(self) -> None:
        """Atualiza Tabela e status de Energia/Disco sem travar a interface."""
        # --- Bateria e Disco ---
        bat = psutil.sensors_battery()
        bat_str = f"Bateria: {bat.percent}% {'(Ligado)' if bat.power_plugged else ''}" if bat else "Bateria: N/A"
        
        disco = psutil.disk_usage('/')
        disk_str = f"Disco Raiz: {disco.percent}% usado ({formatar_bytes(disco.total)})"
        
        self.query_one("#info-bar", Label).update(f" {bat_str}   |   {disk_str}")

        # --- Processos ---
        procs = []
        for p in sorted(psutil.process_iter(['pid', 'name', 'memory_info']), 
                        key=lambda x: x.info['memory_info'].rss if x.info['memory_info'] else 0, 
                        reverse=True)[:15]: # Pegando 15 processos
            
            # Formatando os dados para a tabela
            pid = str(p.info['pid'])
            nome = str(p.info['name'])
            memoria = formatar_bytes(p.info['memory_info'].rss) if p.info['memory_info'] else "0 B"
            procs.append((pid, nome, memoria))

    
        table = self.query_one(DataTable)
        table.clear()
        table.add_rows(procs)

if __name__ == "__main__":
    app = SystemMonitorApp()
    app.run()