import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

# ============================================================
# JUH QUIZ — GAME SHOW
# 8 vídeos × 5 perguntas
# Fluxo:
# 1) narra SOMENTE a pergunta
# 2) inicia contagem de 3 segundos com bips
# 3) revela a alternativa correta
# 4) narra SOMENTE o texto da resposta correta
# ============================================================

QUANTIDADE_VIDEOS = 8
PERGUNTAS_POR_VIDEO = 5
TEMPO_ESCOLHA = 3

# Mesma voz e velocidade do outro gerador
VOZ = "pt-BR-AntonioNeural"
VELOCIDADE_VOZ = "+10%"

W = 1080
H = 1920
FPS = 30

AUDIO_HZ = 48000
AUDIO_CHANNELS = 2
PAUSA_DEPOIS_RESPOSTA = 0.55

FUSO = ZoneInfo("America/Fortaleza")
DATA_DO_DIA = datetime.now(FUSO).strftime("%Y-%m-%d")

PASTA_RAIZ = Path("output_game_show")
PASTA_TMP = Path("_tmp_juhquiz_game_show")
PASTA_SAIDA = PASTA_RAIZ / DATA_DO_DIA

# ============================================================
# 8 TEMAS × 5 PERGUNTAS NOVAS
# correta: 0=A, 1=B, 2=C
# As perguntas abaixo são diferentes das 40 usadas no gerador rosa.
# ============================================================

