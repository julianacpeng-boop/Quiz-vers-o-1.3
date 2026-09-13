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

  # 45 novos temas de quiz - 5 perguntas por tema
# Total: 225 perguntas
# Respostas corretas variando entre A/B/C.

QUIZZES = {

    "Menstruação": [
        {"pergunta": "Em média, qual evento marca o primeiro dia de um novo ciclo menstrual?", "alternativas": ["O início do sangramento menstrual", "O fim da ovulação", "O aumento da temperatura corporal"], "correta": 0},
        {"pergunta": "Qual hormônio tende a aumentar antes da ovulação?", "alternativas": ["Insulina", "LH", "Melatonina"], "correta": 1},
        {"pergunta": "Qual estrutura do útero é eliminada em parte durante a menstruação?", "alternativas": ["Miocárdio", "Pleura", "Endométrio"], "correta": 2},
        {"pergunta": "Qual sintoma pode ocorrer antes ou durante a menstruação?", "alternativas": ["Cólica", "Perda permanente da visão", "Fratura óssea"], "correta": 0},
        {"pergunta": "Qual profissional pode avaliar alterações menstruais persistentes?", "alternativas": ["Oftalmologista", "Ginecologista", "Ortopedista"], "correta": 1},
    ],

    "Quiz Bíblico": [
        {"pergunta": "Quem construiu a arca segundo o livro de Gênesis?", "alternativas": ["Moisés", "Noé", "Davi"], "correta": 1},
        {"pergunta": "Quem recebeu os Dez Mandamentos no monte Sinai?", "alternativas": ["Salomão", "Pedro", "Moisés"], "correta": 2},
        {"pergunta": "Qual personagem bíblico derrotou Golias?", "alternativas": ["Davi", "José", "Isaías"], "correta": 0},
        {"pergunta": "Quantos Evangelhos há no Novo Testamento?", "alternativas": ["Dois", "Quatro", "Sete"], "correta": 1},
        {"pergunta": "Qual é o último livro do Novo Testamento?", "alternativas": ["Atos", "Romanos", "Apocalipse"], "correta": 2},
    ],

    "Leis de Trânsito": [
        {"pergunta": "Segundo o Código de Trânsito Brasileiro, o uso do cinto de segurança é obrigatório para quem?", "alternativas": ["Apenas o condutor", "Apenas quem está no banco da frente", "Condutor e passageiros"], "correta": 2},
        {"pergunta": "Dirigir segurando ou manuseando telefone celular é o quê?", "alternativas": ["Infração de trânsito", "Conduta sempre permitida", "Obrigação do condutor"], "correta": 0},
        {"pergunta": "Em regra, o pedestre que já iniciou a travessia deve receber o quê dos condutores?", "alternativas": ["Buzina obrigatória", "Prioridade de passagem", "Sinal de luz alta"], "correta": 1},
        {"pergunta": "A sinalização e as regras de trânsito têm como objetivo principal o quê?", "alternativas": ["Aumentar o consumo de combustível", "Reduzir o número de pedestres", "Segurança e organização da circulação"], "correta": 2},
        {"pergunta": "Conduzir veículo após consumir álcool pode gerar o quê?", "alternativas": ["Sanções administrativas e, em certos casos, crime", "Apenas advertência verbal", "Nenhuma consequência"], "correta": 0},
    ],

    "Complete a Frase da Sua Mãe": [
        {"pergunta": "Complete: Na volta a gente...", "alternativas": ["compra", "esquece", "vende"], "correta": 0},
        {"pergunta": "Complete: Você não é todo...", "alternativas": ["bairro", "mundo", "colégio"], "correta": 1},
        {"pergunta": "Complete: Enquanto você morar debaixo do meu...", "alternativas": ["carro", "sapato", "teto"], "correta": 2},
        {"pergunta": "Complete: Eu não sou sua...", "alternativas": ["empregada", "vizinha", "professora"], "correta": 0},
        {"pergunta": "Complete: Se eu achar, você vai...", "alternativas": ["dormir", "ver", "estudar"], "correta": 1},
    ],

    "Genética": [
        {"pergunta": "Qual molécula armazena a maior parte da informação genética nas células humanas?", "alternativas": ["Glicose", "DNA", "Colesterol"], "correta": 1},
        {"pergunta": "Como se chama uma versão alternativa de um gene?", "alternativas": ["Neurônio", "Antígeno", "Alelo"], "correta": 2},
        {"pergunta": "Quantos cromossomos há normalmente nas células somáticas humanas?", "alternativas": ["46", "23", "92"], "correta": 0},
        {"pergunta": "Qual processo produz gametas com metade do número de cromossomos?", "alternativas": ["Mitose", "Meiose", "Tradução"], "correta": 1},
        {"pergunta": "Como se chama a característica observável resultante da interação entre genes e ambiente?", "alternativas": ["Genótipo", "Cariótipo", "Fenótipo"], "correta": 2},
    ],

    "Métodos Contraceptivos": [
        {"pergunta": "Qual método também ajuda a reduzir o risco de infecções sexualmente transmissíveis?", "alternativas": ["Pílula anticoncepcional", "DIU de cobre", "Preservativo"], "correta": 2},
        {"pergunta": "Qual método é colocado dentro do útero por profissional de saúde?", "alternativas": ["DIU", "Adesivo contraceptivo", "Preservativo externo"], "correta": 0},
        {"pergunta": "A pílula anticoncepcional protege contra infecções sexualmente transmissíveis?", "alternativas": ["Sim, sempre", "Não", "Somente aos fins de semana"], "correta": 1},
        {"pergunta": "Qual método é usado após uma relação sexual desprotegida para reduzir o risco de gravidez?", "alternativas": ["Vacina", "Antibiótico", "Contracepção de emergência"], "correta": 2},
        {"pergunta": "Qual atitude é mais adequada ao escolher um método contraceptivo?", "alternativas": ["Buscar orientação profissional e considerar necessidades individuais", "Copiar o método de outra pessoa sem avaliação", "Interromper qualquer método sem motivo ou orientação"], "correta": 0},
    ],

    "Datas Importantes de Setembro": [
        {"pergunta": "Qual data marca a Independência do Brasil?", "alternativas": ["7 de setembro", "15 de setembro", "30 de setembro"], "correta": 0},
        {"pergunta": "No Brasil, o Dia da Árvore é lembrado em qual data?", "alternativas": ["1 de setembro", "21 de setembro", "12 de setembro"], "correta": 1},
        {"pergunta": "O Dia Mundial de Prevenção do Suicídio é lembrado em qual data?", "alternativas": ["20 de setembro", "29 de setembro", "10 de setembro"], "correta": 2},
        {"pergunta": "Qual mês é associado à campanha Setembro Amarelo no Brasil?", "alternativas": ["Setembro", "Março", "Julho"], "correta": 0},
        {"pergunta": "Qual estação do ano começa por volta de setembro no Hemisfério Sul?", "alternativas": ["Inverno", "Primavera", "Outono"], "correta": 1},
    ],

    "Primeira Vez": [
        {"pergunta": "Antes de uma relação sexual, o que deve existir entre as pessoas envolvidas?", "alternativas": ["Pressão para agradar", "Consentimento livre e claro", "Medo de dizer não"], "correta": 1},
        {"pergunta": "Qual método de barreira ajuda a reduzir o risco de gravidez e de infecções sexualmente transmissíveis?", "alternativas": ["Antibiótico", "Analgésico", "Preservativo"], "correta": 2},
        {"pergunta": "É possível ocorrer gravidez na primeira relação sexual com penetração vaginal sem contracepção?", "alternativas": ["Sim", "Não, nunca", "Somente depois dos 30 anos"], "correta": 0},
        {"pergunta": "Se alguém muda de ideia durante uma relação, o que deve acontecer?", "alternativas": ["A pessoa deve ser convencida", "A atividade deve parar", "Nada muda"], "correta": 1},
        {"pergunta": "Qual atitude ajuda a tornar uma primeira experiência mais segura?", "alternativas": ["Evitar qualquer conversa", "Confiar apenas em mitos", "Conversar sobre limites, proteção e consentimento"], "correta": 2},
    ],

    "Voto de Cabresto": [
        {"pergunta": "O voto de cabresto ficou associado principalmente a qual período da história brasileira?", "alternativas": ["Brasil Colônia inicial", "Nova República após 1988", "República Velha"], "correta": 2},
        {"pergunta": "O voto de cabresto estava ligado ao poder de quem nas comunidades locais?", "alternativas": ["Coronéis e chefes políticos", "Astronautas", "Diplomatas estrangeiros"], "correta": 0},
        {"pergunta": "Qual característica favorecia o controle do voto naquele período?", "alternativas": ["Voto eletrônico", "Ausência de voto secreto efetivo", "Biometria digital"], "correta": 1},
        {"pergunta": "O coronelismo estava relacionado principalmente a quê?", "alternativas": ["Exploração espacial", "Industrialização japonesa", "Poder político local e relações de dependência"], "correta": 2},
        {"pergunta": "Qual mudança ajudou a reduzir práticas de controle direto do voto?", "alternativas": ["Adoção do voto secreto", "Fim das eleições", "Proibição de partidos"], "correta": 0},
    ],

    "Primeira Guerra Mundial": [
        {"pergunta": "Em que ano começou a Primeira Guerra Mundial?", "alternativas": ["1914", "1905", "1939"], "correta": 0},
        {"pergunta": "Qual acontecimento é apontado como estopim da guerra?", "alternativas": ["Queda do Muro de Berlim", "Assassinato do arquiduque Francisco Ferdinando", "Ataque a Pearl Harbor"], "correta": 1},
        {"pergunta": "Qual conjunto de países formava a Tríplice Entente no início do conflito?", "alternativas": ["Alemanha, Itália e Japão", "Brasil, Argentina e Chile", "França, Reino Unido e Rússia"], "correta": 2},
        {"pergunta": "Qual tipo de combate marcou fortemente a Frente Ocidental?", "alternativas": ["Guerra de trincheiras", "Guerra espacial", "Guerra nuclear"], "correta": 0},
        {"pergunta": "Em que ano terminou a Primeira Guerra Mundial?", "alternativas": ["1929", "1918", "1945"], "correta": 1},
    ],

    "Guerra Fria": [
        {"pergunta": "Quais foram as duas principais potências rivais da Guerra Fria?", "alternativas": ["Brasil e Argentina", "Estados Unidos e União Soviética", "França e Espanha"], "correta": 1},
        {"pergunta": "Qual muro se tornou símbolo da divisão entre os blocos durante a Guerra Fria?", "alternativas": ["Muralha da China", "Muro de Adriano", "Muro de Berlim"], "correta": 2},
        {"pergunta": "Qual disputa tecnológica levou humanos à Lua?", "alternativas": ["Corrida Espacial", "Revolução Industrial", "Primavera dos Povos"], "correta": 0},
        {"pergunta": "Qual aliança militar reuniu países do bloco ocidental?", "alternativas": ["Mercosul", "OTAN", "OPEP"], "correta": 1},
        {"pergunta": "Em que ano caiu o Muro de Berlim?", "alternativas": ["1961", "2001", "1989"], "correta": 2},
    ],

    "Segunda Guerra Mundial": [
        {"pergunta": "Em que ano começou a Segunda Guerra Mundial na Europa?", "alternativas": ["1914", "1948", "1939"], "correta": 2},
        {"pergunta": "Qual país foi invadido pela Alemanha em setembro de 1939?", "alternativas": ["Polônia", "Canadá", "México"], "correta": 0},
        {"pergunta": "Qual ataque levou os Estados Unidos a entrar diretamente na guerra?", "alternativas": ["Batalha de Waterloo", "Pearl Harbor", "Queda de Roma"], "correta": 1},
        {"pergunta": "Em que ano terminou a Segunda Guerra Mundial?", "alternativas": ["1936", "1955", "1945"], "correta": 2},
        {"pergunta": "Qual organização internacional foi criada em 1945 com foco em cooperação e paz?", "alternativas": ["ONU", "OTAN", "União Europeia"], "correta": 0},
    ],

    "Revolução Francesa": [
        {"pergunta": "Em que ano começou a Revolução Francesa?", "alternativas": ["1789", "1815", "1917"], "correta": 0},
        {"pergunta": "Qual prisão foi tomada em 14 de julho de 1789?", "alternativas": ["Alcatraz", "Bastilha", "Torre de Londres"], "correta": 1},
        {"pergunta": "Qual lema ficou associado à Revolução Francesa?", "alternativas": ["Ordem e progresso", "Paz e terra", "Liberdade, igualdade e fraternidade"], "correta": 2},
        {"pergunta": "Quem era o rei da França no início da Revolução?", "alternativas": ["Luís XVI", "Napoleão III", "Carlos Magno"], "correta": 0},
        {"pergunta": "Qual documento de 1789 proclamou direitos e liberdades fundamentais?", "alternativas": ["Magna Carta", "Declaração dos Direitos do Homem e do Cidadão", "Tratado de Versalhes"], "correta": 1},
    ],

    "Independência do Brasil": [
        {"pergunta": "Em que ano foi proclamada a Independência do Brasil?", "alternativas": ["1889", "1822", "1808"], "correta": 1},
        {"pergunta": "Quem proclamou a Independência do Brasil?", "alternativas": ["Dom Pedro II", "Getúlio Vargas", "Dom Pedro I"], "correta": 2},
        {"pergunta": "Qual data é celebrada como Independência do Brasil?", "alternativas": ["7 de setembro", "15 de novembro", "21 de abril"], "correta": 0},
        {"pergunta": "Em que local ocorreu o episódio tradicionalmente associado ao grito da Independência?", "alternativas": ["Na Praia de Copacabana", "Às margens do riacho Ipiranga", "No Pelourinho"], "correta": 1},
        {"pergunta": "Qual país colonizava o Brasil antes da independência?", "alternativas": ["Espanha", "França", "Portugal"], "correta": 2},
    ],

    "Brasil Império": [
        {"pergunta": "Quem foi o primeiro imperador do Brasil?", "alternativas": ["Dom João VI", "Dom Pedro II", "Dom Pedro I"], "correta": 2},
        {"pergunta": "Quem foi o segundo e último imperador do Brasil?", "alternativas": ["Dom Pedro II", "Deodoro da Fonseca", "José Bonifácio"], "correta": 0},
        {"pergunta": "Em que ano foi abolida legalmente a escravidão no Brasil?", "alternativas": ["1822", "1888", "1930"], "correta": 1},
        {"pergunta": "Qual lei aboliu legalmente a escravidão no Brasil?", "alternativas": ["Lei do Ventre Livre apenas", "Lei de Terras", "Lei Áurea"], "correta": 2},
        {"pergunta": "Em que ano terminou o período imperial brasileiro?", "alternativas": ["1889", "1840", "1894"], "correta": 0},
    ],

    "República Velha": [
        {"pergunta": "Qual período brasileiro é chamado de República Velha ou Primeira República?", "alternativas": ["1889 a 1930", "1822 a 1889", "1930 a 1945"], "correta": 0},
        {"pergunta": "Qual política marcou a influência das elites de São Paulo e Minas Gerais?", "alternativas": ["Plano Real", "Política do café com leite", "Regência Trina"], "correta": 1},
        {"pergunta": "Qual fenômeno político local marcou esse período?", "alternativas": ["Apartheid", "Parlamentarismo europeu", "Coronelismo"], "correta": 2},
        {"pergunta": "Qual revolta ocorreu no Rio de Janeiro em 1904?", "alternativas": ["Revolta da Vacina", "Sabinada", "Balaiada"], "correta": 0},
        {"pergunta": "Qual evento encerrou a República Velha?", "alternativas": ["Independência do Brasil", "Revolução de 1930", "Proclamação da República"], "correta": 1},
    ],

    "Era Vargas": [
        {"pergunta": "Em que ano Getúlio Vargas chegou ao poder pela Revolução de 1930?", "alternativas": ["1889", "1930", "1964"], "correta": 1},
        {"pergunta": "Como se chamou o regime autoritário instaurado por Vargas em 1937?", "alternativas": ["República da Espada", "Regência Trina", "Estado Novo"], "correta": 2},
        {"pergunta": "Qual legislação trabalhista foi consolidada em 1943?", "alternativas": ["CLT", "Lei Áurea", "Código Civil de 2002"], "correta": 0},
        {"pergunta": "Qual empresa estatal de petróleo foi criada no segundo governo Vargas?", "alternativas": ["Embraer", "Petrobras", "Correios"], "correta": 1},
        {"pergunta": "Em que ano Getúlio Vargas morreu?", "alternativas": ["1945", "1960", "1954"], "correta": 2},
    ],

    "Ditadura Militar no Brasil": [
        {"pergunta": "Em que ano ocorreu o golpe que iniciou a ditadura militar no Brasil?", "alternativas": ["1954", "1985", "1964"], "correta": 2},
        {"pergunta": "Qual ato institucional de 1968 ampliou a repressão e suspendeu garantias?", "alternativas": ["AI-5", "AI-1 de 1988", "Ato Colonial"], "correta": 0},
        {"pergunta": "Como ficou conhecido o processo de retorno gradual à democracia?", "alternativas": ["Estado Novo", "Abertura política", "Regência"], "correta": 1},
        {"pergunta": "Qual movimento de 1984 defendia eleições diretas para presidente?", "alternativas": ["Tenentismo", "Canudos", "Diretas Já"], "correta": 2},
        {"pergunta": "Em que ano terminou o regime militar no Brasil?", "alternativas": ["1985", "1970", "1994"], "correta": 0},
    ],

    "Constituição Brasileira": [
        {"pergunta": "Em que ano foi promulgada a atual Constituição Federal do Brasil?", "alternativas": ["1988", "1964", "2002"], "correta": 0},
        {"pergunta": "Como a Constituição de 1988 ficou conhecida?", "alternativas": ["Carta do Café", "Constituição Cidadã", "Lei de Ouro"], "correta": 1},
        {"pergunta": "Qual poder tem como função típica elaborar leis em âmbito federal?", "alternativas": ["Poder Executivo", "Poder Judiciário", "Poder Legislativo"], "correta": 2},
        {"pergunta": "Qual princípio afirma que todos são iguais perante a lei?", "alternativas": ["Igualdade", "Hereditariedade", "Censitário"], "correta": 0},
        {"pergunta": "Quantos poderes independentes e harmônicos são previstos na Constituição?", "alternativas": ["Dois", "Três", "Cinco"], "correta": 1},
    ],

    "Eleições no Brasil": [
        {"pergunta": "Qual órgão organiza as eleições em âmbito nacional no Brasil?", "alternativas": ["Banco Central", "Tribunal Superior Eleitoral", "Supremo Tribunal Militar"], "correta": 1},
        {"pergunta": "Para brasileiros alfabetizados com mais de 18 e menos de 70 anos, o voto é como?", "alternativas": ["Proibido", "Facultativo", "Obrigatório"], "correta": 2},
        {"pergunta": "Para jovens de 16 e 17 anos, o voto é como?", "alternativas": ["Facultativo", "Obrigatório", "Proibido"], "correta": 0},
        {"pergunta": "Qual sistema é usado no Brasil para registrar a maior parte dos votos presenciais?", "alternativas": ["Cédula manuscrita obrigatória em todo o país", "Urna eletrônica", "Aplicativo particular"], "correta": 1},
        {"pergunta": "Qual documento eleitoral identifica a inscrição do eleitor?", "alternativas": ["Passaporte diplomático", "Carteira de vacinação", "Título de eleitor"], "correta": 2},
    ],

    "Sistema Solar": [
        {"pergunta": "Qual planeta é o mais próximo do Sol?", "alternativas": ["Vênus", "Marte", "Mercúrio"], "correta": 2},
        {"pergunta": "Qual é o maior planeta do Sistema Solar?", "alternativas": ["Júpiter", "Saturno", "Terra"], "correta": 0},
        {"pergunta": "Qual planeta é conhecido como Planeta Vermelho?", "alternativas": ["Netuno", "Marte", "Urano"], "correta": 1},
        {"pergunta": "Qual astro está no centro do Sistema Solar?", "alternativas": ["Lua", "Júpiter", "Sol"], "correta": 2},
        {"pergunta": "Qual planeta possui anéis muito visíveis?", "alternativas": ["Saturno", "Mercúrio", "Vênus"], "correta": 0},
    ],

    "Corpo Humano": [
        {"pergunta": "Qual órgão bombeia sangue pelo corpo?", "alternativas": ["Coração", "Pulmão", "Rim"], "correta": 0},
        {"pergunta": "Qual órgão é responsável principalmente pelas trocas gasosas?", "alternativas": ["Estômago", "Pulmões", "Pâncreas"], "correta": 1},
        {"pergunta": "Qual órgão produz bile?", "alternativas": ["Baço", "Bexiga", "Fígado"], "correta": 2},
        {"pergunta": "Qual sistema é responsável pela comunicação rápida por impulsos elétricos no corpo?", "alternativas": ["Sistema nervoso", "Sistema digestório", "Sistema linfático"], "correta": 0},
        {"pergunta": "Qual osso protege grande parte do cérebro?", "alternativas": ["Fêmur", "Crânio", "Úmero"], "correta": 1},
    ],

    "Hormônios": [
        {"pergunta": "Qual glândula produz insulina?", "alternativas": ["Tireoide", "Pâncreas", "Hipófise"], "correta": 1},
        {"pergunta": "Qual hormônio ajuda a reduzir a glicose no sangue?", "alternativas": ["Adrenalina", "Melatonina", "Insulina"], "correta": 2},
        {"pergunta": "Qual hormônio está relacionado ao ciclo sono-vigília?", "alternativas": ["Melatonina", "Testosterona", "Insulina"], "correta": 0},
        {"pergunta": "Qual glândula produz os hormônios T3 e T4?", "alternativas": ["Pâncreas", "Tireoide", "Suprarrenal"], "correta": 1},
        {"pergunta": "Qual hormônio aumenta rapidamente em situações de estresse agudo?", "alternativas": ["Progesterona", "Calcitonina", "Adrenalina"], "correta": 2},
    ],

    "Tipos Sanguíneos": [
        {"pergunta": "Quais sistemas são mais usados para classificar tipos sanguíneos em transfusões?", "alternativas": ["DNA e RNA", "T3 e T4", "ABO e Rh"], "correta": 2},
        {"pergunta": "Uma pessoa do grupo O possui quais antígenos A ou B nas hemácias?", "alternativas": ["Nenhum dos dois", "Apenas A", "Apenas B"], "correta": 0},
        {"pergunta": "Qual grupo possui antígenos A e B nas hemácias?", "alternativas": ["O", "AB", "A apenas"], "correta": 1},
        {"pergunta": "O fator Rh é indicado normalmente por qual sinal junto ao tipo sanguíneo?", "alternativas": ["Alto ou baixo", "Quente ou frio", "Positivo ou negativo"], "correta": 2},
        {"pergunta": "Antes de uma transfusão, o que é essencial verificar?", "alternativas": ["Compatibilidade sanguínea", "Cor dos olhos", "Altura do paciente"], "correta": 0},
    ],

    "DNA e RNA": [
        {"pergunta": "Qual base nitrogenada aparece no DNA, mas não no RNA?", "alternativas": ["Timina", "Uracila", "Ribose"], "correta": 0},
        {"pergunta": "Qual base aparece no RNA no lugar da timina?", "alternativas": ["Guanina", "Uracila", "Citosina"], "correta": 1},
        {"pergunta": "Qual açúcar está presente no DNA?", "alternativas": ["Ribose", "Glicose", "Desoxirribose"], "correta": 2},
        {"pergunta": "Qual processo produz RNA a partir de uma sequência de DNA?", "alternativas": ["Transcrição", "Tradução", "Replicação proteica"], "correta": 0},
        {"pergunta": "Qual molécula leva a informação do DNA aos ribossomos para síntese proteica?", "alternativas": ["Lipídio", "RNA mensageiro", "Glicogênio"], "correta": 1},
    ],

    "Puberdade": [
        {"pergunta": "Qual fase da vida envolve mudanças físicas e hormonais que levam à maturação sexual?", "alternativas": ["Velhice", "Puberdade", "Gestação"], "correta": 1},
        {"pergunta": "Qual hormônio sexual aumenta bastante nos meninos durante a puberdade?", "alternativas": ["Insulina", "Melatonina", "Testosterona"], "correta": 2},
        {"pergunta": "Qual mudança pode ocorrer em ambos os sexos durante a puberdade?", "alternativas": ["Crescimento de pelos", "Perda de todos os dentes permanentes", "Redução completa da altura"], "correta": 0},
        {"pergunta": "Nas meninas, qual evento pode ocorrer durante a puberdade?", "alternativas": ["Menopausa", "Menarca", "Catarata"], "correta": 1},
        {"pergunta": "Por que a idade de início da puberdade varia entre pessoas?", "alternativas": ["Porque todos começam no mesmo dia", "Somente pela cor dos olhos", "Por fatores genéticos e ambientais"], "correta": 2},
    ],

    "Ovulação e Fertilidade": [
        {"pergunta": "O que é ovulação?", "alternativas": ["Início obrigatório da menstruação", "Implantação do embrião", "Liberação de um óvulo pelo ovário"], "correta": 2},
        {"pergunta": "Qual hormônio apresenta um pico que desencadeia a ovulação?", "alternativas": ["LH", "Insulina", "Cortisol"], "correta": 0},
        {"pergunta": "A ovulação ocorre sempre exatamente no 14º dia em todas as pessoas?", "alternativas": ["Sim", "Não", "Somente em anos bissextos"], "correta": 1},
        {"pergunta": "Qual estrutura capta o óvulo após a ovulação?", "alternativas": ["Uretra", "Vesícula biliar", "Tuba uterina"], "correta": 2},
        {"pergunta": "Qual fator pode influenciar a regularidade da ovulação?", "alternativas": ["Alterações hormonais", "Tipo sanguíneo apenas", "Cor do cabelo"], "correta": 0},
    ],

    "Infecções Sexualmente Transmissíveis": [
        {"pergunta": "Qual método de barreira ajuda a reduzir o risco de muitas infecções sexualmente transmissíveis?", "alternativas": ["Preservativo", "Pílula anticoncepcional", "DIU"], "correta": 0},
        {"pergunta": "O HIV pode ser transmitido por abraço ou aperto de mão?", "alternativas": ["Sim", "Não", "Sempre"], "correta": 1},
        {"pergunta": "Qual infecção sexualmente transmissível pode ser prevenida por vacinação?", "alternativas": ["Sífilis", "Gonorreia", "HPV"], "correta": 2},
        {"pergunta": "Uma pessoa pode ter uma infecção sexualmente transmissível sem sintomas?", "alternativas": ["Sim", "Não, nunca", "Somente após 60 anos"], "correta": 0},
        {"pergunta": "Ao suspeitar de uma infecção sexualmente transmissível, qual atitude é adequada?", "alternativas": ["Tomar qualquer antibiótico por conta própria", "Buscar avaliação de saúde", "Ignorar os sintomas"], "correta": 1},
    ],

    "Gravidez": [
        {"pergunta": "Onde normalmente ocorre a implantação do embrião?", "alternativas": ["Ovário", "Útero", "Bexiga"], "correta": 1},
        {"pergunta": "Qual hormônio é detectado pelos testes de gravidez?", "alternativas": ["Insulina", "Adrenalina", "hCG"], "correta": 2},
        {"pergunta": "Qual órgão faz trocas de nutrientes e gases entre gestante e feto?", "alternativas": ["Placenta", "Pâncreas", "Tireoide"], "correta": 0},
        {"pergunta": "Quantos trimestres compõem uma gestação?", "alternativas": ["Dois", "Três", "Cinco"], "correta": 1},
        {"pergunta": "Qual profissional pode acompanhar o pré-natal?", "alternativas": ["Oftalmologista apenas", "Dentista apenas", "Obstetra ou equipe de pré-natal"], "correta": 2},
    ],

    "Saúde Íntima Feminina": [
        {"pergunta": "Qual órgão faz parte do sistema reprodutor feminino?", "alternativas": ["Próstata", "Traqueia", "Útero"], "correta": 2},
        {"pergunta": "Qual profissional costuma avaliar a saúde ginecológica?", "alternativas": ["Ginecologista", "Neurologista", "Ortopedista"], "correta": 0},
        {"pergunta": "Quando há alteração persistente no corrimento vaginal, o ideal é o quê?", "alternativas": ["Usar qualquer medicamento sem orientação", "Buscar avaliação de saúde", "Ignorar sempre"], "correta": 1},
        {"pergunta": "Qual exame pode ser usado na avaliação do colo do útero conforme orientação de saúde?", "alternativas": ["Eletrocardiograma", "Espirometria", "Papanicolau"], "correta": 2},
        {"pergunta": "Qual atitude ajuda a saúde íntima?", "alternativas": ["Evitar duchas vaginais sem indicação", "Usar produtos irritantes internamente", "Compartilhar medicamentos"], "correta": 0},
    ],

    "Saúde Íntima Masculina": [
        {"pergunta": "Qual órgão produz espermatozoides?", "alternativas": ["Testículos", "Próstata", "Bexiga"], "correta": 0},
        {"pergunta": "Qual glândula contribui com líquido para o sêmen?", "alternativas": ["Tireoide", "Próstata", "Hipófise"], "correta": 1},
        {"pergunta": "Qual profissional pode avaliar problemas do sistema urinário e reprodutor masculino?", "alternativas": ["Oftalmologista", "Dermatologista apenas", "Urologista"], "correta": 2},
        {"pergunta": "Dor testicular súbita e intensa deve ser tratada como o quê?", "alternativas": ["Situação que requer avaliação médica urgente", "Algo para ignorar por vários dias", "Sinal certo de gripe"], "correta": 0},
        {"pergunta": "O preservativo ajuda a reduzir o risco de quê?", "alternativas": ["Miopia", "Infecções sexualmente transmissíveis e gravidez", "Cárie"], "correta": 1},
    ],

    "Sono e Sonhos": [
        {"pergunta": "Qual hormônio está associado ao início do sono em resposta à escuridão?", "alternativas": ["Insulina", "Melatonina", "Adrenalina"], "correta": 1},
        {"pergunta": "Qual fase do sono está muito associada a sonhos vívidos?", "alternativas": ["Estado de vigília", "Sono profundo apenas", "Sono REM"], "correta": 2},
        {"pergunta": "O que é higiene do sono?", "alternativas": ["Hábitos que favorecem sono regular e de qualidade", "Limpeza do quarto apenas", "Uso obrigatório de medicamentos"], "correta": 0},
        {"pergunta": "Qual hábito pode atrapalhar o sono se feito perto do horário de dormir?", "alternativas": ["Reduzir luz intensa", "Consumir muita cafeína", "Manter horário regular"], "correta": 1},
        {"pergunta": "Adultos passam por vários ciclos de sono durante a noite?", "alternativas": ["Não", "Somente uma vez por mês", "Sim"], "correta": 2},
    ],

    "Cérebro Humano": [
        {"pergunta": "Qual parte do cérebro está muito envolvida com equilíbrio e coordenação motora?", "alternativas": ["Hipófise", "Medula óssea", "Cerebelo"], "correta": 2},
        {"pergunta": "Qual lobo cerebral está associado principalmente ao processamento visual?", "alternativas": ["Occipital", "Frontal", "Temporal"], "correta": 0},
        {"pergunta": "Qual estrutura conecta os dois hemisférios cerebrais?", "alternativas": ["Fêmur", "Corpo caloso", "Diafragma"], "correta": 1},
        {"pergunta": "Qual célula é especializada em transmitir impulsos nervosos?", "alternativas": ["Hemácia", "Osteócito", "Neurônio"], "correta": 2},
        {"pergunta": "Qual neurotransmissor está envolvido em recompensa e motivação?", "alternativas": ["Dopamina", "Hemoglobina", "Colágeno"], "correta": 0},
    ],

    "Vacinas e Imunidade": [
        {"pergunta": "Qual é a função principal de uma vacina?", "alternativas": ["Treinar o sistema imune para reconhecer um agente ou parte dele", "Curar qualquer doença instantaneamente", "Substituir alimentação saudável"], "correta": 0},
        {"pergunta": "Qual tipo de célula participa da defesa imunológica?", "alternativas": ["Hemácia apenas", "Leucócito", "Adipócito apenas"], "correta": 1},
        {"pergunta": "O que é memória imunológica?", "alternativas": ["Esquecimento total de infecções", "Perda de anticorpos em minutos", "Capacidade de responder mais rapidamente a um agente já reconhecido"], "correta": 2},
        {"pergunta": "Vacinas podem ajudar a reduzir a circulação de doenças em uma população?", "alternativas": ["Sim", "Não", "Somente em animais"], "correta": 0},
        {"pergunta": "Onde devem ser verificadas informações confiáveis sobre vacinação no Brasil?", "alternativas": ["Correntes de mensagens", "Ministério da Saúde e serviços de saúde", "Perfis sem fonte"], "correta": 1},
    ],

    "Alimentação e Nutrientes": [
        {"pergunta": "Qual nutriente é uma importante fonte de energia?", "alternativas": ["Água apenas", "Carboidrato", "Mineral apenas"], "correta": 1},
        {"pergunta": "Qual nutriente é fundamental para construção e reparo de tecidos?", "alternativas": ["Vitamina C apenas", "Água", "Proteína"], "correta": 2},
        {"pergunta": "Qual vitamina está associada à absorção de cálcio e saúde óssea?", "alternativas": ["Vitamina D", "Vitamina K apenas", "Vitamina B12 apenas"], "correta": 0},
        {"pergunta": "Qual mineral é componente da hemoglobina?", "alternativas": ["Sódio", "Ferro", "Iodo"], "correta": 1},
        {"pergunta": "Qual alimento é fonte de fibras?", "alternativas": ["Açúcar refinado", "Óleo puro", "Feijão"], "correta": 2},
    ],

    "Primeiros Socorros": [
        {"pergunta": "Ao encontrar uma pessoa inconsciente, qual é uma das primeiras atitudes?", "alternativas": ["Oferecer comida imediatamente", "Colocar a pessoa de pé", "Verificar segurança do local e responsividade"], "correta": 2},
        {"pergunta": "Em uma emergência, qual número aciona o SAMU no Brasil?", "alternativas": ["192", "190", "193"], "correta": 0},
        {"pergunta": "Em caso de sangramento externo importante, o que pode ajudar enquanto chega socorro?", "alternativas": ["Aplicar café em pó", "Compressão direta com material limpo", "Colocar terra sobre o ferimento"], "correta": 1},
        {"pergunta": "Em uma queimadura térmica leve, qual cuidado inicial é recomendado?", "alternativas": ["Aplicar pasta de dente", "Estourar bolhas", "Resfriar com água corrente"], "correta": 2},
        {"pergunta": "Se houver suspeita de lesão na coluna após trauma, o ideal é o quê?", "alternativas": ["Evitar movimentação desnecessária e chamar socorro", "Sentar a pessoa rapidamente", "Puxar pelos braços"], "correta": 0},
    ],

    "Segurança no Trânsito": [
        {"pergunta": "Qual atitude reduz distrações ao dirigir?", "alternativas": ["Guardar o celular e evitar manuseá-lo", "Responder mensagens enquanto conduz", "Assistir vídeos no painel"], "correta": 0},
        {"pergunta": "O cinto de segurança deve ser usado por quem?", "alternativas": ["Somente o motorista", "Todos os ocupantes", "Somente crianças"], "correta": 1},
        {"pergunta": "Antes de mudar de faixa, o condutor deve fazer o quê?", "alternativas": ["Mudar sem olhar", "Acelerar sem sinalizar", "Sinalizar e verificar se a manobra é segura"], "correta": 2},
        {"pergunta": "Em pista molhada, qual atitude é mais segura?", "alternativas": ["Reduzir a velocidade e aumentar a distância", "Aumentar a velocidade", "Frear bruscamente o tempo todo"], "correta": 0},
        {"pergunta": "Qual atitude é adequada diante de pedestre atravessando em local apropriado?", "alternativas": ["Acelerar", "Reduzir e respeitar a prioridade quando aplicável", "Buzinar continuamente"], "correta": 1},
    ],

    "Prova Teórica da CNH": [
        {"pergunta": "Qual documento reúne as principais regras de trânsito no Brasil?", "alternativas": ["Código Penal apenas", "Código de Trânsito Brasileiro", "Constituição Estadual apenas"], "correta": 1},
        {"pergunta": "Qual equipamento de segurança é obrigatório para ocupantes de automóveis?", "alternativas": ["Capacete dentro do carro", "Colete refletivo para todos", "Cinto de segurança"], "correta": 2},
        {"pergunta": "Dirigir sob influência de álcool é permitido?", "alternativas": ["Não", "Sim, sempre", "Somente à noite"], "correta": 0},
        {"pergunta": "O que deve ser feito antes de iniciar uma ultrapassagem?", "alternativas": ["Acelerar sem observar", "Verificar se é permitida e segura", "Usar o celular"], "correta": 1},
        {"pergunta": "Qual é a principal finalidade da sinalização de trânsito?", "alternativas": ["Decorar as vias", "Aumentar o ruído", "Orientar, advertir e regulamentar a circulação"], "correta": 2},
    ],

    "Pedestres e Ciclistas no Trânsito": [
        {"pergunta": "Quando houver calçada em boas condições, o pedestre deve preferencialmente utilizá-la para quê?", "alternativas": ["Estacionar bicicleta", "Parar automóveis", "Circular fora da pista de veículos"], "correta": 2},
        {"pergunta": "Ao atravessar uma via, o pedestre deve procurar o quê?", "alternativas": ["Local seguro e, quando houver, faixa de pedestres", "O ponto de maior velocidade dos carros", "A curva sem visibilidade"], "correta": 0},
        {"pergunta": "O ciclista deve respeitar as regras de circulação e sinalização?", "alternativas": ["Não", "Sim", "Somente em rodovias"], "correta": 1},
        {"pergunta": "Ao ultrapassar uma bicicleta, o motorista deve agir como?", "alternativas": ["Passando o mais perto possível", "Buzinando sem parar", "Com cuidado e distância lateral segura"], "correta": 2},
        {"pergunta": "Qual item melhora a visibilidade do ciclista à noite?", "alternativas": ["Iluminação e elementos refletivos", "Roupa totalmente escura sem luz", "Fone de ouvido com volume máximo"], "correta": 0},
    ],

    "Geografia do Brasil": [
        {"pergunta": "Qual é a maior região brasileira em área territorial?", "alternativas": ["Norte", "Sul", "Sudeste"], "correta": 0},
        {"pergunta": "Qual é o maior estado brasileiro em área?", "alternativas": ["Bahia", "Amazonas", "São Paulo"], "correta": 1},
        {"pergunta": "Qual rio possui a maior bacia hidrográfica do mundo?", "alternativas": ["São Francisco", "Paraná", "Amazonas"], "correta": 2},
        {"pergunta": "Qual bioma predomina em grande parte da região Norte?", "alternativas": ["Amazônia", "Pampa", "Caatinga"], "correta": 0},
        {"pergunta": "Qual é a capital do Brasil?", "alternativas": ["Rio de Janeiro", "Brasília", "São Paulo"], "correta": 1},
    ],

    "Capitais do Brasil": [
        {"pergunta": "Qual é a capital da Paraíba?", "alternativas": ["Recife", "João Pessoa", "Natal"], "correta": 1},
        {"pergunta": "Qual é a capital de Pernambuco?", "alternativas": ["Maceió", "Fortaleza", "Recife"], "correta": 2},
        {"pergunta": "Qual é a capital da Bahia?", "alternativas": ["Salvador", "Aracaju", "Vitória"], "correta": 0},
        {"pergunta": "Qual é a capital do Ceará?", "alternativas": ["Teresina", "Fortaleza", "São Luís"], "correta": 1},
        {"pergunta": "Qual é a capital do Amazonas?", "alternativas": ["Belém", "Porto Velho", "Manaus"], "correta": 2},
    ],

    "Língua Portuguesa": [
        {"pergunta": "Qual palavra é um substantivo?", "alternativas": ["Correr", "Bonito", "Casa"], "correta": 2},
        {"pergunta": "Qual palavra é um verbo?", "alternativas": ["Cantar", "Azul", "Mesa"], "correta": 0},
        {"pergunta": "Qual palavra está escrita corretamente?", "alternativas": ["Excessão", "Exceção", "Eceção"], "correta": 1},
        {"pergunta": "Qual é o plural de cidadão?", "alternativas": ["Cidadões", "Cidadães", "Cidadãos"], "correta": 2},
        {"pergunta": "Qual palavra é sinônimo de rápido?", "alternativas": ["Veloz", "Lento", "Parado"], "correta": 0},
    ],

    "Matemática Rápida": [
        {"pergunta": "Quanto é 7 vezes 8?", "alternativas": ["56", "54", "64"], "correta": 0},
        {"pergunta": "Quanto é 144 dividido por 12?", "alternativas": ["14", "12", "10"], "correta": 1},
        {"pergunta": "Quanto é 15 por cento de 200?", "alternativas": ["20", "40", "30"], "correta": 2},
        {"pergunta": "Qual é a raiz quadrada de 81?", "alternativas": ["9", "8", "7"], "correta": 0},
        {"pergunta": "Quanto é 25 mais 37?", "alternativas": ["52", "62", "72"], "correta": 1},
    ],

    "Mitos e Verdades do Dia a Dia": [
        {"pergunta": "Engolir chiclete faz ele ficar sete anos no estômago?", "alternativas": ["Sim", "Não", "Somente em crianças"], "correta": 1},
        {"pergunta": "Raspar o pelo faz ele crescer mais grosso de verdade?", "alternativas": ["Sim, sempre", "Somente no inverno", "Não"], "correta": 2},
        {"pergunta": "Ler com pouca luz estraga permanentemente a visão?", "alternativas": ["Não, mas pode causar desconforto temporário", "Sim, sempre causa cegueira", "Só se o livro for digital"], "correta": 0},
        {"pergunta": "Estalar os dedos causa artrite automaticamente?", "alternativas": ["Sim, sempre", "Não há evidência de que cause artrite automaticamente", "Somente na mão esquerda"], "correta": 1},
        {"pergunta": "Tomar água ajuda a manter o corpo hidratado?", "alternativas": ["Não", "Somente durante o verão", "Sim"], "correta": 2},
    ],

    "Frases que Todo Professor Já Falou": [
        {"pergunta": "Complete: A prova vai ser baseada no que foi...", "alternativas": ["dito no recreio", "postado no grupo da família", "dado em sala"], "correta": 2},
        {"pergunta": "Complete: Pode guardar o material, agora é...", "alternativas": ["prova", "intervalo eterno", "hora de ir embora"], "correta": 0},
        {"pergunta": "Complete: Quem terminou pode ficar em...", "alternativas": ["pé", "silêncio", "casa"], "correta": 1},
        {"pergunta": "Complete: Eu vou esperar todo mundo ficar em...", "alternativas": ["fila do lanche", "casa", "silêncio"], "correta": 2},
        {"pergunta": "Complete: Essa conversa eu quero ver na hora da...", "alternativas": ["prova", "merenda", "saída"], "correta": 0},
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
