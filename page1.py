import mysql.connector
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

# Configuração do console do Rich
console = Console()

# Conexão com o banco de dados
con = mysql.connector.connect(
    host="localhost",
    user="root",
    password="0",
    database="python"
)
cur = con.cursor()

# Criação das tabelas (caso ainda não existam)
cur.execute("""
CREATE TABLE IF NOT EXISTS candidatos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    numero INT UNIQUE NOT NULL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS votos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidato_id INT,
    tipo_voto ENUM('VÁLIDO', 'BRANCO', 'NULO') NOT NULL,
    FOREIGN KEY (candidato_id) REFERENCES candidatos(id)
)
""")

# Função pra imprimir cabeçalhos
def print_header(titulo):
    console.print(Panel(f"[bold cyan]{titulo}[/bold cyan]", expand=True))

# Listar os candidatos (concorrendo)
def listar_candidatos():
    print_header("Candidatos Registrados")
    cur.execute("SELECT nome, numero FROM candidatos ORDER BY numero")
    candidatos = cur.fetchall()
    if candidatos:
        # Montar uma tabela visual com os dados
        tabela = Table(title="Candidatos", title_style="bold green")
        tabela.add_column("Número", style="cyan", justify="center")
        tabela.add_column("Nome", style="white", justify="left")
        for nome, numero in candidatos:
            tabela.add_row(str(numero), nome)
        console.print(tabela)
    else:
        console.print("[bold red]Nenhum candidato registrado ainda... bora registrar uns?[/bold red]")

# Função pra gerenciar os candidatos (quem entra, sai ou muda de nome)
def gerenciar_candidatos():
    while True:
        print_header("Gerenciar Candidatos")
        console.print("[cyan]1.[/] Adicionar candidato")
        console.print("[cyan]2.[/] Atualizar candidato")
        console.print("[cyan]3.[/] Remover candidato")
        console.print("[cyan]4.[/] Listar candidatos")
        console.print("[cyan]5.[/] Voltar")
        escolha = Prompt.ask("[bold green]O que você quer fazer?[/bold green]")

        if escolha == "1":
            nome = Prompt.ask("[bold yellow]Nome do candidato[/bold yellow]")
            numero = Prompt.ask("[bold yellow]Número do candidato[/bold yellow]")
            try:
                cur.execute("INSERT INTO candidatos (nome, numero) VALUES (%s, %s)", (nome, numero))
                con.commit()
                console.print(f"[green]Candidato '{nome}' adicionado com sucesso![/green]")
            except mysql.connector.Error as e:
                console.print(f"[red]Deu ruim: {e}[/red]")
        elif escolha == "2":
            listar_candidatos()
            numero = Prompt.ask("[bold yellow]Número do candidato pra atualizar[/bold yellow]")
            novo_nome = Prompt.ask("[bold yellow]Novo nome do candidato[/bold yellow]")
            cur.execute("UPDATE candidatos SET nome = %s WHERE numero = %s", (novo_nome, numero))
            con.commit()
            console.print("[green]Atualizado! Esse nome novo tá bonito, hein![/green]")
        elif escolha == "3":
            listar_candidatos()
            numero = Prompt.ask("[bold yellow]Número do candidato pra remover[/bold yellow]")
            cur.execute("DELETE FROM candidatos WHERE numero = %s", (numero,))
            con.commit()
            console.print("[green]Removido com sucesso. Adeus, candidato![/green]")
        elif escolha == "4":
            listar_candidatos()
        elif escolha == "5":
            break
        else:
            console.print("[red]Essa opção não existe, tenta de novo![/red]")

# Função de votação
def votar():
    print_header("Votação")
    listar_candidatos()
    console.print("[cyan]Digite [bold]0[/bold] pra votar BRANCO[/cyan]")
    numero = Prompt.ask("[bold yellow]Número do candidato[/bold yellow]")

    if numero == "0":
        cur.execute("INSERT INTO votos (tipo_voto) VALUES ('BRANCO')")
        con.commit()
        console.print("[green]Voto em branco registrado. Cada voto conta, mesmo branco![/green]")
    else:
        cur.execute("SELECT id, nome FROM candidatos WHERE numero = %s", (numero,))
        candidato = cur.fetchone()
        if candidato:
            confirmacao = Prompt.ask(f"[bold yellow]Confirma seu voto no candidato '{candidato[1]}'? (s/n)[/bold yellow]", choices=["s", "n"])
            if confirmacao == "s":
                cur.execute("INSERT INTO votos (candidato_id, tipo_voto) VALUES (%s, 'VÁLIDO')", (candidato[0],))
                con.commit()
                console.print("[green]Voto computado com sucesso![/green]")
            else:
                console.print("[red]Voto não registrado. Tá tudo bem mudar de ideia![/red]")
        else:
            console.print("[red]Número inválido. Foi computado como voto NULO![/red]")
            cur.execute("INSERT INTO votos (tipo_voto) VALUES ('NULO')")
            con.commit()

# Função pra apurar os votos
def apurar_votos():
    print_header("Resultados da Votação")
    cur.execute("""
    SELECT c.nome, COUNT(v.id) AS total_votos
    FROM votos v
    LEFT JOIN candidatos c ON v.candidato_id = c.id
    WHERE v.tipo_voto = 'VÁLIDO'
    GROUP BY c.nome
    ORDER BY total_votos DESC
    """)
    validos = cur.fetchall()

    console.print("[bold cyan]Votos Válidos:[/bold cyan]")
    if validos:
        for nome, total_votos in validos:
            console.print(f"[green]{nome}[/green]: [bold]{total_votos}[/bold] voto(s)")
    else:
        console.print("[red]Ninguém votou em ninguém. Que triste![/red]")

    cur.execute("SELECT COUNT(id) FROM votos WHERE tipo_voto = 'BRANCO'")
    brancos = cur.fetchone()[0]
    console.print(f"[cyan]Votos em Branco:[/cyan] [bold]{brancos}[/bold]")

    cur.execute("SELECT COUNT(id) FROM votos WHERE tipo_voto = 'NULO'")
    nulos = cur.fetchone()[0]
    console.print(f"[cyan]Votos Nulos:[/cyan] [bold]{nulos}[/bold]")

# Menu principal
def menu():
    while True:
        print_header("Urna Eletrônica Brasileira")
        console.print("[cyan]1.[/] Votar")
        console.print("[cyan]2.[/] Apurar votos")
        console.print("[cyan]3.[/] Gerenciar candidatos")
        console.print("[cyan]4.[/] Sair")
        escolha = Prompt.ask("[bold green]Escolha uma opção[/bold green]")

        if escolha == "1":
            votar()
        elif escolha == "2":
            apurar_votos()
        elif escolha == "3":
            gerenciar_candidatos()
        elif escolha == "4":
            console.print("[bold red]Valeu! Até a próxima![/bold red]")
            break
        else:
            console.print("[red]Opção inválida! Tenta aí de novo![/red]")

# Bora rodar
menu()

# Fecha tudo
cur.close()
con.close()