QUIZZES = {
    "Cinema e TV": [
        {"pergunta": "Em qual franquia de filmes aparece o personagem Jack Sparrow?", "alternativas": ["Piratas do Caribe", "Jurassic Park", "O Senhor dos Anéis"], "correta": 0},
        {"pergunta": "Qual é o nome do cowboy de brinquedo em Toy Story?", "alternativas": ["Buzz", "Woody", "Rex"], "correta": 1},
        {"pergunta": "Qual é a cor do personagem Shrek?", "alternativas": ["Azul", "Vermelho", "Verde"], "correta": 2},
        {"pergunta": "Qual é o nome da irmã de Elsa no filme Frozen?", "alternativas": ["Anna", "Ariel", "Moana"], "correta": 0},
        {"pergunta": "Qual super-herói tem Bruce Wayne como identidade secreta?", "alternativas": ["Superman", "Batman", "Thor"], "correta": 1},
    ],

    "Música": [
        {"pergunta": "Quantas cordas possui normalmente um violão tradicional?", "alternativas": ["4", "6", "8"], "correta": 1},
        {"pergunta": "Qual instrumento costuma ter 88 teclas?", "alternativas": ["Piano", "Violino", "Pandeiro"], "correta": 0},
        {"pergunta": "As escolas de samba desfilam principalmente em qual festa brasileira?", "alternativas": ["São João", "Carnaval", "Oktoberfest"], "correta": 1},
        {"pergunta": "O saxofone pertence principalmente a qual família de instrumentos?", "alternativas": ["Cordas", "Percussão", "Sopro"], "correta": 2},
        {"pergunta": "Na música, qual símbolo indica um período de silêncio?", "alternativas": ["Pausa", "Clave", "Compasso"], "correta": 0},
    ],

    "Esportes": [
        {"pergunta": "Quantos jogadores cada time inicia em campo em uma partida de futebol?", "alternativas": ["9", "11", "13"], "correta": 1},
        {"pergunta": "No basquete, quantos pontos vale uma cesta feita atrás da linha de três?", "alternativas": ["3", "2", "1"], "correta": 0},
        {"pergunta": "No vôlei, quantos toques uma equipe pode dar antes de enviar a bola ao outro lado?", "alternativas": ["2", "4", "3"], "correta": 2},
        {"pergunta": "No tênis, como é chamado o placar de quarenta a quarenta?", "alternativas": ["Tie-break", "Deuce", "Match point"], "correta": 1},
        {"pergunta": "Qual esporte olímpico usa florete, espada ou sabre?", "alternativas": ["Esgrima", "Judô", "Tiro com arco"], "correta": 0},
    ],

    "Gastronomia": [
        {"pergunta": "Qual é o principal ingrediente do guacamole?", "alternativas": ["Batata", "Abacate", "Tomate"], "correta": 1},
        {"pergunta": "O sushi é tradicionalmente associado à culinária de qual país?", "alternativas": ["Japão", "China", "Tailândia"], "correta": 0},
        {"pergunta": "Qual queijo é tradicionalmente usado na pizza margherita?", "alternativas": ["Cheddar", "Gorgonzola", "Muçarela"], "correta": 2},
        {"pergunta": "O cacau é a principal matéria-prima de qual alimento?", "alternativas": ["Chocolate", "Pão", "Queijo"], "correta": 0},
        {"pergunta": "Qual país é mais associado ao croissant na culinária atual?", "alternativas": ["México", "França", "Brasil"], "correta": 1},
    ],

    "Tecnologia": [
        {"pergunta": "Para que o GPS é usado principalmente em celulares?", "alternativas": ["Medir pressão", "Determinar localização", "Medir temperatura"], "correta": 1},
        {"pergunta": "Qual aparelho transforma uma folha de papel em imagem digital?", "alternativas": ["Roteador", "Modem", "Scanner"], "correta": 2},
        {"pergunta": "O que significa salvar arquivos na nuvem?", "alternativas": ["Guardar em servidores remotos", "Guardar somente no pendrive", "Imprimir automaticamente"], "correta": 0},
        {"pergunta": "Qual atalho é normalmente usado para copiar no computador?", "alternativas": ["Ctrl mais P", "Ctrl mais C", "Ctrl mais S"], "correta": 1},
        {"pergunta": "Qual sistema operacional de celular é desenvolvido pelo Google?", "alternativas": ["Android", "iOS", "Windows Phone"], "correta": 0},
    ],

    "Língua Portuguesa": [
        {"pergunta": "Qual é o plural correto da palavra pão?", "alternativas": ["Pãos", "Pães", "Pãeses"], "correta": 1},
        {"pergunta": "Qual é o contrário da palavra claro?", "alternativas": ["Escuro", "Rápido", "Alto"], "correta": 0},
        {"pergunta": "Qual destas palavras é um verbo?", "alternativas": ["Bonito", "Casa", "Correr"], "correta": 2},
        {"pergunta": "A palavra ontem indica principalmente qual ideia?", "alternativas": ["Lugar", "Tempo", "Modo"], "correta": 1},
        {"pergunta": "Qual palavra é sinônimo de feliz?", "alternativas": ["Alegre", "Triste", "Lento"], "correta": 0},
    ],

    "Natureza": [
        {"pergunta": "Qual é a maior floresta tropical do mundo?", "alternativas": ["Floresta Amazônica", "Floresta do Congo", "Taiga Siberiana"], "correta": 0},
        {"pergunta": "Como se chama o processo em que plantas usam luz para produzir alimento?", "alternativas": ["Digestão", "Fotossíntese", "Evaporação"], "correta": 1},
        {"pergunta": "Como chamamos a água em estado sólido?", "alternativas": ["Vapor", "Orvalho", "Gelo"], "correta": 2},
        {"pergunta": "Qual estação vem depois do inverno no hemisfério sul?", "alternativas": ["Primavera", "Verão", "Outono"], "correta": 0},
        {"pergunta": "Qual destas é uma fonte de energia renovável?", "alternativas": ["Carvão", "Solar", "Diesel"], "correta": 1},
    ],

    "Invenções e Descobertas": [
        {"pergunta": "Quem é tradicionalmente creditado pela invenção do telefone?", "alternativas": ["Thomas Edison", "Alexander Graham Bell", "Nikola Tesla"], "correta": 1},
        {"pergunta": "Os irmãos Wright ficaram famosos por qual invenção?", "alternativas": ["Avião", "Rádio", "Máquina de escrever"], "correta": 0},
        {"pergunta": "Johannes Gutenberg é associado ao desenvolvimento de qual tecnologia?", "alternativas": ["Telescópio", "Imprensa de tipos móveis", "Bússola"], "correta": 1},
        {"pergunta": "Quem descobriu a penicilina?", "alternativas": ["Charles Darwin", "Isaac Newton", "Alexander Fleming"], "correta": 2},
        {"pergunta": "Quem criou a World Wide Web?", "alternativas": ["Tim Berners-Lee", "Steve Jobs", "Bill Gates"], "correta": 0},
    ],
}

# ============================================================
# UTILITÁRIOS
# ============================================================

def slug(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto).strip("_").lower()
    return texto or "video"


