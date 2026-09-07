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

QUANTIDADE_VIDEOS = 45
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
# 45 TEMAS × 5 PERGUNTAS NOVAS
# correta: 0=A, 1=B, 2=C
# As perguntas abaixo são diferentes das 40 usadas no gerador rosa.
# ============================================================
QUIZZES = {
    "Olimpíadas": [
        {"pergunta": "Quantos anéis aparecem no símbolo olímpico?", "alternativas": ["4", "5", "6"], "correta": 1},
        {"pergunta": "Em qual cidade aconteceram os primeiros Jogos Olímpicos modernos, em 1896?", "alternativas": ["Paris", "Roma", "Atenas"], "correta": 2},
        {"pergunta": "Em qual país fica Olímpia, onde tradicionalmente é acesa a chama olímpica?", "alternativas": ["Grécia", "Itália", "França"], "correta": 0},
        {"pergunta": "Qual é a distância oficial de uma maratona?", "alternativas": ["40 km", "42,195 km", "50 km"], "correta": 1},
        {"pergunta": "Qual é o comprimento de uma piscina olímpica?", "alternativas": ["25 metros", "100 metros", "50 metros"], "correta": 2},
    ],

    "Fórmula 1": [
        {"pergunta": "Qual bandeira indica o fim de uma corrida de Fórmula 1?", "alternativas": ["Amarela", "Vermelha", "Quadriculada"], "correta": 2},
        {"pergunta": "Como é chamado o local onde os carros param para trocar pneus?", "alternativas": ["Pit stop", "Grid", "Pódio"], "correta": 0},
        {"pergunta": "Como é chamada a primeira posição do grid de largada?", "alternativas": ["Safety position", "Pole position", "Fast position"], "correta": 1},
        {"pergunta": "Qual equipe de Fórmula 1 é famosa pelo símbolo do cavalo rampante?", "alternativas": ["McLaren", "Mercedes", "Ferrari"], "correta": 2},
        {"pergunta": "Quantos pilotos ocupam normalmente um carro de Fórmula 1 durante a corrida?", "alternativas": ["1", "2", "3"], "correta": 0},
    ],

    "Basquete": [
        {"pergunta": "Quantos jogadores de cada equipe ficam normalmente em quadra no basquete?", "alternativas": ["5", "6", "7"], "correta": 0},
        {"pergunta": "Quantos pontos vale uma cesta feita além da linha de três pontos?", "alternativas": ["2", "3", "4"], "correta": 1},
        {"pergunta": "Quanto vale um lance livre convertido?", "alternativas": ["3 pontos", "2 pontos", "1 ponto"], "correta": 2},
        {"pergunta": "Qual é aproximadamente a altura oficial da cesta de basquete?", "alternativas": ["3,05 metros", "2,50 metros", "4 metros"], "correta": 0},
        {"pergunta": "Na NBA, quantos segundos uma equipe possui para tentar uma cesta?", "alternativas": ["30", "24", "45"], "correta": 1},
    ],

    "Vôlei": [
        {"pergunta": "Quantos jogadores de cada equipe ficam em quadra no vôlei?", "alternativas": ["5", "6", "7"], "correta": 1},
        {"pergunta": "Quantos pontos normalmente são necessários para vencer um set comum de vôlei?", "alternativas": ["21", "15", "25"], "correta": 2},
        {"pergunta": "Qual jogador utiliza uniforme diferente dos demais no vôlei?", "alternativas": ["Líbero", "Capitão", "Levantador"], "correta": 0},
        {"pergunta": "Quantos toques uma equipe normalmente pode dar antes de enviar a bola para o outro lado?", "alternativas": ["2", "3", "5"], "correta": 1},
        {"pergunta": "De onde é realizado o saque no vôlei?", "alternativas": ["Do centro da quadra", "Próximo à rede", "Atrás da linha de fundo"], "correta": 2},
    ],

    "Tênis": [
        {"pergunta": "Qual palavra representa zero na pontuação do tênis?", "alternativas": ["Zero", "Point", "Love"], "correta": 2},
        {"pergunta": "Qual é a sequência inicial tradicional de pontuação no tênis?", "alternativas": ["15, 30 e 40", "10, 20 e 30", "20, 40 e 60"], "correta": 0},
        {"pergunta": "Em qual superfície é disputado Wimbledon?", "alternativas": ["Saibro", "Grama", "Areia"], "correta": 1},
        {"pergunta": "Quantos torneios formam o Grand Slam do tênis?", "alternativas": ["3", "5", "4"], "correta": 2},
        {"pergunta": "Qual objeto é usado para golpear a bola no tênis?", "alternativas": ["Raquete", "Taco", "Bastão"], "correta": 0},
    ],

    "Artes Marciais": [
        {"pergunta": "Em qual país surgiu o judô?", "alternativas": ["Japão", "China", "Brasil"], "correta": 0},
        {"pergunta": "Qual arte marcial é originária da Coreia?", "alternativas": ["Judô", "Taekwondo", "Capoeira"], "correta": 1},
        {"pergunta": "Qual luta brasileira combina golpes, música e movimentos acrobáticos?", "alternativas": ["Karatê", "Boxe", "Capoeira"], "correta": 2},
        {"pergunta": "Qual proteção é usada nas mãos no boxe?", "alternativas": ["Luvas", "Caneleiras", "Nadadeiras"], "correta": 0},
        {"pergunta": "Qual arte marcial japonesa utiliza golpes de mãos e pés e significa 'mãos vazias'?", "alternativas": ["Sumô", "Karatê", "Esgrima"], "correta": 1},
    ],

    "Esportes Radicais": [
        {"pergunta": "Qual esporte utiliza uma prancha com quatro rodas?", "alternativas": ["Surfe", "Snowboard", "Skate"], "correta": 2},
        {"pergunta": "Qual esporte consiste em deslizar sobre ondas usando uma prancha?", "alternativas": ["Surfe", "Rapel", "Motocross"], "correta": 0},
        {"pergunta": "Qual atividade consiste em saltar de um local alto preso por uma corda elástica?", "alternativas": ["Paraquedismo", "Bungee jumping", "Escalada"], "correta": 1},
        {"pergunta": "Qual esporte utiliza um paraquedas após um salto de grande altitude?", "alternativas": ["Rapel", "Skate", "Paraquedismo"], "correta": 2},
        {"pergunta": "Qual atividade consiste em subir paredes naturais ou artificiais usando mãos e pés?", "alternativas": ["Escalada", "Rafting", "Surfe"], "correta": 0},
    ],

    "Clubes do Futebol Brasileiro": [
        {"pergunta": "Quais são as cores tradicionais do Flamengo?", "alternativas": ["Verde e branco", "Vermelho e preto", "Azul e branco"], "correta": 1},
        {"pergunta": "Qual clube brasileiro é conhecido pela cor verde e pelo apelido Verdão?", "alternativas": ["Fluminense", "Corinthians", "Palmeiras"], "correta": 2},
        {"pergunta": "De qual cidade é o Corinthians?", "alternativas": ["São Paulo", "Recife", "Salvador"], "correta": 0},
        {"pergunta": "Em qual cidade fica a sede do Grêmio?", "alternativas": ["Curitiba", "Porto Alegre", "Brasília"], "correta": 1},
        {"pergunta": "Qual clube mineiro utiliza uma raposa como mascote tradicional?", "alternativas": ["Bahia", "Santos", "Cruzeiro"], "correta": 2},
    ],

    "Estádios Famosos": [
        {"pergunta": "Em qual cidade fica o estádio do Maracanã?", "alternativas": ["São Paulo", "Brasília", "Rio de Janeiro"], "correta": 2},
        {"pergunta": "Em qual cidade fica o estádio Mineirão?", "alternativas": ["Belo Horizonte", "Fortaleza", "Curitiba"], "correta": 0},
        {"pergunta": "Em qual cidade fica o estádio de Wembley?", "alternativas": ["Madri", "Londres", "Paris"], "correta": 1},
        {"pergunta": "Em qual cidade fica o Camp Nou?", "alternativas": ["Milão", "Lisboa", "Barcelona"], "correta": 2},
        {"pergunta": "Em qual cidade argentina fica o estádio La Bombonera?", "alternativas": ["Buenos Aires", "Córdoba", "Rosário"], "correta": 0},
    ],

    "Mascotes Esportivos": [
        {"pergunta": "Qual animal inspirou Fuleco, mascote da Copa do Mundo de 2014?", "alternativas": ["Tatu-bola", "Onça", "Capivara"], "correta": 0},
        {"pergunta": "Qual era o animal do mascote Zabivaka da Copa de 2018?", "alternativas": ["Leão", "Lobo", "Urso"], "correta": 1},
        {"pergunta": "Qual animal era Misha, mascote dos Jogos Olímpicos de Moscou de 1980?", "alternativas": ["Tigre", "Panda", "Urso"], "correta": 2},
        {"pergunta": "Qual foi o nome de um dos mascotes dos Jogos Olímpicos Rio 2016?", "alternativas": ["Vinicius", "Fuleco", "Zabivaka"], "correta": 0},
        {"pergunta": "Qual personagem foi o mascote da Copa do Mundo de 1966?", "alternativas": ["Naranjito", "World Cup Willie", "Footix"], "correta": 1},
    ],

    "Rock Nacional": [
        {"pergunta": "Quem foi o vocalista da Legião Urbana?", "alternativas": ["Cazuza", "Renato Russo", "Herbert Vianna"], "correta": 1},
        {"pergunta": "Cazuza foi vocalista de qual banda antes da carreira solo?", "alternativas": ["Titãs", "Legião Urbana", "Barão Vermelho"], "correta": 2},
        {"pergunta": "Qual banda brasileira gravou a música 'Epitáfio'?", "alternativas": ["Titãs", "Skank", "Capital Inicial"], "correta": 0},
        {"pergunta": "Quem é o vocalista de Os Paralamas do Sucesso?", "alternativas": ["Samuel Rosa", "Herbert Vianna", "Dinho Ouro Preto"], "correta": 1},
        {"pergunta": "Qual banda de Brasília tem Dinho Ouro Preto como vocalista?", "alternativas": ["Jota Quest", "Charlie Brown Jr.", "Capital Inicial"], "correta": 2},
    ],

    "Sertanejo": [
        {"pergunta": "Qual dupla ficou famosa pela música 'Evidências'?", "alternativas": ["Jorge e Mateus", "Bruno e Marrone", "Chitãozinho e Xororó"], "correta": 2},
        {"pergunta": "Marília Mendonça ficou conhecida por qual apelido?", "alternativas": ["Rainha da Sofrência", "Rainha do Rock", "Rainha do Axé"], "correta": 0},
        {"pergunta": "Jorge e Mateus formam uma dupla de qual gênero musical?", "alternativas": ["Samba", "Sertanejo", "Rock"], "correta": 1},
        {"pergunta": "Qual dupla interpreta o clássico sertanejo 'Fio de Cabelo'?", "alternativas": ["Zezé Di Camargo e Luciano", "Victor e Leo", "Chitãozinho e Xororó"], "correta": 2},
        {"pergunta": "Qual instrumento de cordas é muito utilizado na música sertaneja?", "alternativas": ["Viola caipira", "Harpa", "Violoncelo"], "correta": 0},
    ],

    "Samba e Pagode": [
        {"pergunta": "Qual compositor brasileiro foi um dos fundadores da Estação Primeira de Mangueira?", "alternativas": ["Cartola", "Raul Seixas", "Luiz Gonzaga"], "correta": 0},
        {"pergunta": "Qual cantor é conhecido por sucessos do samba e pagode como 'Deixa a Vida Me Levar'?", "alternativas": ["Djavan", "Zeca Pagodinho", "Roberto Carlos"], "correta": 1},
        {"pergunta": "Qual destes é um instrumento muito utilizado no samba?", "alternativas": ["Violoncelo", "Fagote", "Pandeiro"], "correta": 2},
        {"pergunta": "Quem compôs 'Trem das Onze'?", "alternativas": ["Adoniran Barbosa", "Tim Maia", "Renato Russo"], "correta": 0},
        {"pergunta": "Qual grupo é considerado uma referência na história do pagode brasileiro?", "alternativas": ["Roupa Nova", "Fundo de Quintal", "Engenheiros do Hawaii"], "correta": 1},
    ],

    "Forró": [
        {"pergunta": "Quem é conhecido como o Rei do Baião?", "alternativas": ["Dominguinhos", "Luiz Gonzaga", "Alceu Valença"], "correta": 1},
        {"pergunta": "Qual conjunto de instrumentos é tradicional no trio de forró?", "alternativas": ["Violino, piano e flauta", "Guitarra, baixo e bateria", "Sanfona, zabumba e triângulo"], "correta": 2},
        {"pergunta": "Quem gravou e popularizou a música 'Asa Branca' ao lado de Humberto Teixeira como compositor?", "alternativas": ["Luiz Gonzaga", "Gilberto Gil", "Caetano Veloso"], "correta": 0},
        {"pergunta": "Qual destes ritmos está diretamente ligado ao forró?", "alternativas": ["Reggae", "Xote", "Jazz"], "correta": 1},
        {"pergunta": "Qual músico brasileiro ficou famoso como grande sanfoneiro e parceiro de Luiz Gonzaga?", "alternativas": ["Tom Jobim", "Chico Buarque", "Dominguinhos"], "correta": 2},
    ],

    "Instrumentos Musicais": [
        {"pergunta": "Quantas teclas possui normalmente um piano moderno de tamanho completo?", "alternativas": ["88", "72", "100"], "correta": 0},
        {"pergunta": "Quantas cordas possui normalmente um violino?", "alternativas": ["6", "4", "8"], "correta": 1},
        {"pergunta": "A qual família pertence o saxofone?", "alternativas": ["Cordas", "Percussão", "Madeiras"], "correta": 2},
        {"pergunta": "Qual destes instrumentos pertence à família dos metais?", "alternativas": ["Trompete", "Violino", "Flauta doce"], "correta": 0},
        {"pergunta": "Qual destes é um instrumento de percussão?", "alternativas": ["Clarinete", "Bateria", "Violoncelo"], "correta": 1},
    ],

    "Bandas Famosas": [
        {"pergunta": "Em qual cidade inglesa surgiu a banda The Beatles?", "alternativas": ["Londres", "Manchester", "Liverpool"], "correta": 2},
        {"pergunta": "Quem foi o vocalista mais conhecido da banda Queen?", "alternativas": ["Freddie Mercury", "Bono", "Kurt Cobain"], "correta": 0},
        {"pergunta": "Quem foi o vocalista da banda Nirvana?", "alternativas": ["Axl Rose", "Kurt Cobain", "Mick Jagger"], "correta": 1},
        {"pergunta": "Qual banda tem Bono como vocalista?", "alternativas": ["Coldplay", "Oasis", "U2"], "correta": 2},
        {"pergunta": "De qual país surgiu o grupo ABBA?", "alternativas": ["Suécia", "Estados Unidos", "Canadá"], "correta": 0},
    ],

    "Cantores Internacionais": [
        {"pergunta": "Qual cantor ficou conhecido como Rei do Pop?", "alternativas": ["Michael Jackson", "Elton John", "Bruno Mars"], "correta": 0},
        {"pergunta": "A cantora Adele nasceu em qual país?", "alternativas": ["Canadá", "Reino Unido", "Austrália"], "correta": 1},
        {"pergunta": "Shakira nasceu em qual país?", "alternativas": ["México", "Espanha", "Colômbia"], "correta": 2},
        {"pergunta": "Céline Dion nasceu em qual país?", "alternativas": ["Canadá", "França", "Estados Unidos"], "correta": 0},
        {"pergunta": "Qual cantor interpreta o hit 'Just the Way You Are'?", "alternativas": ["Ed Sheeran", "Bruno Mars", "Justin Bieber"], "correta": 1},
    ],

    "Festivais de Música": [
        {"pergunta": "Em qual cidade brasileira nasceu o festival Rock in Rio?", "alternativas": ["São Paulo", "Rio de Janeiro", "Salvador"], "correta": 1},
        {"pergunta": "Em qual estado americano acontece o festival Coachella?", "alternativas": ["Texas", "Flórida", "Califórnia"], "correta": 2},
        {"pergunta": "Em qual país acontece o tradicional festival Glastonbury?", "alternativas": ["Reino Unido", "Itália", "Canadá"], "correta": 0},
        {"pergunta": "Quem criou originalmente o festival Lollapalooza?", "alternativas": ["Dave Grohl", "Perry Farrell", "Bono"], "correta": 1},
        {"pergunta": "Em qual país acontece o festival Tomorrowland?", "alternativas": ["Holanda", "Alemanha", "Bélgica"], "correta": 2},
    ],

    "K-pop": [
        {"pergunta": "De qual país surgiu o gênero conhecido como K-pop?", "alternativas": ["Japão", "China", "Coreia do Sul"], "correta": 2},
        {"pergunta": "Como é conhecido o fandom do grupo BTS?", "alternativas": ["ARMY", "BLINK", "ONCE"], "correta": 0},
        {"pergunta": "Quantas integrantes formam o grupo BLACKPINK?", "alternativas": ["5", "4", "7"], "correta": 1},
        {"pergunta": "Qual grupo possui integrantes como RM, Jin, Suga e J-Hope?", "alternativas": ["EXO", "Stray Kids", "BTS"], "correta": 2},
        {"pergunta": "Como é conhecido o fandom do BLACKPINK?", "alternativas": ["BLINK", "ARMY", "MOA"], "correta": 0},
    ],

    "Hits dos Anos 2000": [
        {"pergunta": "Quem lançou o hit 'Crazy in Love' em 2003?", "alternativas": ["Beyoncé", "Rihanna", "Pink"], "correta": 0},
        {"pergunta": "Qual cantora lançou 'Umbrella' em 2007?", "alternativas": ["Britney Spears", "Rihanna", "Alicia Keys"], "correta": 1},
        {"pergunta": "Quem canta o hit 'Poker Face'?", "alternativas": ["Katy Perry", "Beyoncé", "Lady Gaga"], "correta": 2},
        {"pergunta": "Qual grupo lançou 'I Gotta Feeling' em 2009?", "alternativas": ["Black Eyed Peas", "Maroon 5", "Coldplay"], "correta": 0},
        {"pergunta": "Qual banda lançou a música 'Viva la Vida'?", "alternativas": ["U2", "Coldplay", "Oasis"], "correta": 1},
    ],

    "Novelas Brasileiras": [
        {"pergunta": "Qual personagem de Avenida Brasil busca vingança contra Carminha?", "alternativas": ["Jade", "Nina", "Tieta"], "correta": 1},
        {"pergunta": "Em qual novela aparece a personagem Jade?", "alternativas": ["Avenida Brasil", "Vale Tudo", "O Clone"], "correta": 2},
        {"pergunta": "Qual região brasileira dá nome à novela Pantanal?", "alternativas": ["Pantanal", "Amazônia", "Sertão"], "correta": 0},
        {"pergunta": "Qual personagem ficou famosa na novela Vale Tudo por seu assassinato misterioso?", "alternativas": ["Carminha", "Odete Roitman", "Nazaré Tedesco"], "correta": 1},
        {"pergunta": "A novela Tieta foi baseada em obra de qual escritor?", "alternativas": ["Machado de Assis", "José de Alencar", "Jorge Amado"], "correta": 2},
    ],

    "Doramas": [
        {"pergunta": "Como são chamados popularmente os dramas produzidos na Coreia do Sul?", "alternativas": ["K-dramas", "J-dramas", "C-dramas"], "correta": 0},
        {"pergunta": "Qual país produz os chamados J-dramas?", "alternativas": ["China", "Japão", "Tailândia"], "correta": 1},
        {"pergunta": "Qual série sul-coreana acompanha participantes em jogos mortais por um grande prêmio?", "alternativas": ["Goblin", "Pousando no Amor", "Round 6"], "correta": 2},
        {"pergunta": "Qual dorama envolve uma empresária sul-coreana que cai acidentalmente na Coreia do Norte?", "alternativas": ["Pousando no Amor", "Pretendente Surpresa", "Itaewon Class"], "correta": 0},
        {"pergunta": "Qual termo é usado para dramas produzidos na China?", "alternativas": ["K-drama", "C-drama", "J-drama"], "correta": 1},
    ],

    "Animes e Mangás": [
        {"pergunta": "Qual é o nome do protagonista de Dragon Ball?", "alternativas": ["Naruto", "Luffy", "Goku"], "correta": 2},
        {"pergunta": "Em qual vila ninja vive Naruto?", "alternativas": ["Konoha", "Suna", "Kiri"], "correta": 0},
        {"pergunta": "Qual personagem é o protagonista de One Piece?", "alternativas": ["Ichigo", "Monkey D. Luffy", "Gohan"], "correta": 1},
        {"pergunta": "Em Death Note, qual objeto permite matar alguém ao escrever seu nome?", "alternativas": ["Espada", "Relógio", "Caderno"], "correta": 2},
        {"pergunta": "Qual é o nome da protagonista de Sailor Moon?", "alternativas": ["Usagi Tsukino", "Sakura Haruno", "Bulma"], "correta": 0},
    ],

    "Filmes de Terror": [
        {"pergunta": "Qual é o nome do palhaço de 'It: A Coisa'?", "alternativas": ["Pennywise", "Ghostface", "Freddy"], "correta": 0},
        {"pergunta": "Qual personagem possui lâminas nas luvas em 'A Hora do Pesadelo'?", "alternativas": ["Jason", "Freddy Krueger", "Michael Myers"], "correta": 1},
        {"pergunta": "Qual é o nome do assassino mascarado da franquia Pânico?", "alternativas": ["Leatherface", "Jigsaw", "Ghostface"], "correta": 2},
        {"pergunta": "Em 'O Iluminado', qual é o nome do hotel onde ocorre grande parte da história?", "alternativas": ["Overlook Hotel", "Bates Motel", "Hotel California"], "correta": 0},
        {"pergunta": "Qual personagem é possuída em 'O Exorcista'?", "alternativas": ["Carrie", "Regan", "Wendy"], "correta": 1},
    ],

    "Ficção Científica": [
        {"pergunta": "Qual computador aparece no filme '2001: Uma Odisseia no Espaço'?", "alternativas": ["R2-D2", "HAL 9000", "T-800"], "correta": 1},
        {"pergunta": "Qual veículo é transformado em máquina do tempo em 'De Volta para o Futuro'?", "alternativas": ["Mustang", "Fusca", "DeLorean"], "correta": 2},
        {"pergunta": "Qual personagem é o protagonista de Matrix?", "alternativas": ["Neo", "Ripley", "Deckard"], "correta": 0},
        {"pergunta": "Qual criatura extraterrestre aparece na franquia Alien?", "alternativas": ["Predador", "Xenomorfo", "Ewok"], "correta": 1},
        {"pergunta": "Em E.T., qual personagem quer voltar para casa?", "alternativas": ["Um robô", "Um astronauta", "Um extraterrestre"], "correta": 2},
    ],

"Filmes de Fantasia": [
    {"pergunta": "Qual objeto Frodo precisa destruir em O Senhor dos Anéis?", "alternativas": ["Um colar", "Uma espada", "Um anel"], "correta": 2},
    {"pergunta": "Qual é a escola de magia frequentada por Harry Potter?", "alternativas": ["Hogwarts", "Nárnia", "Camelot"], "correta": 0},
    {"pergunta": "Por qual objeto as crianças entram em Nárnia no primeiro filme da série?", "alternativas": ["Espelho", "Guarda-roupa", "Janela"], "correta": 1},
    {"pergunta": "Quem é o protagonista de O Hobbit?", "alternativas": ["Aragorn", "Gandalf", "Bilbo Bolseiro"], "correta": 2},
    {"pergunta": "Qual é o nome da protagonista de O Mágico de Oz?", "alternativas": ["Dorothy", "Alice", "Wendy"], "correta": 0},
],

    "Oscar e Premiações do Cinema": [
        {"pergunta": "Qual organização entrega o Oscar?", "alternativas": ["Academia de Artes e Ciências Cinematográficas", "Grammy Academy", "FIFA"], "correta": 0},
        {"pergunta": "Qual categoria premia o filme considerado o principal vencedor da cerimônia?", "alternativas": ["Melhor Figurino", "Melhor Filme", "Melhor Som"], "correta": 1},
        {"pergunta": "Em qual ano aconteceu a primeira cerimônia do Oscar?", "alternativas": ["1950", "1910", "1929"], "correta": 2},
        {"pergunta": "Como é popularmente chamada a estatueta entregue aos vencedores?", "alternativas": ["Oscar", "Emmy", "Grammy"], "correta": 0},
        {"pergunta": "Qual premiação é voltada principalmente para produções de televisão nos Estados Unidos?", "alternativas": ["Oscar", "Emmy", "Grammy"], "correta": 1},
    ],

    "Personagens Famosos do Cinema": [
        {"pergunta": "Qual é a profissão de Indiana Jones?", "alternativas": ["Médico", "Arqueólogo", "Piloto"], "correta": 1},
        {"pergunta": "Qual personagem é um boxeador da Filadélfia?", "alternativas": ["Rambo", "Terminator", "Rocky Balboa"], "correta": 2},
        {"pergunta": "Qual personagem é capitão do navio Pérola Negra?", "alternativas": ["Jack Sparrow", "Indiana Jones", "Sherlock Holmes"], "correta": 0},
        {"pergunta": "Qual personagem diz que a vida é como uma caixa de chocolates?", "alternativas": ["Rocky", "Forrest Gump", "Neo"], "correta": 1},
        {"pergunta": "Qual personagem robótico é interpretado por Arnold Schwarzenegger na franquia O Exterminador do Futuro?", "alternativas": ["R2-D2", "C-3PO", "T-800"], "correta": 2},
    ],

    "Vilões Famosos": [
        {"pergunta": "Qual vilão é pai de Luke Skywalker em Star Wars?", "alternativas": ["Thanos", "Voldemort", "Darth Vader"], "correta": 2},
        {"pergunta": "Qual vilão é o principal inimigo do Batman e costuma usar maquiagem de palhaço?", "alternativas": ["Coringa", "Duende Verde", "Magneto"], "correta": 0},
        {"pergunta": "Qual vilão é o principal inimigo de Harry Potter?", "alternativas": ["Saruman", "Voldemort", "Loki"], "correta": 1},
        {"pergunta": "Qual vilão busca reunir as Joias do Infinito no universo Marvel?", "alternativas": ["Ultron", "Caveira Vermelha", "Thanos"], "correta": 2},
        {"pergunta": "Qual personagem é o vilão de O Rei Leão e irmão de Mufasa?", "alternativas": ["Scar", "Simba", "Rafiki"], "correta": 0},
    ],

    "Desenhos dos Anos 90": [
        {"pergunta": "Qual desenho acompanha um garoto cientista com um laboratório secreto?", "alternativas": ["O Laboratório de Dexter", "Doug", "Rugrats"], "correta": 0},
        {"pergunta": "Quais personagens formam As Meninas Superpoderosas?", "alternativas": ["Anna, Elsa e Moana", "Florzinha, Lindinha e Docinho", "Mônica, Magali e Denise"], "correta": 1},
        {"pergunta": "Qual desenho acompanha bebês como Tommy e Chuckie?", "alternativas": ["Hey Arnold!", "Pokémon", "Rugrats"], "correta": 2},
        {"pergunta": "Qual personagem possui uma cabeça com formato parecido com uma bola de futebol americano?", "alternativas": ["Arnold", "Dexter", "Doug"], "correta": 0},
        {"pergunta": "Qual anime se tornou famoso mundialmente com personagens como Ash e Pikachu?", "alternativas": ["Digimon", "Pokémon", "Naruto"], "correta": 1},
    ],

    "Moedas do Mundo": [
        {"pergunta": "Qual é a moeda do Japão?", "alternativas": ["Won", "Yuan", "Iene"], "correta": 2},
        {"pergunta": "Qual é a moeda oficial do Reino Unido?", "alternativas": ["Libra esterlina", "Euro", "Dólar"], "correta": 0},
        {"pergunta": "Qual é a moeda da Suíça?", "alternativas": ["Euro", "Franco suíço", "Coroa"], "correta": 1},
        {"pergunta": "Qual é a moeda oficial da Índia?", "alternativas": ["Peso", "Dinar", "Rúpia"], "correta": 2},
        {"pergunta": "Qual é a moeda da Coreia do Sul?", "alternativas": ["Won", "Iene", "Yuan"], "correta": 0},
    ],

    "Idiomas do Mundo": [
        {"pergunta": "Qual é o idioma oficial do Brasil?", "alternativas": ["Português", "Espanhol", "Francês"], "correta": 0},
        {"pergunta": "Qual idioma é falado oficialmente na Argentina?", "alternativas": ["Italiano", "Espanhol", "Alemão"], "correta": 1},
        {"pergunta": "Qual é o principal idioma do Japão?", "alternativas": ["Mandarim", "Coreano", "Japonês"], "correta": 2},
        {"pergunta": "Qual é o idioma oficial predominante da Alemanha?", "alternativas": ["Alemão", "Holandês", "Sueco"], "correta": 0},
        {"pergunta": "Qual idioma é oficial no Egito?", "alternativas": ["Persa", "Árabe", "Hindi"], "correta": 1},
    ],

    "Siglas e Abreviações": [
        {"pergunta": "O que significa a sigla CPU em informática?", "alternativas": ["Central Power Unit", "Central Processing Unit", "Computer Personal User"], "correta": 1},
        {"pergunta": "O que significa USB?", "alternativas": ["Universal System Base", "User Serial Box", "Universal Serial Bus"], "correta": 2},
        {"pergunta": "O que significa GPS?", "alternativas": ["Global Positioning System", "General Power Service", "Global Phone Signal"], "correta": 0},
        {"pergunta": "O que significa PDF?", "alternativas": ["Personal Data File", "Portable Document Format", "Public Digital Folder"], "correta": 1},
        {"pergunta": "O que significa HTML?", "alternativas": ["High Text Machine Language", "Home Tool Markup Link", "HyperText Markup Language"], "correta": 2},
    ],

    "Emojis e Seus Significados": [
        {"pergunta": "Qual sentimento o emoji ❤️ geralmente representa?", "alternativas": ["Raiva", "Sono", "Amor"], "correta": 2},
        {"pergunta": "O emoji 😂 geralmente indica qual reação?", "alternativas": ["Riso intenso", "Tristeza profunda", "Sono"], "correta": 0},
        {"pergunta": "O emoji 👍 geralmente é usado para indicar o quê?", "alternativas": ["Dúvida", "Aprovação", "Choro"], "correta": 1},
        {"pergunta": "Na internet, o emoji 🔥 costuma indicar algo que está como?", "alternativas": ["Gelado", "Esquecido", "Muito bom ou em alta"], "correta": 2},
        {"pergunta": "O emoji 🤔 geralmente representa qual ação?", "alternativas": ["Pensando", "Dormindo", "Correndo"], "correta": 0},
    ],
     "Cibersegurança e Internet": [
        {"pergunta": "Como é chamado o golpe que tenta roubar dados usando mensagens ou páginas falsas?", "alternativas": ["Phishing", "Streaming", "Backup"], "correta": 0},
        {"pergunta": "Qual recurso adiciona uma segunda etapa de verificação ao login?", "alternativas": ["Modo avião", "Autenticação de dois fatores", "Bluetooth"], "correta": 1},
        {"pergunta": "Qual malware bloqueia arquivos e exige pagamento para liberá-los?", "alternativas": ["Adware", "Cookie", "Ransomware"], "correta": 2},
        {"pergunta": "Qual senha tende a ser mais segura?", "alternativas": ["Uma senha longa e única", "123456", "Seu primeiro nome"], "correta": 0},
        {"pergunta": "Qual protocolo seguro costuma aparecer no início de endereços de sites protegidos?", "alternativas": ["FTP", "HTTPS", "TXT"], "correta": 1},
    ],

    "Computadores e Informática": [
        {"pergunta": "Qual componente é frequentemente chamado de cérebro do computador?", "alternativas": ["Monitor", "Teclado", "CPU"], "correta": 2},
        {"pergunta": "Qual memória armazena temporariamente dados usados pelos programas em execução?", "alternativas": ["RAM", "HDMI", "USB"], "correta": 0},
        {"pergunta": "Qual dispositivo de armazenamento não possui partes mecânicas móveis?", "alternativas": ["Disquete", "SSD", "CD"], "correta": 1},
        {"pergunta": "Qual destes é um sistema operacional?", "alternativas": ["Google", "Firefox", "Windows"], "correta": 2},
        {"pergunta": "Qual programa é usado para acessar páginas da internet?", "alternativas": ["Navegador", "Calculadora", "Editor de áudio"], "correta": 0},
    ],

    "Celulares e Smartphones": [
        {"pergunta": "Qual empresa desenvolve o sistema Android?", "alternativas": ["Google", "Nintendo", "Adobe"], "correta": 0},
        {"pergunta": "Qual sistema operacional é usado nos iPhones?", "alternativas": ["Android", "iOS", "Windows"], "correta": 1},
        {"pergunta": "Qual tecnologia permite comunicação sem fio a curta distância entre dispositivos?", "alternativas": ["HDMI", "VGA", "Bluetooth"], "correta": 2},
        {"pergunta": "Qual tecnologia pode ser usada para pagamentos por aproximação em celulares?", "alternativas": ["NFC", "DVD", "VHS"], "correta": 0},
        {"pergunta": "Qual componente transforma a energia elétrica armazenada em alimentação para o celular?", "alternativas": ["Câmera", "Bateria", "Microfone"], "correta": 1},
    ],

    "Robôs e Tecnologia": [
        {"pergunta": "Qual componente permite que um robô perceba informações do ambiente?", "alternativas": ["Teclado", "Sensor", "Impressora"], "correta": 1},
        {"pergunta": "Qual componente pode gerar movimento em um robô?", "alternativas": ["Tela", "Microfone", "Atuador"], "correta": 2},
        {"pergunta": "Como é chamado um robô usado em linhas de produção industrial?", "alternativas": ["Robô industrial", "Satélite", "Roteador"], "correta": 0},
        {"pergunta": "Qual tecnologia permite que máquinas aprendam padrões a partir de dados?", "alternativas": ["Bluetooth", "Aprendizado de máquina", "HDMI"], "correta": 1},
        {"pergunta": "Como é chamado um veículo aéreo não tripulado controlado remotamente ou automaticamente?", "alternativas": ["Submarino", "Trator", "Drone"], "correta": 2},
    ],

    "Elementos Químicos": [
        {"pergunta": "Qual é o símbolo químico do ouro?", "alternativas": ["Ag", "Fe", "Au"], "correta": 2},
        {"pergunta": "Qual é o símbolo químico do hidrogênio?", "alternativas": ["H", "O", "He"], "correta": 0},
        {"pergunta": "Qual é o símbolo químico do oxigênio?", "alternativas": ["N", "O", "C"], "correta": 1},
        {"pergunta": "Qual é o símbolo químico do ferro?", "alternativas": ["Ir", "Fr", "Fe"], "correta": 2},
        {"pergunta": "Qual é o símbolo químico do sódio?", "alternativas": ["Na", "So", "Sd"], "correta": 0},
    ],

    "Física do Dia a Dia": [
        {"pergunta": "Qual força atrai os objetos em direção à Terra?", "alternativas": ["Gravidade", "Eletricidade", "Magnetismo"], "correta": 0},
        {"pergunta": "Qual força dificulta o deslizamento entre duas superfícies?", "alternativas": ["Empuxo", "Atrito", "Gravidade zero"], "correta": 1},
        {"pergunta": "Qual viaja mais rápido no ar?", "alternativas": ["Som", "Vento", "Luz"], "correta": 2},
        {"pergunta": "Qual é a unidade de força no Sistema Internacional?", "alternativas": ["Newton", "Joule", "Watt"], "correta": 0},
        {"pergunta": "Qual é a unidade de energia no Sistema Internacional?", "alternativas": ["Volt", "Joule", "Pascal"], "correta": 1},
    ],

    "Pedras e Minerais": [
        {"pergunta": "Qual elemento químico forma o diamante?", "alternativas": ["Ferro", "Silício", "Carbono"], "correta": 2},
        {"pergunta": "Qual mineral é formado principalmente por dióxido de silício?", "alternativas": ["Quartzo", "Talc", "Halita"], "correta": 0},
        {"pergunta": "O rubi é uma variedade de qual mineral?", "alternativas": ["Quartzo", "Coríndon", "Calcita"], "correta": 1},
        {"pergunta": "Qual mineral ocupa a posição 1 na escala de dureza de Mohs?", "alternativas": ["Diamante", "Topázio", "Talco"], "correta": 2},
        {"pergunta": "Qual mineral é amplamente utilizado na fabricação de gesso?", "alternativas": ["Gipsita", "Pirita", "Magnetita"], "correta": 0},
    ],

    "Vulcões": [
        {"pergunta": "Como é chamada a rocha derretida quando ainda está abaixo da superfície terrestre?", "alternativas": ["Lava", "Magma", "Cinza"], "correta": 1},
        {"pergunta": "Como é chamada a rocha derretida após chegar à superfície?", "alternativas": ["Magma", "Granito", "Lava"], "correta": 2},
        {"pergunta": "Ao redor de qual oceano fica o chamado Círculo de Fogo?", "alternativas": ["Pacífico", "Atlântico", "Índico"], "correta": 0},
        {"pergunta": "Em qual país fica o vulcão Vesúvio?", "alternativas": ["Grécia", "Itália", "Portugal"], "correta": 1},
        {"pergunta": "Em qual ilha italiana fica o vulcão Etna?", "alternativas": ["Sardenha", "Capri", "Sicília"], "correta": 2},
    ],

    "Montanhas Famosas": [
        {"pergunta": "Qual é a montanha mais alta do mundo acima do nível do mar?", "alternativas": ["Everest", "K2", "Kilimanjaro"], "correta": 0},
        {"pergunta": "Qual montanha é a segunda mais alta do mundo acima do nível do mar?", "alternativas": ["Aconcágua", "K2", "Monte Fuji"], "correta": 1},
        {"pergunta": "Em qual país africano fica o Monte Kilimanjaro?", "alternativas": ["Quênia", "Egito", "Tanzânia"], "correta": 2},
        {"pergunta": "Qual é a montanha mais alta da América do Sul?", "alternativas": ["Aconcágua", "Everest", "K2"], "correta": 0},
        {"pergunta": "Em qual país fica o Monte Fuji?", "alternativas": ["China", "Japão", "Coreia do Sul"], "correta": 1},
    ],

    "Rios do Mundo": [
        {"pergunta": "Em qual continente fica o rio Nilo?", "alternativas": ["Ásia", "Europa", "África"], "correta": 2},
        {"pergunta": "Qual grande rio atravessa a Floresta Amazônica?", "alternativas": ["Rio Amazonas", "Rio Danúbio", "Rio Tâmisa"], "correta": 0},
        {"pergunta": "Qual rio atravessa ou faz fronteira com vários países da Europa Central e Oriental?", "alternativas": ["Mississippi", "Danúbio", "Ganges"], "correta": 1},
        {"pergunta": "Qual grande rio atravessa os Estados Unidos de norte a sul?", "alternativas": ["Tâmisa", "Sena", "Mississippi"], "correta": 2},
        {"pergunta": "Qual rio é considerado sagrado por muitos hindus?", "alternativas": ["Ganges", "Nilo", "Reno"], "correta": 0},
    ],

    "Biomas Brasileiros": [
        {"pergunta": "Qual é o maior bioma brasileiro em extensão territorial?", "alternativas": ["Caatinga", "Amazônia", "Pampa"], "correta": 1},
        {"pergunta": "Qual bioma brasileiro é conhecido como uma grande savana tropical?", "alternativas": ["Pantanal", "Mata Atlântica", "Cerrado"], "correta": 2},
        {"pergunta": "Qual bioma é característico do semiárido nordestino?", "alternativas": ["Caatinga", "Pampa", "Amazônia"], "correta": 0},
        {"pergunta": "Qual bioma brasileiro é conhecido por suas extensas áreas sazonalmente alagadas?", "alternativas": ["Cerrado", "Pantanal", "Caatinga"], "correta": 1},
        {"pergunta": "Qual bioma brasileiro está concentrado principalmente no Rio Grande do Sul?", "alternativas": ["Amazônia", "Pantanal", "Pampa"], "correta": 2},
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
