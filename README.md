#  Monitor de Sistema e Diagnóstico (GUI vs TUI)

Um projeto desenvolvido em Python focado na coleta, análise e exibição de métricas do Sistema Operacional e Hardware em tempo real. 

Este repositório serve como um **Estudo de Caso Arquitetural**, apresentando a mesma regra de negócios (coleta de dados via `psutil`) aplicada em dois paradigmas de interface de usuário completamente diferentes: uma interface gráfica moderna (GUI) e uma interface de terminal avançada (TUI).

---

## 🎯 Objetivo do Projeto
O objetivo principal é demonstrar na prática os conceitos estudados em Sistemas Operacionais, observando como o SO gerencia o processador, a memória física, processos em execução, armazenamento e recursos de hardware (como a GPU).

## 🚀 As Duas Versões

### 1. Versão Flet (Interface Gráfica - GUI)
**Arquivo:** `monitor_flet.py`
Uma interface estilo "Dashboard" construída com o framework **Flet** (que utiliza o motor do Flutter por baixo dos panos). 
* **Características:** Design *Material 3*, barras de progresso suaves, alinhamento flexível e cores dinâmicas (ex: alertas em vermelho quando a CPU ou GPU esquentam muito).
* **Concorrência:** Utiliza a biblioteca nativa `threading` do Python para separar a interface gráfica do loop de coleta de dados.

### 2. Versão Textual (Interface de Terminal - TUI)
**Arquivo:** `monitor_textual.py`
Uma interface construída inteiramente no terminal utilizando o framework **Textual**. 
* **Características:** Estética "Hacker"/Sysadmin, extremamente leve, suporte a cliques do mouse direto no terminal e renderização via caracteres ANSI. 
* **Concorrência:** Utiliza o loop de eventos assíncrono nativo do framework (`set_interval`), dispensando a gestão manual de threads. O design é gerido de forma separada usando **TCSS** (Textual CSS).

---

## 📊 Funcionalidades Implementadas

Ambas as versões são capazes de monitorar em tempo real:
*** CPU:** Porcentagem de uso global, separação entre núcleos físicos e lógicos.
*** Memória RAM:** Capacidade total, memória em uso e porcentagem. Os dados são convertidos dinamicamente de Bytes para formatos legíveis (MB/GB).
*** GPU (Placa de Vídeo):** Leitura de VRAM, porcentagem de estresse do chip gráfico e temperatura (requer hardware compatível).
*** Energia e Disco:** Nível de bateria, status de conexão na tomada e uso da partição raiz (C: ou /).
*** Processos:** Uma tabela interativa (Top 10 ou Top 15) que lista os processos do sistema operacional ordenados por quem mais consome memória RAM no momento.

---

##  Solução de Arquitetura (Prevenção de Gargalos)

Ler dezenas de processos diretamente do Sistema Operacional é uma tarefa que exige muito do processador. Para evitar que a interface visual "engasgue" ou congele durante o uso, a arquitetura de atualização de dados foi separada em duas rotinas (Tempos de Tick):

1. **Ciclo Rápido (1 segundo):** Atualiza métricas leves (Uso numérico de CPU, RAM e GPU) para manter as barras de progresso fluidas e responsivas.
2. **Ciclo Lento (4 segundos):** Atualiza métricas pesadas (Varredura e ordenação de Processos, leitura de Disco). Isso dá "fôlego" para o processador e mantém o dashboard estável.

---

##  Como Executar o Projeto na sua Máquina

### Pré-requisitos
* Python 3.8 ou superior.
* É altamente recomendado o uso de um **Ambiente Virtual (`venv`)**.

### Passo a passo de Instalação

1. Clone este repositório:
   ```bash
   git clone [https://github.com/SEU-NOME-DE-USUARIO/monitor-sistema.git](https://github.com/SEU-NOME-DE-USUARIO/monitor-sistema.git)
   cd monitor-sistema