def executar(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        print(p.stderr[-5000:])
        raise RuntimeError("Comando retornou erro.")
    return p


def achar_fonte(*candidatos):
    for caminho in candidatos:
        if caminho and os.path.exists(caminho):
            return caminho
    return None


FONT_BOLD = achar_fonte(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
)

FONT_REG = achar_fonte(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
)


def fonte(tamanho, bold=True):
    caminho = FONT_BOLD if bold else FONT_REG
    if caminho:
        return ImageFont.truetype(caminho, int(tamanho))
    return ImageFont.load_default()


def texto_central(draw, y, texto, fnt, fill, x0=0, x1=W):
    bb = draw.textbbox((0, 0), texto, font=fnt)
    tw = bb[2] - bb[0]
    x = x0 + ((x1 - x0) - tw) / 2
    draw.text((x, y), texto, font=fnt, fill=fill)


def wrap_text(draw, texto, fnt, max_width):
    palavras = str(texto).split()
    linhas = []
    atual = ""

    for palavra in palavras:
        teste = (atual + " " + palavra).strip()
        bb = draw.textbbox((0, 0), teste, font=fnt)
        if (bb[2] - bb[0]) <= max_width:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra

    if atual:
        linhas.append(atual)

    return linhas


def desenhar_multilinha_central(draw, texto, fnt, y, max_width, fill, line_gap=10):
    linhas = wrap_text(draw, texto, fnt, max_width)
    bb = draw.textbbox((0, 0), "Ag", font=fnt)
    line_h = bb[3] - bb[1]
    yy = y
    for linha in linhas:
        texto_central(draw, yy, linha, fnt, fill, 100, W - 100)
        yy += line_h + line_gap
    return yy


# ============================================================
# RENDER DO MODELO GAME SHOW
# ============================================================

PURPLE = (58, 32, 92)
PINK = (255, 55, 122)
YELLOW = (255, 207, 25)
CORAL = (255, 94, 66)
CREAM = (255, 249, 239)
GREEN = (202, 255, 173)
GREEN_DARK = (19, 175, 113)
TEAL = (18, 188, 162)
LAVENDER = (110, 75, 215)


def render_frame(tema, pergunta, numero, estado, timer=None):
    img = Image.new("RGB", (W, H), CORAL)
    draw = ImageDraw.Draw(img)

    # Fundo: parte superior amarela e parte inferior coral.
    limite_topo = int(H * 0.31)
    draw.rectangle([0, 0, W, limite_topo], fill=YELLOW)
    draw.rectangle([0, limite_topo, W, H], fill=CORAL)

    # Raios decorativos no topo.
    cx, cy = W // 2, 170
    raio = 730
    for i in range(0, 360, 24):
        import math
        a1 = math.radians(i)
        a2 = math.radians(i + 10)
        pts = [
            (cx, cy),
            (cx + raio * math.cos(a1), cy + raio * math.sin(a1)),
            (cx + raio * math.cos(a2), cy + raio * math.sin(a2)),
        ]
        draw.polygon(pts, fill=(255, 221, 78))

    # Logo com borda branca e sombra rosa.
    logo_box = [280, 60, 800, 180]
    shadow = [logo_box[0] + 16, logo_box[1] + 18, logo_box[2] + 16, logo_box[3] + 18]
    draw.rounded_rectangle(shadow, radius=32, fill=PINK)
    draw.rounded_rectangle(logo_box, radius=32, fill=PURPLE, outline=(255, 255, 255), width=12)
    texto_central(draw, 86, "JUH QUIZ", fonte(54, True), (255, 255, 255))

    # Número 1/5.
    draw.rounded_rectangle([875, 62, 1018, 132], radius=22, fill=(255, 255, 255))
    texto_central(draw, 78, f"{numero}/5", fonte(34, True), PURPLE, 875, 1018)

    # Tema visível em cima.
    tema_txt = f"TEMA: {tema.upper()}"
    tema_font = fonte(27, True)
    bb = draw.textbbox((0, 0), tema_txt, font=tema_font)
    tw = bb[2] - bb[0]
    tema_x0 = (W - tw) / 2 - 28
    tema_x1 = (W + tw) / 2 + 28
    draw.rounded_rectangle(
        [tema_x0, 210, tema_x1, 272],
        radius=30,
        fill=(255, 249, 239),
        outline=PURPLE,
        width=4
    )
    texto_central(draw, 226, tema_txt, tema_font, PURPLE)

    # Card principal.
    card = [55, 340, W - 55, 1570]
    shadow_card = [card[0] + 20, card[1] + 22, card[2] + 20, card[3] + 22]
    draw.rounded_rectangle(shadow_card, radius=50, fill=(120, 62, 88))
    draw.rounded_rectangle(card, radius=50, fill=CREAM, outline=PURPLE, width=10)

    # Chamada.
    chamada = "DESAFIO RELÂMPAGO"
    f_chamada = fonte(27, True)
    bb = draw.textbbox((0, 0), chamada, font=f_chamada)
    cw = bb[2] - bb[0]
    draw.rounded_rectangle(
        [W/2 - cw/2 - 34, 390, W/2 + cw/2 + 34, 456],
        radius=32,
        fill=PINK
    )
    texto_central(draw, 408, chamada, f_chamada, (255, 255, 255))

    # Pergunta.
    f_q = fonte(54, True)
    y_after = desenhar_multilinha_central(
        draw,
        pergunta["pergunta"],
        f_q,
        505,
        800,
        (38, 32, 63),
        line_gap=10
    )

    # Cronômetro.
    timer_y = max(740, y_after + 30)
    timer_box = [W/2 - 72, timer_y, W/2 + 72, timer_y + 118]
    draw.rounded_rectangle(
        [timer_box[0] + 10, timer_box[1] + 10, timer_box[2] + 10, timer_box[3] + 10],
        radius=28,
        fill=PURPLE
    )
    draw.rounded_rectangle(timer_box, radius=28, fill=YELLOW, outline=PURPLE, width=7)

    if estado == "reading":
        timer_txt = "..."
        feedback = "OUÇA A PERGUNTA"
    elif estado == "countdown":
        timer_txt = str(timer)
        feedback = "AGORA RESPONDA!"
    else:
        timer_txt = "✓"
        feedback = "ACERTOU?"

    texto_central(draw, timer_y + 24, timer_txt, fonte(55, True), PURPLE, timer_box[0], timer_box[2])

    # Alternativas.
    alt_top = timer_y + 155
    letras = ["A", "B", "C"]
    label_colors = [LAVENDER, PINK, TEAL]

    for j, alt in enumerate(pergunta["alternativas"]):
        yy = alt_top + j * 130
        correta = j == int(pergunta["correta"])

        if estado == "answer" and correta:
            bg = GREEN
            label_bg = GREEN_DARK
            texto_cor = (38, 32, 63)
        elif estado == "answer" and not correta:
            bg = (238, 232, 226)
            label_bg = (170, 160, 168)
            texto_cor = (130, 125, 128)
        else:
            bg = (255, 255, 255)
            label_bg = label_colors[j]
            texto_cor = (38, 32, 63)

        box = [145, yy, W - 145, yy + 100]
        shadow_alt = [box[0] + 8, box[1] + 10, box[2] + 8, box[3] + 10]
        draw.rounded_rectangle(shadow_alt, radius=26, fill=PURPLE)
        draw.rounded_rectangle(box, radius=26, fill=bg, outline=PURPLE, width=6)

        label = [170, yy + 16, 250, yy + 84]
        draw.rounded_rectangle(label, radius=18, fill=label_bg)

        letra_txt = "✓" if (estado == "answer" and correta) else letras[j]
        texto_central(draw, yy + 29, letra_txt, fonte(38, True), (255, 255, 255), label[0], label[2])

        # Ajusta a fonte se a alternativa for maior.
        f_alt = fonte(37 if len(alt) <= 25 else 31, True)
        draw.text((285, yy + 28), alt, font=f_alt, fill=texto_cor)

    texto_central(draw, 1450, feedback, fonte(32, True), PINK)

    # Rodapé.
    texto_central(
        draw,
        H - 115,
        "QUANTAS VOCÊ CONSEGUE ACERTAR?",
        fonte(34, True),
        (255, 255, 255)
    )
    texto_central(
        draw,
        H - 70,
        "@juhquiz",
        fonte(26, True),
        (255, 240, 235)
    )

    return img


def render_final(tema):
    img = Image.new("RGB", (W, H), CORAL)
    draw = ImageDraw.Draw(img)

    limite_topo = int(H * 0.31)
    draw.rectangle([0, 0, W, limite_topo], fill=YELLOW)
    draw.rectangle([0, limite_topo, W, H], fill=CORAL)

    draw.rounded_rectangle([280, 60, 800, 180], radius=32, fill=PURPLE, outline=(255,255,255), width=12)
    texto_central(draw, 86, "JUH QUIZ", fonte(54, True), (255,255,255))

    tema_txt = f"TEMA: {tema.upper()}"
    texto_central(draw, 240, tema_txt, fonte(32, True), PURPLE)

    card = [80, 390, W - 80, 1490]
    draw.rounded_rectangle([card[0] + 20, card[1] + 22, card[2] + 20, card[3] + 22], radius=50, fill=(120,62,88))
    draw.rounded_rectangle(card, radius=50, fill=CREAM, outline=PURPLE, width=10)

    texto_central(draw, 520, "FIM DO DESAFIO!", fonte(56, True), PINK)
    texto_central(draw, 650, "QUANTAS VOCÊ ACERTOU?", fonte(48, True), PURPLE)

    placares = [
        "5/5 = GÊNIO",
        "4/5 = MUITO BOM",
        "3/5 = QUASE LÁ",
    ]
    y = 800
    for txt in placares:
        draw.rounded_rectangle([230, y, W - 230, y + 110], radius=28, fill=(255,255,255), outline=PURPLE, width=5)
        texto_central(draw, y + 30, txt, fonte(34, True), PURPLE)
        y += 145

    texto_central(draw, 1280, "COMENTA SUA PONTUAÇÃO", fonte(38, True), PINK)
    texto_central(draw, H - 110, "@juhquiz", fonte(28, True), (255,255,255))

    return img


# ============================================================
# ÁUDIO / FFMPEG
# ============================================================

def limpar_tts(texto):
    return re.sub(r"\s+", " ", str(texto)).strip()


def tts_salvar(texto, caminho):
    caminho = str(caminho)
    if os.path.exists(caminho):
        os.remove(caminho)

    p = subprocess.run(
        [
            "edge-tts",
            "--voice", VOZ,
            "--rate", VELOCIDADE_VOZ,
            "--text", limpar_tts(texto),
            "--write-media", caminho
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if p.returncode != 0:
        print(p.stderr)
        raise RuntimeError("Falha ao gerar voz com Edge TTS.")

    if not os.path.exists(caminho) or os.path.getsize(caminho) < 500:
        raise RuntimeError(f"Áudio não foi criado: {caminho}")


def duracao_audio(caminho):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(caminho)
    ]
    return float(subprocess.check_output(cmd, text=True).strip())


# Mesmos bips do outro gerador.
def criar_beep(caminho, frequencia=950):
    caminho = str(caminho)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency={frequencia}:duration=0.14",
        "-af", "volume=0.55,apad=pad_dur=1",
        "-t", "1.0",
        "-c:a", "aac", "-b:a", "160k",
        "-ar", str(AUDIO_HZ),
        "-ac", str(AUDIO_CHANNELS),
        caminho
    ]
    executar(cmd)


def criar_clipe_imagem(img_path, duracao, saida, audio=None):
    img_path = str(img_path)
    saida = str(saida)
    duracao = float(duracao)

    if audio:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-i", str(audio),
            "-t", f"{duracao:.3f}",
            "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p",
            "-af", f"aresample={AUDIO_HZ}:async=1:first_pts=0,apad",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-ar", str(AUDIO_HZ), "-ac", str(AUDIO_CHANNELS),
            "-video_track_timescale", "90000",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            saida
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_HZ}",
            "-t", f"{duracao:.3f}",
            "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-ar", str(AUDIO_HZ), "-ac", str(AUDIO_CHANNELS),
            "-shortest",
            "-video_track_timescale", "90000",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            saida
        ]

    executar(cmd)


