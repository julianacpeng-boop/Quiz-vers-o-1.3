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

    "Curiosidades sobre o Sono": [
        {"pergunta": "Qual hormônio está relacionado ao controle do ciclo do sono?", "alternativas": ["Insulina", "Melatonina", "Adrenalina"], "correta": 1},
        {"pergunta": "Durante qual fase do sono os sonhos costumam ser mais intensos?", "alternativas": ["Vigília", "Sono leve inicial", "REM"], "correta": 2},
        {"pergunta": "Como é chamado o relógio biológico que regula sono e vigília?", "alternativas": ["Ritmo circadiano", "Reflexo pupilar", "Metabolismo basal"], "correta": 0},
        {"pergunta": "Qual ambiente normalmente favorece o sono?", "alternativas": ["Muito iluminado", "Escuro e silencioso", "Com televisão alta"], "correta": 1},
        {"pergunta": "Qual substância presente no café pode dificultar o sono?", "alternativas": ["Vitamina C", "Cálcio", "Cafeína"], "correta": 2},
    ],

    "Sonhos e Pesadelos": [
        {"pergunta": "Em qual fase do sono os sonhos vívidos são mais comuns?", "alternativas": ["Vigília", "Sono profundo apenas", "Sono REM"], "correta": 2},
        {"pergunta": "Como é chamado um sonho que provoca medo intenso?", "alternativas": ["Pesadelo", "Devaneio", "Reflexo"], "correta": 0},
        {"pergunta": "Qual órgão está diretamente envolvido na formação dos sonhos?", "alternativas": ["Pulmão", "Cérebro", "Estômago"], "correta": 1},
        {"pergunta": "Como é chamado o sonho no qual a pessoa percebe que está sonhando?", "alternativas": ["Sonambulismo", "Insônia", "Sonho lúcido"], "correta": 2},
        {"pergunta": "Pesadelos podem ocorrer com maior frequência após períodos de quê?", "alternativas": ["Estresse", "Beber água", "Comer cenoura"], "correta": 0},
    ],

    "Memória e Inteligência": [
        {"pergunta": "Qual parte do cérebro tem papel importante na formação de novas memórias?", "alternativas": ["Hipocampo", "Pâncreas", "Medula óssea"], "correta": 0},
        {"pergunta": "Como é chamada a memória que mantém informações por pouco tempo?", "alternativas": ["Memória genética", "Memória muscular", "Memória de curto prazo"], "correta": 2},
        {"pergunta": "Qual atividade ajuda a exercitar a memória?", "alternativas": ["Nunca aprender nada novo", "Resolver desafios mentais", "Dormir zero horas"], "correta": 1},
        {"pergunta": "Aprender uma nova habilidade envolve principalmente qual órgão?", "alternativas": ["Cérebro", "Rim", "Fígado"], "correta": 0},
        {"pergunta": "A repetição pode ajudar em qual processo?", "alternativas": ["Digestão", "Respiração", "Memorização"], "correta": 2},
    ],

    "Emoções do Corpo Humano": [
        {"pergunta": "Qual emoção pode aumentar os batimentos cardíacos?", "alternativas": ["Sono profundo", "Medo", "Tédio"], "correta": 1},
        {"pergunta": "Qual substância está associada à resposta de luta ou fuga?", "alternativas": ["Queratina", "Melanina", "Adrenalina"], "correta": 2},
        {"pergunta": "Qual parte do rosto costuma se elevar quando sorrimos?", "alternativas": ["Bochechas", "Queixo", "Orelhas"], "correta": 0},
        {"pergunta": "Qual emoção frequentemente está associada ao choro?", "alternativas": ["Equilíbrio", "Tristeza", "Fome"], "correta": 1},
        {"pergunta": "Qual órgão participa diretamente do processamento das emoções?", "alternativas": ["Pulmão", "Fígado", "Cérebro"], "correta": 2},
    ],

    "Hábitos Estranhos do Corpo": [
        {"pergunta": "O mecanismo exato do bocejo é totalmente compreendido pela ciência?", "alternativas": ["Não", "Sim, completamente", "Só durante o sono"], "correta": 0},
        {"pergunta": "O que normalmente causa soluços?", "alternativas": ["Movimento dos ossos", "Contrações involuntárias do diafragma", "Crescimento do cabelo"], "correta": 1},
        {"pergunta": "Por que os pelos ficam arrepiados quando sentimos frio?", "alternativas": ["Os ossos encolhem", "A pele desliga", "Pequenos músculos ligados aos pelos se contraem"], "correta": 2},
        {"pergunta": "O que acontece durante um espirro?", "alternativas": ["O ar é expulso rapidamente pelas vias respiratórias", "O coração para por minutos", "Os pulmões deixam de funcionar"], "correta": 0},
        {"pergunta": "Por que piscamos várias vezes por minuto?", "alternativas": ["Para ajudar na digestão", "Para lubrificar e proteger os olhos", "Para aumentar a visão à distância"], "correta": 1},
    ],

    "Coisas que o Cérebro Faz sem Você Perceber": [
        {"pergunta": "Qual função o cérebro ajuda a controlar automaticamente?", "alternativas": ["Cor do cabelo", "Tamanho do pé", "Respiração"], "correta": 2},
        {"pergunta": "O cérebro continua funcionando enquanto dormimos?", "alternativas": ["Sim", "Não", "Somente quando sonhamos"], "correta": 0},
        {"pergunta": "Qual ação pode ocorrer sem pensamento consciente?", "alternativas": ["Escrever uma redação", "Reflexo", "Resolver uma equação"], "correta": 1},
        {"pergunta": "Qual estrutura ajuda a controlar respiração e frequência cardíaca?", "alternativas": ["Fêmur", "Pele", "Tronco encefálico"], "correta": 2},
        {"pergunta": "O cérebro recebe continuamente informações dos sentidos?", "alternativas": ["Sim", "Não", "Somente durante o sono"], "correta": 0},
    ],

    "Alimentos que Enganam": [
        {"pergunta": "Botanicamente, o tomate é classificado como quê?", "alternativas": ["Raiz", "Fruto", "Folha"], "correta": 1},
        {"pergunta": "Qual destes é botanicamente um fruto apesar de ser usado como legume?", "alternativas": ["Batata", "Cenoura", "Pepino"], "correta": 2},
        {"pergunta": "O amendoim pertence a qual grupo?", "alternativas": ["Leguminosas", "Tubérculos", "Frutas cítricas"], "correta": 0},
        {"pergunta": "Qual destas é botanicamente considerada uma baga?", "alternativas": ["Morango", "Banana", "Maçã"], "correta": 1},
        {"pergunta": "A batata que normalmente comemos é qual parte da planta?", "alternativas": ["Fruto", "Folha", "Tubérculo"], "correta": 2},
    ],

    "Curiosidades sobre Chocolate": [
        {"pergunta": "De qual planta vem o ingrediente principal do chocolate?", "alternativas": ["Cacaueiro", "Cafeeiro", "Oliveira"], "correta": 0},
        {"pergunta": "Qual tipo de chocolate geralmente possui maior teor de cacau?", "alternativas": ["Chocolate branco", "Chocolate ao leite", "Chocolate amargo"], "correta": 2},
        {"pergunta": "Qual ingrediente é característico do chocolate branco?", "alternativas": ["Café", "Manteiga de cacau", "Caramelo"], "correta": 1},
        {"pergunta": "De qual parte do fruto do cacau é produzido o chocolate?", "alternativas": ["Sementes", "Folhas", "Raízes"], "correta": 0},
        {"pergunta": "O cacaueiro se desenvolve melhor principalmente em qual clima?", "alternativas": ["Polar", "Desértico", "Tropical"], "correta": 2},
    ],

    "Curiosidades sobre Café": [
        {"pergunta": "Qual substância estimulante existe naturalmente no café?", "alternativas": ["Vitamina D", "Cafeína", "Colágeno"], "correta": 1},
        {"pergunta": "O café é produzido principalmente a partir de quê?", "alternativas": ["Folhas", "Raízes", "Sementes do fruto"], "correta": 2},
        {"pergunta": "Qual país é um dos maiores produtores mundiais de café?", "alternativas": ["Brasil", "Islândia", "Groenlândia"], "correta": 0},
        {"pergunta": "Qual destes é um tipo conhecido de café?", "alternativas": ["Cedro", "Arábica", "Granito"], "correta": 1},
        {"pergunta": "A torra influencia principalmente quais características do café?", "alternativas": ["Número de grãos", "Altura da planta", "Aroma e sabor"], "correta": 2},
    ],

    "Temperos do Mundo": [
        {"pergunta": "Qual tempero amarelo é muito usado na culinária indiana?", "alternativas": ["Cúrcuma", "Açúcar", "Baunilha"], "correta": 0},
        {"pergunta": "Qual erva é um dos principais ingredientes do pesto tradicional?", "alternativas": ["Alecrim", "Coentro", "Manjericão"], "correta": 2},
        {"pergunta": "Qual especiaria é obtida da casca de uma árvore?", "alternativas": ["Cravo", "Canela", "Pimenta"], "correta": 1},
        {"pergunta": "Qual especiaria é formada por botões florais secos?", "alternativas": ["Cravo-da-índia", "Noz-moscada", "Cominho"], "correta": 0},
        {"pergunta": "Qual tempero é produzido a partir dos frutos secos de uma planta do gênero Piper?", "alternativas": ["Sal", "Canela", "Pimenta-do-reino"], "correta": 2},
    ],

    "Comidas com Nomes Estranhos": [
        {"pergunta": "O que é um escondidinho?", "alternativas": ["Uma bebida", "Um prato com purê e recheio", "Um biscoito"], "correta": 1},
        {"pergunta": "O arrumadinho é tradicionalmente associado a qual região brasileira?", "alternativas": ["Sul", "Centro-Oeste", "Nordeste"], "correta": 2},
        {"pergunta": "Qual doce leva ameixa e coco e tem um nome curioso?", "alternativas": ["Olho de sogra", "Pé de moleque", "Quindim"], "correta": 0},
        {"pergunta": "Qual doce tradicional é preparado principalmente com amendoim e açúcar ou rapadura?", "alternativas": ["Brigadeiro", "Pé de moleque", "Maria-mole"], "correta": 1},
        {"pergunta": "Qual doce possui textura macia e leva claras, açúcar e gelatina em muitas receitas?", "alternativas": ["Paçoca", "Rapadura", "Maria-mole"], "correta": 2},
    ],

    "Frutas que Parecem Outras Coisas": [
        {"pergunta": "Qual fruta cortada transversalmente lembra uma estrela?", "alternativas": ["Carambola", "Banana", "Maçã"], "correta": 0},
        {"pergunta": "Qual fruta possui casca formada por segmentos que lembram escamas?", "alternativas": ["Uva", "Melancia", "Pinha"], "correta": 2},
        {"pergunta": "Qual fruta possui uma grande casca verde e espinhosa?", "alternativas": ["Pera", "Jaca", "Ameixa"], "correta": 1},
        {"pergunta": "Qual fruta frequentemente possui formato semelhante a um coração?", "alternativas": ["Morango", "Limão", "Banana"], "correta": 0},
        {"pergunta": "Qual fruta também é conhecida como fruta-do-dragão?", "alternativas": ["Caju", "Mamão", "Pitaya"], "correta": 2},
    ],

    "Animais com Habilidades Incríveis": [
        {"pergunta": "Qual animal é famoso por mudar de cor?", "alternativas": ["Galinha", "Camaleão", "Cavalo"], "correta": 1},
        {"pergunta": "Qual animal consegue regenerar braços perdidos em determinadas condições?", "alternativas": ["Cachorro", "Pombo", "Estrela-do-mar"], "correta": 2},
        {"pergunta": "Qual animal utiliza ecolocalização para se orientar?", "alternativas": ["Morcego", "Girafa", "Elefante"], "correta": 0},
        {"pergunta": "Qual ave consegue pairar no ar batendo rapidamente as asas?", "alternativas": ["Pinguim", "Beija-flor", "Avestruz"], "correta": 1},
        {"pergunta": "Qual animal pode liberar tinta para confundir predadores?", "alternativas": ["Golfinho", "Cavalo-marinho", "Polvo"], "correta": 2},
    ],

    "Animais Mais Inteligentes": [
        {"pergunta": "Qual molusco é conhecido por resolver problemas complexos?", "alternativas": ["Polvo", "Ostra", "Mexilhão"], "correta": 0},
        {"pergunta": "Qual mamífero marinho apresenta comunicação e comportamento social complexos?", "alternativas": ["Caranguejo", "Sardinha", "Golfinho"], "correta": 2},
        {"pergunta": "Qual ave é conhecida por conseguir utilizar ferramentas?", "alternativas": ["Pato", "Corvo", "Galinha"], "correta": 1},
        {"pergunta": "Qual primata é muito estudado por sua capacidade cognitiva?", "alternativas": ["Chimpanzé", "Coelho", "Capivara"], "correta": 0},
        {"pergunta": "Qual grande mamífero é famoso por sua memória e complexa vida social?", "alternativas": ["Zebra", "Antílope", "Elefante"], "correta": 2},
    ],

    "Animais Mais Rápidos": [
        {"pergunta": "Qual animal terrestre é famoso por sua enorme velocidade?", "alternativas": ["Elefante", "Guepardo", "Hipopótamo"], "correta": 1},
        {"pergunta": "Qual ave pode atingir velocidades extremas durante mergulhos?", "alternativas": ["Pombo", "Pato", "Falcão-peregrino"], "correta": 2},
        {"pergunta": "Qual destes peixes é conhecido por alcançar grandes velocidades?", "alternativas": ["Agulhão-vela", "Ostra", "Estrela-do-mar"], "correta": 0},
        {"pergunta": "Qual animal africano utiliza sua velocidade para fugir de predadores?", "alternativas": ["Preguiça", "Gazela", "Tartaruga"], "correta": 1},
        {"pergunta": "Qual grande ave terrestre é uma excelente corredora?", "alternativas": ["Pinguim", "Canário", "Avestruz"], "correta": 2},
    ],

    "Animais Mais Perigosos": [
        {"pergunta": "Qual animal é responsável pela transmissão de doenças como dengue e malária?", "alternativas": ["Mosquito", "Girafa", "Coelho"], "correta": 0},
        {"pergunta": "Qual grande réptil possui uma mordida extremamente forte?", "alternativas": ["Tartaruga", "Lagartixa", "Crocodilo"], "correta": 2},
        {"pergunta": "Qual animal marinho possui espécies com venenos extremamente potentes?", "alternativas": ["Sardinha", "Água-viva", "Baleia"], "correta": 1},
        {"pergunta": "Qual grande mamífero africano pode ser bastante territorial e perigoso?", "alternativas": ["Hipopótamo", "Coelho", "Gazela"], "correta": 0},
        {"pergunta": "Qual serpente é conhecida pelo potente veneno neurotóxico?", "alternativas": ["Jiboia", "Sucuri", "Cobra-real"], "correta": 2},
    ],

    "Animais com Aparência Estranha": [
        {"pergunta": "Qual primata é famoso pelo nariz muito grande?", "alternativas": ["Gorila", "Macaco-narigudo", "Chimpanzé"], "correta": 1},
        {"pergunta": "Qual peixe das profundezas utiliza uma estrutura luminosa para atrair presas?", "alternativas": ["Sardinha", "Tilápia", "Peixe-pescador"], "correta": 2},
        {"pergunta": "Qual mamífero possui um bico semelhante ao de um pato?", "alternativas": ["Ornitorrinco", "Coelho", "Capivara"], "correta": 0},
        {"pergunta": "Qual animal possui uma cabeça que lembra a de um cavalo?", "alternativas": ["Tubarão", "Cavalo-marinho", "Golfinho"], "correta": 1},
        {"pergunta": "Qual anfíbio é famoso por suas brânquias externas?", "alternativas": ["Sapo", "Rã", "Axolote"], "correta": 2},
    ],

    "Animais que Mudam de Cor": [
        {"pergunta": "Qual réptil é famoso por alterar sua coloração?", "alternativas": ["Camaleão", "Jabuti", "Crocodilo"], "correta": 0},
        {"pergunta": "Qual animal marinho pode alterar rapidamente cor e padrões da pele?", "alternativas": ["Golfinho", "Baleia", "Polvo"], "correta": 2},
        {"pergunta": "Qual molusco é especialmente conhecido por mudar sua aparência rapidamente?", "alternativas": ["Ostra", "Sépia", "Mexilhão"], "correta": 1},
        {"pergunta": "A mudança de cor pode ajudar determinados animais principalmente em quê?", "alternativas": ["Camuflagem", "Criar asas", "Aumentar o tamanho"], "correta": 0},
        {"pergunta": "Além da camuflagem, a mudança de cor do camaleão pode estar ligada a quê?", "alternativas": ["Número de patas", "Comprimento da cauda", "Temperatura e comunicação"], "correta": 2},
    ],

    "Animais que Dormem de Jeitos Estranhos": [
        {"pergunta": "Qual animal costuma dormir pendurado de cabeça para baixo?", "alternativas": ["Elefante", "Morcego", "Cavalo"], "correta": 1},
        {"pergunta": "Qual animal pode manter uma parte do cérebro mais ativa enquanto dorme?", "alternativas": ["Coelho", "Capivara", "Golfinho"], "correta": 2},
        {"pergunta": "Qual animal passa muitas horas do dia dormindo?", "alternativas": ["Coala", "Girafa", "Cavalo"], "correta": 0},
        {"pergunta": "Qual ave é famosa por permanecer apoiada em uma perna?", "alternativas": ["Águia", "Flamingo", "Avestruz"], "correta": 1},
        {"pergunta": "Qual grande mamífero pode cochilar em pé?", "alternativas": ["Polvo", "Peixe", "Cavalo"], "correta": 2},
    ],

    "Filhotes de Animais": [
        {"pergunta": "Como é chamado o filhote do cavalo?", "alternativas": ["Potro", "Bezerro", "Leitão"], "correta": 0},
        {"pergunta": "Como é chamado o filhote da vaca?", "alternativas": ["Cordeiro", "Potro", "Bezerro"], "correta": 2},
        {"pergunta": "Como é chamado o filhote da galinha?", "alternativas": ["Cabrito", "Pintinho", "Leitão"], "correta": 1},
        {"pergunta": "Como é chamado o filhote da ovelha?", "alternativas": ["Cordeiro", "Potro", "Bezerro"], "correta": 0},
        {"pergunta": "Como é chamado o filhote do porco?", "alternativas": ["Cordeiro", "Cabrito", "Leitão"], "correta": 2},
    ],

    "Sons dos Animais": [
        {"pergunta": "Qual animal mia?", "alternativas": ["Cachorro", "Gato", "Cavalo"], "correta": 1},
        {"pergunta": "Qual animal late?", "alternativas": ["Gato", "Vaca", "Cachorro"], "correta": 2},
        {"pergunta": "Qual animal relincha?", "alternativas": ["Cavalo", "Pato", "Galinha"], "correta": 0},
        {"pergunta": "Qual animal muge?", "alternativas": ["Leão", "Vaca", "Macaco"], "correta": 1},
        {"pergunta": "Qual animal ruge?", "alternativas": ["Coelho", "Pomba", "Leão"], "correta": 2},
    ],

    "Pegadas de Animais": [
        {"pergunta": "Qual animal costuma deixar marcas de patas com quatro dedos e almofadas?", "alternativas": ["Cachorro", "Cavalo", "Pato"], "correta": 0},
        {"pergunta": "Qual animal deixa uma marca característica de casco?", "alternativas": ["Gato", "Pato", "Cavalo"], "correta": 2},
        {"pergunta": "Qual ave costuma deixar pegadas com membranas entre os dedos?", "alternativas": ["Águia", "Pato", "Canário"], "correta": 1},
        {"pergunta": "Qual grande felino pode deixar pegadas semelhantes às de um gato, mas muito maiores?", "alternativas": ["Onça", "Capivara", "Tamanduá"], "correta": 0},
        {"pergunta": "O estudo de pegadas permite identificar principalmente o quê?", "alternativas": ["A idade das árvores", "A temperatura", "Animais que passaram pelo local"], "correta": 2},
    ],

    "O Mundo dos Insetos": [
        {"pergunta": "Quantas pernas possui normalmente um inseto adulto?", "alternativas": ["8", "6", "10"], "correta": 1},
        {"pergunta": "Qual inseto é conhecido por produzir mel?", "alternativas": ["Mosquito", "Barata", "Abelha"], "correta": 2},
        {"pergunta": "Qual inseto passa por uma fase de lagarta?", "alternativas": ["Borboleta", "Gafanhoto", "Formiga adulta"], "correta": 0},
        {"pergunta": "Qual inseto forma colônias com rainhas e operárias?", "alternativas": ["Libélula", "Formiga", "Mosca"], "correta": 1},
        {"pergunta": "Qual inseto produz luz em algumas espécies?", "alternativas": ["Mosquito", "Pulga", "Vaga-lume"], "correta": 2},
    ],

    "Aranhas e Escorpiões": [
        {"pergunta": "Quantas patas possui normalmente uma aranha?", "alternativas": ["8", "6", "10"], "correta": 0},
        {"pergunta": "Aranhas pertencem a qual grupo?", "alternativas": ["Insetos", "Moluscos", "Aracnídeos"], "correta": 2},
        {"pergunta": "Em qual parte do escorpião fica o ferrão?", "alternativas": ["Cabeça", "Extremidade da cauda", "Pinça"], "correta": 1},
        {"pergunta": "Qual destes animais possui grandes pinças na parte frontal do corpo?", "alternativas": ["Escorpião", "Borboleta", "Mosquito"], "correta": 0},
        {"pergunta": "Aranhas possuem antenas?", "alternativas": ["Sim, duas", "Sim, quatro", "Não"], "correta": 2},
    ],

    "Cobras Curiosas": [
        {"pergunta": "Qual grande serpente brasileira vive frequentemente próxima da água?", "alternativas": ["Cascavel", "Sucuri", "Coral"], "correta": 1},
        {"pergunta": "Qual cobra possui um chocalho na cauda?", "alternativas": ["Jiboia", "Sucuri", "Cascavel"], "correta": 2},
        {"pergunta": "Qual serpente mata suas presas principalmente por constrição?", "alternativas": ["Jiboia", "Cobra-coral", "Cascavel"], "correta": 0},
        {"pergunta": "Qual estrutura ajuda as serpentes a captar partículas químicas do ambiente?", "alternativas": ["Patas", "Língua bifurcada", "Orelhas externas"], "correta": 1},
        {"pergunta": "As cobras possuem pálpebras móveis?", "alternativas": ["Sim", "Somente filhotes", "Não"], "correta": 2},
    ],

    "Tubarões e Predadores do Mar": [
        {"pergunta": "Qual tubarão possui cabeça característica em formato de martelo?", "alternativas": ["Tubarão-martelo", "Tubarão-branco", "Tubarão-lixa"], "correta": 0},
        {"pergunta": "Qual grande tubarão é famoso por seus dentes triangulares serrilhados?", "alternativas": ["Tubarão-baleia", "Tubarão-lixa", "Tubarão-branco"], "correta": 2},
        {"pergunta": "Qual mamífero marinho é um poderoso predador e caça cooperativamente?", "alternativas": ["Cavalo-marinho", "Orca", "Peixe-palhaço"], "correta": 1},
        {"pergunta": "O esqueleto dos tubarões é formado principalmente por quê?", "alternativas": ["Cartilagem", "Conchas", "Ossos densos"], "correta": 0},
        {"pergunta": "Qual é o maior peixe conhecido atualmente?", "alternativas": ["Atum", "Tubarão-branco", "Tubarão-baleia"], "correta": 2},
    ],

    "Baleias e Golfinhos": [
        {"pergunta": "Baleias pertencem a qual grupo?", "alternativas": ["Peixes", "Mamíferos", "Répteis"], "correta": 1},
        {"pergunta": "Golfinhos respiram usando qual órgão?", "alternativas": ["Brânquias", "Pele", "Pulmões"], "correta": 2},
        {"pergunta": "Qual é o maior animal conhecido atualmente?", "alternativas": ["Baleia-azul", "Elefante", "Orca"], "correta": 0},
        {"pergunta": "Como é chamada a abertura respiratória no topo da cabeça de baleias?", "alternativas": ["Barbatana", "Espiráculo", "Brânquia"], "correta": 1},
        {"pergunta": "Qual recurso os golfinhos podem utilizar para localizar objetos?", "alternativas": ["Fotossíntese", "Visão de raios X", "Ecolocalização"], "correta": 2},
    ],

    "Criaturas das Profundezas do Oceano": [
        {"pergunta": "Qual peixe utiliza uma estrutura luminosa para atrair presas?", "alternativas": ["Peixe-pescador", "Sardinha", "Atum"], "correta": 0},
        {"pergunta": "Como é chamada a produção de luz por organismos vivos?", "alternativas": ["Fotossíntese", "Evaporação", "Bioluminescência"], "correta": 2},
        {"pergunta": "Por que alguns animais das profundezas possuem olhos muito grandes?", "alternativas": ["Para respirar", "Para aproveitar a pouca luz", "Para produzir calor"], "correta": 1},
        {"pergunta": "Qual condição aumenta muito com a profundidade no oceano?", "alternativas": ["Pressão", "Quantidade de luz", "Temperatura sempre"], "correta": 0},
        {"pergunta": "Qual molusco das profundezas pode atingir tamanho enorme?", "alternativas": ["Ostra", "Mexilhão", "Lula-gigante"], "correta": 2},
    ],

    "Ilhas Misteriosas": [
        {"pergunta": "Qual ilha é famosa pelas enormes estátuas chamadas moais?", "alternativas": ["Madagascar", "Ilha de Páscoa", "Islândia"], "correta": 1},
        {"pergunta": "Qual ilha japonesa abandonada também é conhecida como Battleship Island?", "alternativas": ["Okinawa", "Hokkaido", "Hashima"], "correta": 2},
        {"pergunta": "Qual arquipélago ajudou Charles Darwin em suas observações sobre evolução?", "alternativas": ["Galápagos", "Malta", "Sicília"], "correta": 0},
        {"pergunta": "Qual ilha japonesa ficou conhecida por possuir muitos gatos?", "alternativas": ["Creta", "Aoshima", "Groenlândia"], "correta": 1},
        {"pergunta": "Em qual oceano fica a Ilha de Páscoa?", "alternativas": ["Atlântico", "Índico", "Pacífico"], "correta": 2},
    ],

    "Cidades Mais Curiosas do Mundo": [
        {"pergunta": "Qual cidade italiana é famosa por seus canais e gôndolas?", "alternativas": ["Veneza", "Roma", "Milão"], "correta": 0},
        {"pergunta": "Em qual cidade está a famosa Torre Inclinada?", "alternativas": ["Paris", "Roma", "Pisa"], "correta": 2},
        {"pergunta": "Qual cidade está localizada em dois continentes?", "alternativas": ["Lisboa", "Istambul", "Lima"], "correta": 1},
        {"pergunta": "Qual cidade possui o edifício Burj Khalifa?", "alternativas": ["Dubai", "Sydney", "Roma"], "correta": 0},
        {"pergunta": "Qual cidade é famosa por possuir a Praça de São Marcos e canais?", "alternativas": ["Florença", "Madri", "Veneza"], "correta": 2},
    ],

    "Lugares com Nomes Estranhos": [
        {"pergunta": "Em qual estado fica o município de Não-Me-Toque?", "alternativas": ["Paraná", "Rio Grande do Sul", "Bahia"], "correta": 1},
        {"pergunta": "Em qual estado brasileiro fica o município de Feliz?", "alternativas": ["Minas Gerais", "Goiás", "Rio Grande do Sul"], "correta": 2},
        {"pergunta": "Venha-Ver é um município de qual estado brasileiro?", "alternativas": ["Rio Grande do Norte", "Paraná", "Bahia"], "correta": 0},
        {"pergunta": "Passa e Fica pertence a qual estado?", "alternativas": ["Paraíba", "Rio Grande do Norte", "Ceará"], "correta": 1},
        {"pergunta": "Anta Gorda é um município de qual estado?", "alternativas": ["Amazonas", "Bahia", "Rio Grande do Sul"], "correta": 2},
    ],

    "Fronteiras Curiosas entre Países": [
        {"pergunta": "Qual destes países faz fronteira com o Brasil?", "alternativas": ["Bolívia", "Portugal", "México"], "correta": 0},
        {"pergunta": "Qual país está completamente cercado pela África do Sul?", "alternativas": ["Egito", "Marrocos", "Lesoto"], "correta": 2},
        {"pergunta": "Qual pequeno país está completamente cercado pela Itália?", "alternativas": ["Portugal", "San Marino", "Bélgica"], "correta": 1},
        {"pergunta": "Qual país independente está localizado dentro da cidade de Roma?", "alternativas": ["Vaticano", "Mônaco", "Andorra"], "correta": 0},
        {"pergunta": "Estados Unidos e Canadá compartilham o quê?", "alternativas": ["Nenhuma fronteira", "Somente fronteira marítima", "Uma extensa fronteira terrestre"], "correta": 2},
    ],

    "Países Pequenos do Mundo": [
        {"pergunta": "Qual é o menor país do mundo em área?", "alternativas": ["Mônaco", "Vaticano", "Malta"], "correta": 1},
        {"pergunta": "Qual pequeno país é famoso pelo cassino de Monte Carlo?", "alternativas": ["Andorra", "Luxemburgo", "Mônaco"], "correta": 2},
        {"pergunta": "Qual pequeno país fica entre França e Espanha?", "alternativas": ["Andorra", "Malta", "San Marino"], "correta": 0},
        {"pergunta": "Qual país está localizado dentro de Roma?", "alternativas": ["Liechtenstein", "Vaticano", "Mônaco"], "correta": 1},
        {"pergunta": "Qual pequeno país fica entre a Suíça e a Áustria?", "alternativas": ["Malta", "Chipre", "Liechtenstein"], "correta": 2},
    ],

    "Países com Curiosidades Inacreditáveis": [
        {"pergunta": "Qual país é formado por milhares de ilhas?", "alternativas": ["Indonésia", "Suíça", "Paraguai"], "correta": 0},
        {"pergunta": "Qual país é conhecido como Terra do Sol Nascente?", "alternativas": ["Canadá", "México", "Japão"], "correta": 2},
        {"pergunta": "Qual país possui uma folha de bordo em sua bandeira?", "alternativas": ["Chile", "Canadá", "Peru"], "correta": 1},
        {"pergunta": "Qual país possui formato frequentemente comparado a uma bota?", "alternativas": ["Itália", "Noruega", "Índia"], "correta": 0},
        {"pergunta": "Qual país é famoso por seus numerosos fiordes?", "alternativas": ["Egito", "Uruguai", "Noruega"], "correta": 2},
    ],

    "Costumes Estranhos pelo Mundo": [
        {"pergunta": "Em qual país retirar os sapatos antes de entrar em casa é um costume bastante comum?", "alternativas": ["Brasil", "Japão", "México"], "correta": 1},
        {"pergunta": "Qual país é muito associado ao cumprimento por meio de reverências?", "alternativas": ["Argentina", "Canadá", "Japão"], "correta": 2},
        {"pergunta": "O tradicional chá da tarde é fortemente associado a qual país?", "alternativas": ["Reino Unido", "Chile", "Brasil"], "correta": 0},
        {"pergunta": "Qual país é especialmente conhecido por sua cultura de saunas?", "alternativas": ["Egito", "Finlândia", "México"], "correta": 1},
        {"pergunta": "Em qual país existe a tradição de comer doze uvas na virada do ano?", "alternativas": ["Japão", "Canadá", "Espanha"], "correta": 2},
    ],

    "Leis Curiosas pelo Mundo": [
        {"pergunta": "As leis são iguais em todos os países?", "alternativas": ["Não", "Sim", "Somente na Europa"], "correta": 0},
        {"pergunta": "Antes de viajar para outro país, o que é importante conhecer?", "alternativas": ["Somente o clima", "Somente a moeda", "Leis e regras locais"], "correta": 2},
        {"pergunta": "Algo permitido em um país pode ser proibido em outro?", "alternativas": ["Nunca", "Sim", "Somente em ilhas"], "correta": 1},
        {"pergunta": "As leis podem sofrer alterações ao longo do tempo?", "alternativas": ["Sim", "Não", "Apenas a cada 100 anos"], "correta": 0},
        {"pergunta": "Quem deve respeitar as leis locais durante uma viagem?", "alternativas": ["Somente moradores", "Somente autoridades", "Também os visitantes"], "correta": 2},
    ],

    "Objetos que Você Usa e Não Sabe o Nome": [
        {"pergunta": "Como é chamada a pequena peça que protege a ponta do cadarço?", "alternativas": ["Arruela", "Ponteira", "Rolamento"], "correta": 1},
        {"pergunta": "Qual peça permite que uma porta gire ao abrir e fechar?", "alternativas": ["Puxador", "Trinco", "Dobradiça"], "correta": 2},
        {"pergunta": "Como é chamada a peça usada para puxar o cursor de um zíper?", "alternativas": ["Puxador", "Botão", "Fivela"], "correta": 0},
        {"pergunta": "Qual peça de borracha pode ser colocada na extremidade de uma perna de cadeira?", "alternativas": ["Porca", "Ponteira", "Rolha"], "correta": 1},
        {"pergunta": "Como é chamada a parte de uma garrafa pela qual o líquido sai?", "alternativas": ["Base", "Fundo", "Gargalo"], "correta": 2},
    ],

    "Para que Serve Isso?": [
        {"pergunta": "Para que serve um nível de bolha?", "alternativas": ["Verificar nivelamento", "Medir temperatura", "Medir peso"], "correta": 0},
        {"pergunta": "Para que serve uma bússola?", "alternativas": ["Medir pressão", "Cortar papel", "Indicar direções"], "correta": 2},
        {"pergunta": "Para que serve um paquímetro?", "alternativas": ["Medir som", "Medir dimensões com precisão", "Medir luminosidade"], "correta": 1},
        {"pergunta": "Para que serve um funil?", "alternativas": ["Facilitar a transferência de líquidos", "Medir velocidade", "Ampliar sons"], "correta": 0},
        {"pergunta": "Para que serve uma lupa?", "alternativas": ["Medir corrente", "Aquecer alimentos", "Ampliar visualmente objetos"], "correta": 2},
    ],

    "Coisas Inventadas por Acidente": [
        {"pergunta": "Qual medicamento foi descoberto após Fleming observar um fungo em uma cultura?", "alternativas": ["Aspirina", "Penicilina", "Insulina"], "correta": 1},
        {"pergunta": "Qual produto surgiu de um adesivo que não grudava com muita força?", "alternativas": ["Supercola", "Fita isolante", "Post-it"], "correta": 2},
        {"pergunta": "Qual aparelho surgiu após observações sobre aquecimento provocado por micro-ondas?", "alternativas": ["Forno de micro-ondas", "Geladeira", "Liquidificador"], "correta": 0},
        {"pergunta": "Qual alimento ficou associado à história de batatas cortadas extremamente finas e fritas?", "alternativas": ["Purê", "Batata chips", "Pão"], "correta": 1},
        {"pergunta": "Qual invenção foi inspirada por sementes que grudavam em roupas e pelos?", "alternativas": ["Botão", "Zíper", "Velcro"], "correta": 2},
    ],

    "Produtos que Mudaram com o Tempo": [
        {"pergunta": "Qual aparelho evoluiu de modelos de disco para smartphones?", "alternativas": ["Telefone", "Geladeira", "Liquidificador"], "correta": 0},
        {"pergunta": "Qual mídia doméstica foi amplamente substituída pelo DVD?", "alternativas": ["CD de música", "Disquete", "VHS"], "correta": 2},
        {"pergunta": "Qual aparelho passou de grandes telas de tubo para modelos muito finos?", "alternativas": ["Máquina de escrever", "Televisão", "Ventilador"], "correta": 1},
        {"pergunta": "Qual formato musical foi muito popular antes dos serviços de streaming?", "alternativas": ["CD", "VHS", "Fax"], "correta": 0},
        {"pergunta": "Qual aparelho substituiu amplamente a máquina de escrever na produção de textos?", "alternativas": ["Fogão", "Bússola", "Computador"], "correta": 2},
    ],

    "Tecnologias que Pareciam Impossíveis": [
        {"pergunta": "Qual tecnologia permite conversar por vídeo com alguém distante?", "alternativas": ["Telégrafo", "Videoconferência", "Máquina a vapor"], "correta": 1},
        {"pergunta": "Qual sistema permite determinar localização usando sinais de satélites?", "alternativas": ["FM", "VHS", "GPS"], "correta": 2},
        {"pergunta": "Qual tecnologia produz objetos físicos camada por camada?", "alternativas": ["Impressão 3D", "Fax", "Rádio"], "correta": 0},
        {"pergunta": "Qual tecnologia permite controlar dispositivos através da fala?", "alternativas": ["Disquete", "Assistente de voz", "Fita cassete"], "correta": 1},
        {"pergunta": "Qual tecnologia permite que veículos realizem parte da condução automaticamente?", "alternativas": ["Telégrafo", "Máquina de escrever", "Direção automatizada"], "correta": 2},
    ],

    "Erros que Viraram Grandes Descobertas": [
        {"pergunta": "Qual antibiótico foi descoberto após uma contaminação acidental de uma cultura?", "alternativas": ["Penicilina", "Paracetamol", "Morfina"], "correta": 0},
        {"pergunta": "Qual aparelho teve seu desenvolvimento ligado à descoberta do aquecimento por micro-ondas?", "alternativas": ["Geladeira", "Ventilador", "Forno de micro-ondas"], "correta": 2},
        {"pergunta": "Qual produto surgiu após a criação de um adesivo mais fraco que o planejado?", "alternativas": ["Clips", "Post-it", "Grampeador"], "correta": 1},
        {"pergunta": "Qual invenção foi inspirada em sementes que grudavam em roupas?", "alternativas": ["Velcro", "Vidro", "Botão"], "correta": 0},
        {"pergunta": "Na ciência, resultados inesperados podem levar a quê?", "alternativas": ["Nada útil", "Erros obrigatoriamente", "Novas descobertas"], "correta": 2},
    ],

    "Perguntas que Parecem Fáceis, Mas Não São": [
        {"pergunta": "Quantos meses do ano possuem pelo menos 28 dias?", "alternativas": ["1", "12", "6"], "correta": 1},
        {"pergunta": "Se você tinha três maçãs e pegou duas delas, quantas maçãs você pegou?", "alternativas": ["1", "3", "2"], "correta": 2},
        {"pergunta": "Onde são enterrados os sobreviventes de um acidente?", "alternativas": ["Sobreviventes não são enterrados", "No local do acidente", "Na cidade mais próxima"], "correta": 0},
        {"pergunta": "O que pesa mais: 1 kg de ferro ou 1 kg de algodão?", "alternativas": ["Ferro", "Pesam igual", "Algodão"], "correta": 1},
        {"pergunta": "Quantos animais Moisés levou para a arca?", "alternativas": ["Dois de cada", "Sete de cada", "Nenhum, a arca era de Noé"], "correta": 2},
    ],

    "Qual Você Acha que é Maior?": [
        {"pergunta": "Qual destes animais é maior em massa?", "alternativas": ["Baleia-azul", "Elefante-africano", "Girafa"], "correta": 0},
        {"pergunta": "Qual destes planetas é maior?", "alternativas": ["Terra", "Marte", "Júpiter"], "correta": 2},
        {"pergunta": "Qual é o maior oceano?", "alternativas": ["Atlântico", "Pacífico", "Índico"], "correta": 1},
        {"pergunta": "Qual destes países possui maior área territorial?", "alternativas": ["Rússia", "Brasil", "Índia"], "correta": 0},
        {"pergunta": "Qual destes animais terrestres normalmente possui maior massa?", "alternativas": ["Girafa", "Leão", "Elefante-africano"], "correta": 2},
    ],

    "Você Sabe para que Isso Serve?": [
        {"pergunta": "Para que serve um extintor de incêndio?", "alternativas": ["Medir temperatura", "Combater princípios de incêndio", "Gerar energia"], "correta": 1},
        {"pergunta": "Para que serve um termômetro?", "alternativas": ["Medir comprimento", "Medir velocidade", "Medir temperatura"], "correta": 2},
        {"pergunta": "Para que serve um estetoscópio?", "alternativas": ["Ouvir sons internos do corpo", "Medir altura", "Ver estrelas"], "correta": 0},
        {"pergunta": "Para que serve um telescópio?", "alternativas": ["Medir peso", "Observar objetos distantes no céu", "Cortar madeira"], "correta": 1},
        {"pergunta": "Para que serve um microscópio?", "alternativas": ["Medir vento", "Ouvir música", "Observar estruturas muito pequenas"], "correta": 2},
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
