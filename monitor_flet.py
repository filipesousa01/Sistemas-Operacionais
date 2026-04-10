import flet as ft
import psutil
import threading
import time

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

# Primeira parte importando as bibliotecas e utilizando flet, um Framework do python para interfaces graficas melhores 

def format_bytes(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024: return f"{n:.2f} {unit}"
        n /= 1024
# Uma funçao para converter os Bytes em forma legivel 

class SystemMonitorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Relatorio do PC"
        self.page.theme_mode = ft.ThemeMode.DARK # tema
        self.page.padding = 30
        self.page.window_width = 1100
        self.page.window_height = 900
    
        
        # Monitoramento da CPU
        self.cpu_percent = ft.Text("0%", size=35, weight="bold", text_align=ft.TextAlign.CENTER)
        self.cpu_bar = ft.ProgressBar(value=0, color=ft.Colors.CYAN_400, height=10)
        self.cpu_cores = ft.Text("Núcleos: -", color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        
        # Monitoramento da memoria ram 
        self.ram_percent = ft.Text("0%", size=35, weight="bold", text_align=ft.TextAlign.CENTER)
        self.ram_bar = ft.ProgressBar(value=0, color=ft.Colors.GREEN_400, height=10)
        self.ram_details = ft.Text("Uso: - / -", color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)

        # Monitoramento da GPU 
        self.gpu_title = ft.Text("", size=14, color=ft.Colors.ORANGE_200, text_align=ft.TextAlign.CENTER) # Nome da placa
        self.gpu_percent = ft.Text("0%", size=35, weight="bold", text_align=ft.TextAlign.CENTER)
        self.gpu_bar = ft.ProgressBar(value=0, color=ft.Colors.ORANGE_400, height=10)
        self.gpu_vram = ft.Text("VRAM: - / -", color=ft.Colors.GREY_400)
        self.gpu_temp = ft.Text("Temp: - °C", color=ft.Colors.WHITE70)
        
        # bateria e disco
        self.battery_info = ft.Text("Bateria: Carregando...")
        self.disk_info = ft.Text("Disco: -")
        
        # Tabela de Processos
        self.process_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("PID", weight="bold")),
                ft.DataColumn(ft.Text("Nome do Processo", weight="bold")),
                ft.DataColumn(ft.Text("Memória (RAM)", weight="bold")),
            ],
            rows=[]
        )

        self.setup_ui()
        
        self.running = True
        
        # Thread 1: Atualiza a cpu/ram/gpu a cada 1 segundo 
        threading.Thread(target=self.update_fast_metrics, daemon=True).start()
        
        # Thread 2: Lenta pois atualiza processos e dicos a 4 segundos 
        threading.Thread(target=self.update_slow_metrics, daemon=True).start()

    def setup_ui(self):
        dashboard = ft.Column([
            ft.Text("Monitoramento do PC", size=28, weight="bold", color=ft.Colors.WHITE),
            
            ft.Divider(color=ft.Colors.WHITE24),
            
            ft.Row([
                # --- CARD CPU ---
                ft.Container(
                    content=ft.Column([
                        ft.Text(" CPU EM USO", size=16, weight="bold", color=ft.Colors.CYAN_400, text_align=ft.TextAlign.CENTER),
                        self.cpu_percent,
                        self.cpu_bar,
                        self.cpu_cores,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), # Centraliza todos os itens na coluna
                    padding=25, border_radius=15, bgcolor=ft.Colors.GREY_900, expand=True
                ),
                
                # --- CARD RAM ---
                ft.Container(
                    content=ft.Column([
                        ft.Text("MEMÓRIA RAM", size=16, weight="bold", color=ft.Colors.GREEN_400, text_align=ft.TextAlign.CENTER),
                        self.ram_percent,
                        self.ram_bar,
                        self.ram_details,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=25, border_radius=15, bgcolor=ft.Colors.GREY_900, expand=True
                ),
                
                # --- CARD GPU ---
                ft.Container(
                    content=ft.Column([
                        ft.Text(" PLACA DE VÍDEO", size=16, weight="bold", color=ft.Colors.ORANGE_400, text_align=ft.TextAlign.CENTER),
                        self.gpu_title, 
                        self.gpu_percent,
                        self.gpu_bar,
                        ft.Row([self.gpu_vram, self.gpu_temp], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=25, border_radius=15, bgcolor=ft.Colors.GREY_800, expand=True
                ),
            ], spacing=20),
            
            ft.Container(height=10),
            
            ft.Row([
                ft.Icon(ft.Icons.BATTERY_CHARGING_FULL, color=ft.Colors.GREEN_400),
                self.battery_info,
                ft.VerticalDivider(color=ft.Colors.WHITE24),
                ft.Icon(ft.Icons.STORAGE, color=ft.Colors.BLUE_400),
                self.disk_info
            ], alignment=ft.MainAxisAlignment.CENTER, height=40)
        ])
        
        # cria uma tabela com rolagem mostrando os processos 
        processes_section = ft.Column([
            ft.Container(height=10),
            ft.Text("10 Processos e Consumo de RAM", size=20, weight="bold", color=ft.Colors.BLUE_200),
            ft.Container(
                content=ft.Column([self.process_table], scroll=ft.ScrollMode.AUTO),
                height=300,
                border=ft.border.all(1, ft.Colors.WHITE24),
                border_radius=10,
                padding=10,
                bgcolor=ft.Colors.GREY_900
            )
        ])

        self.page.add(dashboard, processes_section)

    # metodo de atualizção rapida e mudança de cor caso a CPU/GPU esquente
    def update_fast_metrics(self):
        while self.running:
            try:
                cpu_p = psutil.cpu_percent(interval=None)
                self.cpu_percent.value = f"{cpu_p:.1f}%"
                self.cpu_bar.value = cpu_p / 100
                
                if cpu_p > 85:
                    self.cpu_bar.color = ft.Colors.RED_400
                    self.cpu_percent.color = ft.Colors.RED_400
                else:
                    self.cpu_bar.color = ft.Colors.CYAN_400
                    self.cpu_percent.color = ft.Colors.WHITE

                self.cpu_cores.value = f"Lógicos: {psutil.cpu_count()} | Físicos: {psutil.cpu_count(logical=False)}"

                mem = psutil.virtual_memory()
                self.ram_percent.value = f"{mem.percent}%"
                self.ram_bar.value = mem.percent / 100
                self.ram_details.value = f"{format_bytes(mem.used)} / {format_bytes(mem.total)}"

                if HAS_GPUTIL:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]
                        self.gpu_title.value = f"{gpu.name}"
                        self.gpu_percent.value = f"{int(gpu.load * 100)}%"
                        self.gpu_bar.value = gpu.load
                        self.gpu_vram.value = f"VRAM: {gpu.memoryUsed:.0f}MB"
                        self.gpu_temp.value = f"{gpu.temperature}°C"
                        
                        if gpu.temperature > 80:
                            self.gpu_temp.color = ft.Colors.RED_400
                        else:
                            self.gpu_temp.color = ft.Colors.WHITE70

                self.page.update()
                time.sleep(1) # Rápido!
            except Exception as e:
                time.sleep(1)

    def update_slow_metrics(self):
        while self.running:
            try:
                # Bateria
                bat = psutil.sensors_battery()
                if bat:
                    self.battery_info.value = f"{bat.percent}% ({'Ligado' if bat.power_plugged else 'Bateria'})"
                
                # Disco
                disk = psutil.disk_usage('/')
                self.disk_info.value = f"Raiz: {disk.percent}% usado ({format_bytes(disk.total)})"

                procs = []
                for p in sorted(psutil.process_iter(['pid', 'name', 'memory_info']), 
                               key=lambda x: x.info['memory_info'].rss, reverse=True)[:10]:
                    procs.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(p.info['pid']), color=ft.Colors.CYAN_200)),
                            ft.DataCell(ft.Text(p.info['name'])),
                            ft.DataCell(ft.Text(format_bytes(p.info['memory_info'].rss), weight="bold")),
                        ])
                    )
                self.process_table.rows = procs

                self.page.update()
                time.sleep(4) 
            except Exception as e:
                time.sleep(4)

def main(page: ft.Page):
    SystemMonitorApp(page)

ft.run(main)