def juntar_clipes(lista, saida, concat_path):
    concat_path = Path(concat_path).resolve()
    saida = Path(saida).resolve()

    concat_path.parent.mkdir(parents=True, exist_ok=True)
    saida.parent.mkdir(parents=True, exist_ok=True)

    with open(concat_path, "w", encoding="utf-8") as f:
        for p in lista:
            p_abs = Path(p).resolve()
            if not p_abs.exists():
                raise FileNotFoundError(f"Segmento não encontrado: {p_abs}")

            caminho_ffmpeg = str(p_abs).replace("'", "'\\''")
            f.write("file '" + caminho_ffmpeg + "'\n")

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_path),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-ar", str(AUDIO_HZ), "-ac", str(AUDIO_CHANNELS),
        "-af", f"aresample={AUDIO_HZ}:async=1:first_pts=0",
        "-avoid_negative_ts", "make_zero",
        "-movflags", "+faststart",
        str(saida)
    ]
    executar(cmd)


# ============================================================
# VALIDAÇÃO
# ============================================================

PERGUNTAS_DO_OUTRO_GERADOR = {
    "Em que ano o Brasil declarou sua independência de Portugal?",
    "Quem proclamou a Independência do Brasil?",
    "Qual foi a primeira capital do Brasil?",
    "Em que ano foi proclamada a República no Brasil?",
    "Qual cidade se tornou a capital do Brasil em 1960?",
    "Qual é o maior oceano da Terra?",
    "Qual é a capital do Japão?",
    "Em qual continente fica o Egito?",
    "Qual é o maior país da América do Sul em área?",
    "Qual é a capital da Argentina?",
    "Qual planeta é conhecido como Planeta Vermelho?",
    "Qual gás é essencial para a respiração humana?",
    "Qual órgão bombeia o sangue pelo corpo humano?",
    "Quantos planetas existem no Sistema Solar?",
    "A água congela a quantos graus Celsius ao nível do mar?",
    "Qual é o maior animal terrestre atualmente?",
    "Qual animal é conhecido por mudar de cor para se camuflar?",
    "Qual destes animais é um mamífero marinho?",
    "Qual animal possui listras pretas e brancas?",
    "Qual ave é conhecida por não voar e viver na Antártida?",
    "Qual é o maior órgão do corpo humano?",
    "Quantos pulmões uma pessoa normalmente possui?",
    "Qual órgão é responsável por filtrar o sangue e produzir urina?",
    "Qual parte do corpo contém o fêmur?",
    "Qual órgão está diretamente ligado à visão?",
    "Qual metal é líquido em temperatura ambiente?",
    "Qual é o único mamífero capaz de voo verdadeiro?",
    "Qual país é conhecido pelo formato de uma bota?",
    "Qual é a cor resultante da mistura de azul e amarelo?",
    "Qual instrumento é usado para medir a temperatura?",
    "Qual estrela está no centro do Sistema Solar?",
    "Qual é o maior planeta do Sistema Solar?",
    "Qual planeta é conhecido por seus anéis?",
    "Qual corpo celeste orbita naturalmente a Terra?",
    "Qual é o planeta mais próximo do Sol?",
    "Quantos lados tem um hexágono?",
    "Qual idioma é falado oficialmente no Brasil?",
    "Qual é a capital da França?",
    "Qual destes é um instrumento de cordas?",
    "Quantos dias possui uma semana?",
}


def validar():
    temas = list(QUIZZES.keys())
    if len(temas) != QUANTIDADE_VIDEOS:
        raise ValueError("O gerador precisa ter exatamente 8 temas.")

    vistas = set()

    for tema in temas:
        perguntas = QUIZZES[tema]

        if len(perguntas) != PERGUNTAS_POR_VIDEO:
            raise ValueError(f"Tema '{tema}' precisa ter exatamente 5 perguntas.")

        for q in perguntas:
            pergunta = q["pergunta"].strip()

            if pergunta in PERGUNTAS_DO_OUTRO_GERADOR:
                raise ValueError(f"Pergunta repetida do outro gerador: {pergunta}")

            if pergunta in vistas:
                raise ValueError(f"Pergunta repetida dentro deste gerador: {pergunta}")

            vistas.add(pergunta)

            if len(q["alternativas"]) != 3:
                raise ValueError(f"Pergunta sem 3 alternativas: {pergunta}")

            if int(q["correta"]) not in (0, 1, 2):
                raise ValueError(f"Índice de resposta inválido: {pergunta}")


# ============================================================
# GERAÇÃO
# ============================================================

def main():
    validar()

    if PASTA_TMP.exists():
        shutil.rmtree(PASTA_TMP)

    PASTA_TMP.mkdir(parents=True, exist_ok=True)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    print(f"📅 Pasta do dia: {PASTA_SAIDA}", flush=True)
    print(f"🎬 Gerando {QUANTIDADE_VIDEOS} vídeos × {PERGUNTAS_POR_VIDEO} perguntas", flush=True)
    print(f"🎙️ Voz: {VOZ} | velocidade: {VELOCIDADE_VOZ}", flush=True)
    print(f"⏱️ Contagem: {TEMPO_ESCOLHA} segundos", flush=True)

    beep_normal = PASTA_TMP / "beep_950.m4a"
    beep_final = PASTA_TMP / "beep_1250.m4a"

    criar_beep(beep_normal, 950)
    criar_beep(beep_final, 1250)

    videos_gerados = []

    for video_num, (tema, perguntas_tema) in enumerate(QUIZZES.items(), start=1):
        print("\n" + "=" * 72, flush=True)
        print(f"🎬 {video_num:02d}/08 — {tema}", flush=True)
        print("=" * 72, flush=True)

        pasta_video = PASTA_TMP / f"video_{video_num:02d}_{slug(tema)}"
        pasta_video.mkdir(parents=True, exist_ok=True)

        segmentos = []

        for idx, pergunta in enumerate(perguntas_tema):
            numero = idx + 1
            print(f" • {numero}/5 — {pergunta['pergunta']}", flush=True)

            pasta_q = pasta_video / f"q{numero:02d}"
            pasta_q.mkdir(parents=True, exist_ok=True)

            # 1) NARRA SOMENTE A PERGUNTA
            audio_q = pasta_q / "pergunta.mp3"
            tts_salvar(pergunta["pergunta"], audio_q)
            dur_q = duracao_audio(audio_q) + 0.15

            frame_q = pasta_q / "01_pergunta.png"
            render_frame(
                tema=tema,
                pergunta=pergunta,
                numero=numero,
                estado="reading"
            ).save(frame_q)

            clip_q = pasta_q / "01_pergunta.mp4"
            criar_clipe_imagem(frame_q, dur_q, clip_q, audio=audio_q)
            segmentos.append(clip_q)

            # 2) DEPOIS DA LEITURA, COMEÇA A CONTA DE 3 SEGUNDOS
            for segundos in range(TEMPO_ESCOLHA, 0, -1):
                frame_timer = pasta_q / f"timer_{segundos}.png"
                render_frame(
                    tema=tema,
                    pergunta=pergunta,
                    numero=numero,
                    estado="countdown",
                    timer=segundos
                ).save(frame_timer)

                clip_timer = pasta_q / f"timer_{segundos}.mp4"
                som = beep_final if segundos == 1 else beep_normal
                criar_clipe_imagem(frame_timer, 1.0, clip_timer, audio=som)
                segmentos.append(clip_timer)

            # 3) REVELA E NARRA SOMENTE A RESPOSTA CERTA
            correta = int(pergunta["correta"])
            texto_resposta = pergunta["alternativas"][correta]

            audio_resp = pasta_q / "resposta.mp3"
            tts_salvar(texto_resposta, audio_resp)
            dur_resp = duracao_audio(audio_resp) + PAUSA_DEPOIS_RESPOSTA

            frame_resp = pasta_q / "03_resposta.png"
            render_frame(
                tema=tema,
                pergunta=pergunta,
                numero=numero,
                estado="answer"
            ).save(frame_resp)

            clip_resp = pasta_q / "03_resposta.mp4"
            criar_clipe_imagem(frame_resp, dur_resp, clip_resp, audio=audio_resp)
            segmentos.append(clip_resp)

        # Tela final
        frame_final = pasta_video / "final.png"
        render_final(tema).save(frame_final)

        clip_final = pasta_video / "final.mp4"
        criar_clipe_imagem(frame_final, 2.0, clip_final)
        segmentos.append(clip_final)

        nome_saida = f"{video_num:02d}_{slug(tema)}_{DATA_DO_DIA}.mp4"
        saida_video = PASTA_SAIDA / nome_saida

        juntar_clipes(segmentos, saida_video, pasta_video / "concat.txt")
        videos_gerados.append(saida_video)

        print(f"✅ Vídeo {video_num}/8 gerado: {saida_video}", flush=True)

    print("\n✅ FINALIZADO", flush=True)
    print(f"📁 {PASTA_SAIDA}", flush=True)
    for p in videos_gerados:
        print(" -", p, flush=True)


if __name__ == "__main__":
    main()
