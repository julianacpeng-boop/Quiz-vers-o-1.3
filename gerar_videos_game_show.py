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
    "Fatos Engraçados sobre a História das Eleições": [
        {
            "pergunta": "Qual animal virou símbolo de voto de protesto em São Paulo em 1959?",
            "alternativas": [
                "Um cavalo",
                "Um papagaio",
                "Uma rinoceronte"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual primata ficou famoso como candidato de protesto no Rio em 1988?",
            "alternativas": [
                "Macaco Tião",
                "Gorila Zico",
                "Mico-leão"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual objeto virou símbolo da campanha presidencial de Jânio Quadros?",
            "alternativas": [
                "Vassoura",
                "Chapéu",
                "Panela"
            ],
            "correta": 0
        },
        {
            "pergunta": "Em que década a urna eletrônica começou a ser usada em eleições brasileiras?",
            "alternativas": [
                "Década de 1970",
                "Década de 2010",
                "Década de 1990"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual foi o primeiro presidente civil eleito diretamente após a Proclamação da República?",
            "alternativas": [
                "Prudente de Morais",
                "Getúlio Vargas",
                "Deodoro da Fonseca"
            ],
            "correta": 0
        }
    ],
    "Eleições 2026": [
        {
            "pergunta": "Em que data acontece o primeiro turno das Eleições 2026?",
            "alternativas": [
                "4 de outubro",
                "25 de outubro",
                "11 de outubro"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quando está previsto o segundo turno, quando necessário?",
            "alternativas": [
                "25 de outubro",
                "18 de outubro",
                "1º de novembro"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quantas escolhas o eleitor faz na urna no primeiro turno de 2026?",
            "alternativas": [
                "Cinco",
                "Quatro",
                "Seis"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual cargo aparece primeiro na ordem de votação de 2026?",
            "alternativas": [
                "Deputado federal",
                "Governador",
                "Presidente"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quantas vagas para o Senado estão em disputa nas Eleições 2026?",
            "alternativas": [
                "81",
                "54",
                "27"
            ],
            "correta": 1
        }
    ],
    "Fatos Engraçados do Rock in Rio 2026": [
        {
            "pergunta": "Qual atração de 2026 tem um número escrito no próprio nome?",
            "alternativas": [
                "Foo Fighters",
                "Twenty One Pilots",
                "Halsey"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual grupo de 2026 tem fãs conhecidos como STAYs?",
            "alternativas": [
                "Maroon 5",
                "Black Eyed Peas",
                "Stray Kids"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual artista do Palco Mundo de 2026 tem 'John' no nome artístico?",
            "alternativas": [
                "J Balvin",
                "Elton John",
                "Jon Batiste"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual banda retorna ao Rock in Rio em 2026 sete anos depois de sua apresentação anterior?",
            "alternativas": [
                "The Hives",
                "Sepultura",
                "Foo Fighters"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual atração de 2026 tem a palavra 'Eyes' no nome?",
            "alternativas": [
                "Black Eyed Peas",
                "Nova Twins",
                "Twenty One Pilots"
            ],
            "correta": 0
        }
    ],
    "Famosos no Rock in Rio 2026": [
        {
            "pergunta": "Quem é o headliner do Palco Mundo em 4 de setembro de 2026?",
            "alternativas": [
                "Maroon 5",
                "Stray Kids",
                "Foo Fighters"
            ],
            "correta": 2
        },
        {
            "pergunta": "Quem lidera o Palco Mundo em 7 de setembro de 2026?",
            "alternativas": [
                "Avenged Sevenfold",
                "Calvin Harris",
                "Elton John"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual grupo de K-pop é headliner em 11 de setembro de 2026?",
            "alternativas": [
                "NEXZ",
                "HWASA",
                "Stray Kids"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual banda é headliner em 12 de setembro de 2026?",
            "alternativas": [
                "Foo Fighters",
                "Maroon 5",
                "Twenty One Pilots"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual artista brasileira está no Palco Mundo em 13 de setembro de 2026?",
            "alternativas": [
                "Ivete Sangalo",
                "Anitta",
                "Luísa Sonza"
            ],
            "correta": 0
        }
    ],
    "Curiosidades dos Presidentes do Brasil": [
        {
            "pergunta": "Quem foi o primeiro presidente do Brasil?",
            "alternativas": [
                "Floriano Peixoto",
                "Deodoro da Fonseca",
                "Prudente de Morais"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual presidente ficou conhecido pelo plano de '50 anos em 5'?",
            "alternativas": [
                "Jânio Quadros",
                "Juscelino Kubitschek",
                "João Goulart"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual presidente tinha o sobrenome curioso 'Café Filho'?",
            "alternativas": [
                "João Café Filho",
                "Itamar Franco",
                "Tancredo Neves"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quem governava o Brasil na inauguração de Brasília em 1960?",
            "alternativas": [
                "Eurico Gaspar Dutra",
                "Juscelino Kubitschek",
                "Getúlio Vargas"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual presidente renunciou ao cargo em 1961 poucos meses após tomar posse?",
            "alternativas": [
                "José Sarney",
                "Jânio Quadros",
                "João Goulart"
            ],
            "correta": 1
        }
    ],
    "Campanhas Eleitorais que Viraram Memória Popular": [
        {
            "pergunta": "A vassoura ficou associada à campanha de qual político?",
            "alternativas": [
                "Juscelino Kubitschek",
                "Jânio Quadros",
                "Ulysses Guimarães"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual recurso musical é criado para fixar o nome de um candidato na memória?",
            "alternativas": [
                "Vinheta de cinema",
                "Trilha instrumental",
                "Jingle eleitoral"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual frase ficou associada ao projeto desenvolvimentista de Juscelino Kubitschek?",
            "alternativas": [
                "Diretas Já",
                "50 anos em 5",
                "Brasil, ame-o"
            ],
            "correta": 1
        },
        {
            "pergunta": "Em qual eleição presidencial a televisão teve papel marcante nos debates entre candidatos?",
            "alternativas": [
                "1945",
                "1930",
                "1989"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual movimento popular dos anos 1980 defendia eleições diretas para presidente?",
            "alternativas": [
                "Diretas Já",
                "Queremismo",
                "Tenentismo"
            ],
            "correta": 0
        }
    ],
    "Urnas Eletrônicas e Curiosidades da Votação": [
        {
            "pergunta": "Em qual década a urna eletrônica estreou no Brasil?",
            "alternativas": [
                "Década de 2010",
                "Década de 1960",
                "Década de 1990"
            ],
            "correta": 2
        },
        {
            "pergunta": "O que o eleitor digita principalmente para escolher uma candidatura na urna?",
            "alternativas": [
                "CEP",
                "CPF",
                "Número do candidato ou legenda"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual tecla normalmente confirma o voto?",
            "alternativas": [
                "Branco",
                "Confirma",
                "Corrige"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual recurso ajuda a identificar visualmente a candidatura na tela?",
            "alternativas": [
                "Brasão do estado",
                "Mapa da cidade",
                "Foto do candidato"
            ],
            "correta": 2
        },
        {
            "pergunta": "Em 2000, a votação eletrônica passou a alcançar o quê?",
            "alternativas": [
                "Todo o eleitorado do país",
                "Somente cidades com mais de 1 milhão",
                "Somente capitais"
            ],
            "correta": 0
        }
    ],
    "Símbolos e Curiosidades da Democracia": [
        {
            "pergunta": "Qual objeto representa de forma direta o ato de escolher representantes?",
            "alternativas": [
                "Ampulheta",
                "Bússola",
                "Urna"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual documento reúne as regras fundamentais de um país?",
            "alternativas": [
                "Constituição",
                "Dicionário",
                "Atlas"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quais são os três Poderes da República no Brasil?",
            "alternativas": [
                "Câmara, Senado e STF",
                "União, estados e municípios",
                "Executivo, Legislativo e Judiciário"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual palavra descreve a participação da população na escolha de representantes?",
            "alternativas": [
                "Censo",
                "Voto",
                "Inventário"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual princípio significa que diferentes opiniões podem coexistir na democracia?",
            "alternativas": [
                "Herança",
                "Pluralismo",
                "Monarquia"
            ],
            "correta": 1
        }
    ],
    "Como Funcionam as Eleições no Brasil": [
        {
            "pergunta": "Qual órgão organiza e regulamenta as eleições brasileiras em âmbito nacional?",
            "alternativas": [
                "IBGE",
                "Banco Central",
                "TSE"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual sistema é usado para eleger deputados no Brasil?",
            "alternativas": [
                "Sorteio",
                "Sistema proporcional",
                "Rodízio"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual cargo pode ter segundo turno quando ninguém alcança a maioria exigida?",
            "alternativas": [
                "Presidente",
                "Senador",
                "Deputado federal"
            ],
            "correta": 0
        },
        {
            "pergunta": "De quanto em quanto tempo ocorrem as eleições gerais para presidente?",
            "alternativas": [
                "Dois anos",
                "Quatro anos",
                "Seis anos"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual aplicativo oficial permite consultar dados eleitorais do próprio eleitor?",
            "alternativas": [
                "Meu INSS",
                "Carteira de Trabalho",
                "e-Título"
            ],
            "correta": 2
        }
    ],
    "Curiosidades sobre Prefeitos, Governadores e Presidentes": [
        {
            "pergunta": "Quem chefia o Poder Executivo de um município?",
            "alternativas": [
                "Prefeito",
                "Governador",
                "Senador"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quem chefia o Poder Executivo de um estado?",
            "alternativas": [
                "Deputado federal",
                "Governador",
                "Vereador"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem chefia o Poder Executivo federal?",
            "alternativas": [
                "Presidente da Câmara",
                "Presidente do STF",
                "Presidente da República"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual desses cargos tem mandato de quatro anos?",
            "alternativas": [
                "Prefeito",
                "Senador",
                "Ministro do STF"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual cargo possui vice para substituir o titular quando necessário?",
            "alternativas": [
                "Deputado estadual",
                "Governador",
                "Vereador"
            ],
            "correta": 1
        }
    ],
    "Momentos Inusitados da Política Brasileira": [
        {
            "pergunta": "Qual presidente eleito em 1985 morreu antes de tomar posse?",
            "alternativas": [
                "Itamar Franco",
                "José Sarney",
                "Tancredo Neves"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual presidente renunciou em 1961 após poucos meses no cargo?",
            "alternativas": [
                "Jânio Quadros",
                "Eurico Dutra",
                "Café Filho"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual presidente ficou apenas poucos dias no cargo em novembro de 1955?",
            "alternativas": [
                "Nereu Ramos",
                "Carlos Luz",
                "Café Filho"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem assumiu a Presidência em 1985 no lugar de Tancredo Neves?",
            "alternativas": [
                "Itamar Franco",
                "Fernando Collor",
                "José Sarney"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual presidente brasileiro ficou conhecido pela campanha com uma vassoura?",
            "alternativas": [
                "Juscelino Kubitschek",
                "Getúlio Vargas",
                "Jânio Quadros"
            ],
            "correta": 2
        }
    ],
    "Frases Históricas da Política Brasileira": [
        {
            "pergunta": "A frase 'Saio da vida para entrar na História' aparece na carta-testamento de quem?",
            "alternativas": [
                "Getúlio Vargas",
                "Jânio Quadros",
                "Tancredo Neves"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual slogan ficou associado ao governo de Juscelino Kubitschek?",
            "alternativas": [
                "Ordem e Progresso",
                "O petróleo é nosso",
                "50 anos em 5"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual expressão marcou o movimento por eleições presidenciais diretas nos anos 1980?",
            "alternativas": [
                "Diretas Já",
                "Queremos votar",
                "Brasil Novo"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual frase ficou ligada à campanha nacionalista em defesa da exploração brasileira do petróleo?",
            "alternativas": [
                "Açúcar é energia",
                "Brasil em marcha",
                "O petróleo é nosso"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual jingle começava com a ideia de 'varrer' a corrupção?",
            "alternativas": [
                "Varre, varre, vassourinha",
                "Lula Lá",
                "Pra Frente Brasil"
            ],
            "correta": 0
        }
    ],
    "Curiosidades sobre o Congresso Nacional": [
        {
            "pergunta": "O Congresso Nacional brasileiro é formado por quais duas Casas?",
            "alternativas": [
                "STF e Senado",
                "Câmara Municipal e Senado",
                "Câmara dos Deputados e Senado Federal"
            ],
            "correta": 2
        },
        {
            "pergunta": "Quantos senadores compõem o Senado Federal?",
            "alternativas": [
                "54",
                "81",
                "100"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quantos deputados federais compõem a Câmara dos Deputados?",
            "alternativas": [
                "400",
                "513",
                "300"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quanto dura o mandato de um deputado federal?",
            "alternativas": [
                "Seis anos",
                "Quatro anos",
                "Oito anos"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quanto dura o mandato de um senador?",
            "alternativas": [
                "Oito anos",
                "Dez anos",
                "Quatro anos"
            ],
            "correta": 0
        }
    ],
    "Brasília e os Bastidores do Poder": [
        {
            "pergunta": "Em que ano Brasília foi inaugurada como capital do Brasil?",
            "alternativas": [
                "1950",
                "1960",
                "1970"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem foi o principal arquiteto dos edifícios monumentais de Brasília?",
            "alternativas": [
                "Oscar Niemeyer",
                "Lúcio Costa",
                "Burle Marx"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual palácio é a residência oficial da Presidência da República?",
            "alternativas": [
                "Palácio do Planalto",
                "Palácio Itamaraty",
                "Palácio da Alvorada"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual edifício é a sede de trabalho da Presidência da República?",
            "alternativas": [
                "Congresso Nacional",
                "Palácio do Planalto",
                "Palácio da Alvorada"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem elaborou o plano urbanístico vencedor de Brasília?",
            "alternativas": [
                "Affonso Reidy",
                "Lúcio Costa",
                "Oscar Niemeyer"
            ],
            "correta": 1
        }
    ],
    "Leis Brasileiras que Parecem Inventadas": [
        {
            "pergunta": "O cartório pode recusar um prenome que exponha a pessoa ao ridículo?",
            "alternativas": [
                "Só depois dos 18 anos",
                "Não",
                "Sim"
            ],
            "correta": 2
        },
        {
            "pergunta": "Para compras feitas pela internet, qual prazo básico de arrependimento é previsto no CDC?",
            "alternativas": [
                "3 dias",
                "30 dias",
                "7 dias"
            ],
            "correta": 2
        },
        {
            "pergunta": "Pelo Código de Trânsito, dirigir usando calçado que não se firme nos pés pode resultar em quê?",
            "alternativas": [
                "Crime hediondo",
                "Nada",
                "Infração de trânsito"
            ],
            "correta": 2
        },
        {
            "pergunta": "A partir de qual idade o voto é facultativo no Brasil?",
            "alternativas": [
                "14 anos",
                "16 anos",
                "21 anos"
            ],
            "correta": 1
        },
        {
            "pergunta": "Para maiores de 70 anos, o voto no Brasil é o quê?",
            "alternativas": [
                "Obrigatório",
                "Proibido",
                "Facultativo"
            ],
            "correta": 2
        }
    ],
    "Curiosidades sobre a Constituição Brasileira": [
        {
            "pergunta": "Em que ano foi promulgada a atual Constituição brasileira?",
            "alternativas": [
                "1988",
                "2002",
                "1964"
            ],
            "correta": 0
        },
        {
            "pergunta": "Como ficou conhecida a Constituição de 1988?",
            "alternativas": [
                "Carta Trabalhista",
                "Constituição Cidadã",
                "Carta Imperial"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem presidiu a Assembleia Nacional Constituinte de 1987-1988?",
            "alternativas": [
                "Ulysses Guimarães",
                "Tancredo Neves",
                "José Sarney"
            ],
            "correta": 0
        },
        {
            "pergunta": "Em que mês a Constituição de 1988 foi promulgada?",
            "alternativas": [
                "Outubro",
                "Janeiro",
                "Julho"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual princípio aparece como fundamento da República no artigo 1º?",
            "alternativas": [
                "Censura prévia",
                "Dignidade da pessoa humana",
                "Monarquia"
            ],
            "correta": 1
        }
    ],
    "Coisas que Já Foram Proibidas no Brasil": [
        {
            "pergunta": "Qual prática foi criminalizada pelo Código Penal de 1890?",
            "alternativas": [
                "Xadrez",
                "Natação",
                "Capoeira"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual atividade esportiva feminina sofreu proibição oficial por décadas no século XX?",
            "alternativas": [
                "Tênis",
                "Futebol",
                "Vôlei"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual atividade foi proibida no país em 1946 e levou ao fechamento de estabelecimentos famosos?",
            "alternativas": [
                "Cassinos",
                "Cinema",
                "Teatro"
            ],
            "correta": 0
        },
        {
            "pergunta": "Durante parte do século XX, o Brasil restringiu fortemente a importação de quê?",
            "alternativas": [
                "Medicamentos",
                "Automóveis",
                "Livros"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual jogo de azar ficou associado à proibição dos cassinos?",
            "alternativas": [
                "Xadrez",
                "Dominó",
                "Roleta"
            ],
            "correta": 2
        }
    ],
    "Costumes Antigos que Hoje Parecem Estranhos": [
        {
            "pergunta": "Na Europa dos séculos XVII e XVIII, qual item de moda podia ser enorme e empoadíssimo?",
            "alternativas": [
                "Sapato esportivo",
                "Peruca",
                "Relógio"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual prática médica antiga usava pequenos animais para retirar sangue?",
            "alternativas": [
                "Acupuntura",
                "Inalação",
                "Sangria com sanguessugas"
            ],
            "correta": 2
        },
        {
            "pergunta": "Antes do despertador popular, quem podia bater nas janelas para acordar trabalhadores?",
            "alternativas": [
                "Carteiro",
                "Vendedor de leite",
                "Knocker-up"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual objeto era usado para iluminar ruas antes da eletricidade?",
            "alternativas": [
                "Televisão",
                "Farol de carro",
                "Lampião a gás"
            ],
            "correta": 2
        },
        {
            "pergunta": "Em muitas casas antigas, qual cômodo nem sempre existia dentro da residência?",
            "alternativas": [
                "Quarto",
                "Cozinha",
                "Banheiro"
            ],
            "correta": 2
        }
    ],
    "Profissões Estranhas que Já Existiram": [
        {
            "pergunta": "Qual profissional britânico acordava pessoas batendo nas janelas?",
            "alternativas": [
                "Coveiro",
                "Knocker-up",
                "Ferreiro"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem acendia manualmente os lampiões das ruas?",
            "alternativas": [
                "Relojoeiro",
                "Tipógrafo",
                "Acendedor de lampiões"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual profissão envolvia capturar roedores em cidades antigas?",
            "alternativas": [
                "Leitor público",
                "Caçador de ratos",
                "Guardador de pontes"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem cortava grandes blocos de gelo antes das geladeiras modernas?",
            "alternativas": [
                "Cortador de gelo",
                "Sapateiro",
                "Alfaiate"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quem lia textos em voz alta para operários de algumas fábricas de charutos?",
            "alternativas": [
                "Cobrador",
                "Porteiro",
                "Leitor de fábrica"
            ],
            "correta": 2
        }
    ],
    "Invenções que Surgiram por Acidente": [
        {
            "pergunta": "Qual aparelho ganhou impulso quando Percy Spencer percebeu que uma barra de chocolate derreteu perto de um magnetron?",
            "alternativas": [
                "Forno de micro-ondas",
                "Aspirador",
                "Liquidificador"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual adesivo nasceu de uma cola que inicialmente parecia fraca demais?",
            "alternativas": [
                "Fita isolante",
                "Supercola",
                "Post-it"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual material antiaderente foi descoberto quando um gás se transformou inesperadamente em um sólido?",
            "alternativas": [
                "Náilon",
                "PVC",
                "Teflon"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual sobremesa gelada é ligada à história de uma bebida deixada ao frio com um palito?",
            "alternativas": [
                "Gelatina",
                "Sorvete italiano",
                "Picolé"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual medicamento foi descoberto após Alexander Fleming observar contaminação por mofo?",
            "alternativas": [
                "Aspirina",
                "Penicilina",
                "Insulina"
            ],
            "correta": 1
        }
    ],
    "Erros que Viraram Grandes Descobertas": [
        {
            "pergunta": "Qual descoberta de Fleming começou com uma placa de cultura contaminada por mofo?",
            "alternativas": [
                "Vacina da gripe",
                "Penicilina",
                "Anestesia"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual radiação Wilhelm Röntgen percebeu durante experimentos com tubos de raios catódicos?",
            "alternativas": [
                "Ultravioleta",
                "Infravermelho",
                "Raios X"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual corante sintético surgiu quando William Perkin tentava produzir quinina?",
            "alternativas": [
                "Anil",
                "Carmim",
                "Malva"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual adesivo muito forte foi inicialmente considerado inadequado para miras ópticas por colar demais?",
            "alternativas": [
                "Cola escolar",
                "Cola quente",
                "Supercola"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual adoçante foi descoberto no século XIX após um pesquisador notar sabor doce relacionado ao trabalho de laboratório?",
            "alternativas": [
                "Sacarina",
                "Aspartame",
                "Stevia"
            ],
            "correta": 0
        }
    ],
    "Coincidências Históricas Impressionantes": [
        {
            "pergunta": "Quais dois ex-presidentes dos EUA morreram em 4 de julho de 1826?",
            "alternativas": [
                "John Adams e Thomas Jefferson",
                "Washington e Madison",
                "Lincoln e Grant"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quem nasceu no mesmo dia, 12 de fevereiro de 1809, que Abraham Lincoln?",
            "alternativas": [
                "Isaac Newton",
                "Albert Einstein",
                "Charles Darwin"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual escritor nasceu em 1835, ano da passagem do cometa Halley, e morreu em 1910, na passagem seguinte?",
            "alternativas": [
                "Mark Twain",
                "Charles Dickens",
                "Jules Verne"
            ],
            "correta": 0
        },
        {
            "pergunta": "Além de John F. Kennedy, qual escritor morreu em 22 de novembro de 1963?",
            "alternativas": [
                "Aldous Huxley",
                "George Orwell",
                "Ernest Hemingway"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual outro escritor também morreu em 22 de novembro de 1963?",
            "alternativas": [
                "C. S. Lewis",
                "J. R. R. Tolkien",
                "Agatha Christie"
            ],
            "correta": 0
        }
    ],
    "Reis e Rainhas com Hábitos Estranhos": [
        {
            "pergunta": "Qual czar russo criou um imposto sobre barbas para incentivar costumes ocidentais?",
            "alternativas": [
                "Pedro, o Grande",
                "Nicolau II",
                "Ivan III"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual rei francês ficou famoso por usar saltos altos como símbolo de status?",
            "alternativas": [
                "Luís XVI",
                "Luís XIV",
                "Carlos X"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual rainha francesa ficou conhecida por visuais muito elaborados e maquiagem muito clara no século XVIII?",
            "alternativas": [
                "Catarina de Médici",
                "Maria de Médici",
                "Maria Antonieta"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual rei francês sofreu episódios da chamada 'ilusão de vidro', acreditando que podia quebrar?",
            "alternativas": [
                "Luís XIII",
                "Francisco I",
                "Carlos VI"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual rainha britânica passou décadas usando luto após a morte do príncipe Albert?",
            "alternativas": [
                "Rainha Vitória",
                "Ana",
                "Elizabeth I"
            ],
            "correta": 0
        }
    ],
    "Tradições Estranhas ao Redor do Mundo": [
        {
            "pergunta": "Em qual país acontece a famosa batalha de tomates La Tomatina?",
            "alternativas": [
                "Espanha",
                "Itália",
                "México"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual festival indiano é conhecido por lançar pós coloridos?",
            "alternativas": [
                "Diwali",
                "Holi",
                "Onam"
            ],
            "correta": 1
        },
        {
            "pergunta": "Em qual país ocorre a famosa corrida atrás de um queijo em Cooper's Hill?",
            "alternativas": [
                "Inglaterra",
                "França",
                "Suíça"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual país é famoso por campeonatos de carregar a esposa?",
            "alternativas": [
                "Portugal",
                "Finlândia",
                "Canadá"
            ],
            "correta": 1
        },
        {
            "pergunta": "Em qual país acontece o festival de lama de Boryeong?",
            "alternativas": [
                "Japão",
                "Tailândia",
                "Coreia do Sul"
            ],
            "correta": 2
        }
    ],
    "Festivais Mais Diferentes do Mundo": [
        {
            "pergunta": "Qual festival espanhol transforma uma cidade em uma batalha de tomates?",
            "alternativas": [
                "La Tomatina",
                "Oktoberfest",
                "Sanremo"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual festival indiano é conhecido como Festival das Cores?",
            "alternativas": [
                "Holi",
                "Vesak",
                "Diwali"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual evento japonês é famoso por enormes esculturas de neve?",
            "alternativas": [
                "Festival de Neve de Sapporo",
                "Gion Matsuri",
                "Awa Odori"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual festival escocês termina tradicionalmente com a queima de uma réplica de navio viking?",
            "alternativas": [
                "Burning Man",
                "Glastonbury",
                "Up Helly Aa"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual festival sul-coreano é centrado em muita lama?",
            "alternativas": [
                "Lantern Festival",
                "Chuseok",
                "Boryeong Mud Festival"
            ],
            "correta": 2
        }
    ],
    "Bastidores de Grandes Festivais de Música": [
        {
            "pergunta": "Em que tipo de propriedade acontece o Glastonbury Festival?",
            "alternativas": [
                "Um navio",
                "Um estádio coberto",
                "Uma fazenda"
            ],
            "correta": 2
        },
        {
            "pergunta": "Em qual região dos EUA acontece o Coachella?",
            "alternativas": [
                "Alasca",
                "Deserto da Califórnia",
                "Flórida"
            ],
            "correta": 1
        },
        {
            "pergunta": "Como é conhecido o espaço do Rock in Rio onde o festival é montado?",
            "alternativas": [
                "Cidade do Rock",
                "Vila da Música",
                "Parque do Rock"
            ],
            "correta": 0
        },
        {
            "pergunta": "Em qual país nasceu o Tomorrowland?",
            "alternativas": [
                "Bélgica",
                "Espanha",
                "Canadá"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual festival de 1969 se tornou símbolo da contracultura?",
            "alternativas": [
                "Lollapalooza",
                "Woodstock",
                "Primavera Sound"
            ],
            "correta": 1
        }
    ],
    "Shows que Entraram para a História": [
        {
            "pergunta": "Qual banda teve uma apresentação lendária no Live Aid de 1985?",
            "alternativas": [
                "Queen",
                "Coldplay",
                "Oasis"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual banda tocou no telhado da Apple Corps em 1969?",
            "alternativas": [
                "Rolling Stones",
                "The Beatles",
                "The Who"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual banda gravou um dos MTV Unplugged mais famosos em 1993?",
            "alternativas": [
                "Nirvana",
                "Pearl Jam",
                "U2"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual cantora teve sua apresentação no Coachella de 2018 apelidada de 'Beychella'?",
            "alternativas": [
                "Rihanna",
                "Adele",
                "Beyoncé"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual artista fez um megashow gratuito em Copacabana em 2024?",
            "alternativas": [
                "Madonna",
                "Cher",
                "Lady Gaga"
            ],
            "correta": 0
        }
    ],
    "Artistas que Começaram Cantando em Lugares Inusitados": [
        {
            "pergunta": "Qual cantor britânico ficou conhecido por tocar nas ruas antes da fama?",
            "alternativas": [
                "Sam Smith",
                "Harry Styles",
                "Ed Sheeran"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual artista foi descoberto após vídeos caseiros publicados no YouTube?",
            "alternativas": [
                "Bruno Mars",
                "Justin Bieber",
                "Shawn Mendes"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual cantora britânico-albanesa publicava covers no YouTube ainda adolescente?",
            "alternativas": [
                "Dua Lipa",
                "Adele",
                "Rita Ora"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual artista australiana ganhou atenção enquanto fazia apresentações de rua em Byron Bay?",
            "alternativas": [
                "Sia",
                "Kylie Minogue",
                "Tones and I"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual cantor canadense ganhou seguidores no Vine antes do sucesso mundial?",
            "alternativas": [
                "Drake",
                "The Weeknd",
                "Shawn Mendes"
            ],
            "correta": 2
        }
    ],
    "Erros e Gafes em Shows Ao Vivo": [
        {
            "pergunta": "Qual cantora reiniciou sua homenagem a George Michael no Grammy de 2017 após errar o começo?",
            "alternativas": [
                "Beyoncé",
                "Adele",
                "Pink"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual artista teve o cabelo preso em um ventilador durante um show em Montreal e continuou cantando?",
            "alternativas": [
                "Katy Perry",
                "Rihanna",
                "Beyoncé"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual vocalista quebrou a perna no palco em 2015 e voltou para terminar o show?",
            "alternativas": [
                "Chris Martin",
                "Dave Grohl",
                "Bono"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual vocalista do Metallica sofreu queimaduras com efeitos pirotécnicos em 1992?",
            "alternativas": [
                "James Hetfield",
                "Kirk Hammett",
                "Lars Ulrich"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual cantora teve um problema de playback no Saturday Night Live em 2004 e saiu do palco após uma dança improvisada?",
            "alternativas": [
                "Kelly Clarkson",
                "Avril Lavigne",
                "Ashlee Simpson"
            ],
            "correta": 2
        }
    ],
    "Objetos Estranhos Levados por Artistas em Turnês": [
        {
            "pergunta": "Qual vocalista do Foo Fighters fez shows sentado em um trono especialmente criado após quebrar a perna?",
            "alternativas": [
                "Dave Grohl",
                "Axl Rose",
                "Bono"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual banda usou um enorme limão espelhado como elemento de palco na turnê PopMart?",
            "alternativas": [
                "Queen",
                "Muse",
                "U2"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual banda ficou famosa por usar um porco inflável gigante em apresentações?",
            "alternativas": [
                "Kiss",
                "Pink Floyd",
                "The Who"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual cantora usa tecidos e estruturas aéreas em várias turnês para fazer acrobacias sobre o público?",
            "alternativas": [
                "Lorde",
                "Pink",
                "Adele"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual banda é conhecida por levar enormes sinos e canhões cenográficos ao palco?",
            "alternativas": [
                "Maroon 5",
                "AC/DC",
                "Coldplay"
            ],
            "correta": 1
        }
    ],
    "Exigências Curiosas de Camarins de Famosos": [
        {
            "pergunta": "Como é chamado o documento com exigências técnicas e de hospitalidade de um artista?",
            "alternativas": [
                "Release",
                "Rider",
                "Setlist"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual banda ficou famosa pela cláusula pedindo M&M's sem os marrons?",
            "alternativas": [
                "Aerosmith",
                "Bon Jovi",
                "Van Halen"
            ],
            "correta": 2
        },
        {
            "pergunta": "Por que a cláusula dos M&M's do Van Halen era útil?",
            "alternativas": [
                "Para decorar o camarim",
                "Para escolher sabores",
                "Para testar se o contrato havia sido lido com atenção"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual músico teve um rider que incluía uma receita de guacamole?",
            "alternativas": [
                "Jack White",
                "Sting",
                "Ed Sheeran"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual parte de um rider trata de palco, som, luz e energia?",
            "alternativas": [
                "Rider técnico",
                "Lista de convidados",
                "Hospitalidade"
            ],
            "correta": 0
        }
    ],
    "Famosos que Têm Talentos Inesperados": [
        {
            "pergunta": "Qual ator e comediante é também um premiado tocador de banjo?",
            "alternativas": [
                "Ben Stiller",
                "Jim Carrey",
                "Steve Martin"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual atriz chegou a competir seriamente no tiro com arco?",
            "alternativas": [
                "Geena Davis",
                "Julia Roberts",
                "Sandra Bullock"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual ator treinou como engolidor de fogo antes da fama?",
            "alternativas": [
                "Hugh Jackman",
                "George Clooney",
                "Pierce Brosnan"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual ator de ação também é conhecido por tocar flauta?",
            "alternativas": [
                "Vin Diesel",
                "Jason Statham",
                "Terry Crews"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual ator é também mágico e já presidiu a Academy of Magical Arts?",
            "alternativas": [
                "Tom Hanks",
                "Neil Patrick Harris",
                "Ryan Reynolds"
            ],
            "correta": 1
        }
    ],
    "Celebridades com Profissões Antes da Fama": [
        {
            "pergunta": "Qual ator trabalhou como carpinteiro antes de virar astro de Hollywood?",
            "alternativas": [
                "Harrison Ford",
                "Brad Pitt",
                "Tom Cruise"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual ator também teve carreira profissional no futebol americano antes da fama?",
            "alternativas": [
                "Tyler James Williams",
                "Terry Crews",
                "Chris Rock"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual ator de 'The Hangover' era médico antes de se dedicar à comédia?",
            "alternativas": [
                "Bradley Cooper",
                "Ken Jeong",
                "Zach Galifianakis"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual ator de 'Pulp Fiction' trabalhou como bombeiro em Nova York antes da fama?",
            "alternativas": [
                "Samuel L. Jackson",
                "John Travolta",
                "Steve Buscemi"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual ator de 'Taxi' chegou a trabalhar como cabeleireiro antes da carreira artística?",
            "alternativas": [
                "Danny DeVito",
                "Robert De Niro",
                "Al Pacino"
            ],
            "correta": 0
        }
    ],
    "Nomes Verdadeiros de Famosos": [
        {
            "pergunta": "Qual é o nome de nascimento de Bruno Mars?",
            "alternativas": [
                "Brandon Cole",
                "Peter Hernandez",
                "Michael Smith"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual é o primeiro nome de Lady Gaga?",
            "alternativas": [
                "Giovanna",
                "Stefani",
                "Francesca"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual é o nome de nascimento de The Weeknd?",
            "alternativas": [
                "Drake Graham",
                "Abel Tesfaye",
                "Shawn Carter"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual é o nome de nascimento da cantora Anitta?",
            "alternativas": [
                "Priscilla Alcantara",
                "Larissa de Macedo Machado",
                "Marina Sena"
            ],
            "correta": 1
        },
        {
            "pergunta": "Katy Perry nasceu com qual sobrenome?",
            "alternativas": [
                "Stefani",
                "Johnson",
                "Hudson"
            ],
            "correta": 2
        }
    ],
    "Famosos que Mudaram Completamente de Visual": [
        {
            "pergunta": "Qual artista assumiu o cabelo vermelho intenso na fase de Ziggy Stardust?",
            "alternativas": [
                "David Bowie",
                "Freddie Mercury",
                "Elton John"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual cantora surpreendeu ao cortar o cabelo bem curto e platinado em 2012?",
            "alternativas": [
                "Selena Gomez",
                "Miley Cyrus",
                "Ariana Grande"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual cantora trocou as raízes verde-neon por um visual loiro em 2021?",
            "alternativas": [
                "Halsey",
                "Lorde",
                "Billie Eilish"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual cantor cortou seus famosos dreadlocks antes da era 'Starboy'?",
            "alternativas": [
                "Drake",
                "Post Malone",
                "The Weeknd"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual cantora raspou o cabelo e as sobrancelhas publicamente em 2022?",
            "alternativas": [
                "Doja Cat",
                "Dua Lipa",
                "SZA"
            ],
            "correta": 0
        }
    ],
    "Encontros Inesperados entre Celebridades": [
        {
            "pergunta": "Qual dupla improvável se conheceu no programa de TV de Martha Stewart em 2008?",
            "alternativas": [
                "Cher e Drake",
                "Adele e Eminem",
                "Martha Stewart e Snoop Dogg"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual rapper cantou 'Stan' ao lado de Elton John no Grammy de 2001?",
            "alternativas": [
                "Eminem",
                "Jay-Z",
                "Kanye West"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual cantora encontrou a rainha Elizabeth II após uma apresentação no Royal Variety Performance de 2009?",
            "alternativas": [
                "Rihanna",
                "Beyoncé",
                "Lady Gaga"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual quarteto britânico posou em uma famosa sessão de fotos com Muhammad Ali em 1964?",
            "alternativas": [
                "Queen",
                "The Beatles",
                "The Rolling Stones"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual cantora participou de 'FourFiveSeconds' com Paul McCartney e Kanye West?",
            "alternativas": [
                "Rihanna",
                "Adele",
                "Beyoncé"
            ],
            "correta": 0
        }
    ],
    "Amizades Improváveis entre Famosos": [
        {
            "pergunta": "Qual apresentadora e empresária tornou-se grande amiga de Snoop Dogg?",
            "alternativas": [
                "Oprah Winfrey",
                "Martha Stewart",
                "Ellen DeGeneres"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual atriz de 'Friends' é amiga de Ed Sheeran e já o hospedou em sua casa?",
            "alternativas": [
                "Lisa Kudrow",
                "Jennifer Aniston",
                "Courteney Cox"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual rapper desenvolveu uma amizade pública com Elton John?",
            "alternativas": [
                "Drake",
                "50 Cent",
                "Eminem"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual cantora faz parte do trio de 'Only Murders in the Building' com Steve Martin e Martin Short?",
            "alternativas": [
                "Demi Lovato",
                "Selena Gomez",
                "Miley Cyrus"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual ex-jogador inglês mantém amizade de longa data com Snoop Dogg?",
            "alternativas": [
                "Wayne Rooney",
                "David Beckham",
                "Frank Lampard"
            ],
            "correta": 1
        }
    ],
    "Curiosidades sobre Tapetes Vermelhos": [
        {
            "pergunta": "Qual evento de moda acontece tradicionalmente na primeira segunda-feira de maio?",
            "alternativas": [
                "Oscar",
                "Met Gala",
                "Grammy"
            ],
            "correta": 1
        },
        {
            "pergunta": "Em qual cidade francesa acontece o famoso tapete vermelho do Festival de Cannes?",
            "alternativas": [
                "Paris",
                "Nice",
                "Cannes"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual premiação trocou temporariamente o tradicional tapete vermelho por um tom champanhe em 2023?",
            "alternativas": [
                "Emmy",
                "Grammy",
                "Oscar"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual museu recebe o Met Gala?",
            "alternativas": [
                "Metropolitan Museum of Art",
                "MoMA PS1",
                "Louvre"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual peça de roupa é frequentemente associada ao código 'black tie' masculino?",
            "alternativas": [
                "Bermuda",
                "Smoking",
                "Macacão esportivo"
            ],
            "correta": 1
        }
    ],
    "Premiações que Tiveram Momentos Inusitados": [
        {
            "pergunta": "Em 2017, qual filme foi anunciado por engano como vencedor de Melhor Filme antes da correção para 'Moonlight'?",
            "alternativas": [
                "Arrival",
                "La La Land",
                "Lion"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem interrompeu o discurso de Taylor Swift no VMA de 2009?",
            "alternativas": [
                "Kanye West",
                "Jay-Z",
                "Drake"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual ator protagonizou um tapa em Chris Rock durante o Oscar de 2022?",
            "alternativas": [
                "Denzel Washington",
                "Jamie Foxx",
                "Will Smith"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual atriz tropeçou ao subir as escadas para receber o Oscar em 2013?",
            "alternativas": [
                "Anne Hathaway",
                "Jennifer Lawrence",
                "Emma Stone"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual ator chamou Idina Menzel de um nome errado no Oscar de 2014?",
            "alternativas": [
                "John Travolta",
                "Ben Affleck",
                "Nicolas Cage"
            ],
            "correta": 0
        }
    ],
    "Bastidores de Videoclipes Famosos": [
        {
            "pergunta": "Quem dirigiu o videoclipe de 'Thriller', de Michael Jackson?",
            "alternativas": [
                "John Landis",
                "Spike Lee",
                "Steven Spielberg"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual técnica de animação marcou o clipe de 'Take on Me', do a-ha?",
            "alternativas": [
                "Claymation",
                "Rotoscopia",
                "Stop motion"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem dança no famoso clipe de 'Chandelier', de Sia?",
            "alternativas": [
                "Maddie Ziegler",
                "Millie Bobby Brown",
                "JoJo Siwa"
            ],
            "correta": 0
        },
        {
            "pergunta": "Quem dirigiu o clipe de 'This Is America', de Childish Gambino?",
            "alternativas": [
                "David Fincher",
                "Hiro Murai",
                "Michel Gondry"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual clipe de Beyoncé ficou famoso pelo cenário minimalista e coreografia com duas dançarinas?",
            "alternativas": [
                "Formation",
                "Halo",
                "Single Ladies"
            ],
            "correta": 2
        }
    ],
    "Músicas que Quase Tiveram Outro Nome": [
        {
            "pergunta": "Qual música dos Beatles teve o título provisório 'Scrambled Eggs'?",
            "alternativas": [
                "Let It Be",
                "Help!",
                "Yesterday"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual música de Paul McCartney começou como 'Hey Jules'?",
            "alternativas": [
                "Hey Jude",
                "Penny Lane",
                "Let It Be"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual música de John Lennon tinha inicialmente o título 'Maharishi'?",
            "alternativas": [
                "Dear Prudence",
                "Julia",
                "Sexy Sadie"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual música dos Beatles teve o título de trabalho 'Bad Finger Boogie'?",
            "alternativas": [
                "Come Together",
                "Something",
                "With a Little Help from My Friends"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual música de George Harrison teve o título provisório 'Granny Smith'?",
            "alternativas": [
                "Taxman",
                "Here Comes the Sun",
                "Love You To"
            ],
            "correta": 2
        }
    ],
    "Artistas que Recusaram Grandes Sucessos": [
        {
            "pergunta": "Qual hit de Rihanna foi oferecido anteriormente à equipe de Britney Spears?",
            "alternativas": [
                "Work",
                "Diamonds",
                "Umbrella"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual música de Britney Spears havia sido oferecida antes ao TLC?",
            "alternativas": [
                "Toxic",
                "...Baby One More Time",
                "Oops!... I Did It Again"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual hit gravado por Britney Spears foi inicialmente oferecido a Kylie Minogue?",
            "alternativas": [
                "Circus",
                "Toxic",
                "Womanizer"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual música Lady Gaga escreveu inicialmente para Britney Spears, que não a lançou?",
            "alternativas": [
                "Alejandro",
                "Poker Face",
                "Telephone"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual hit de Sia foi escrito pensando em Rihanna antes de Sia gravá-lo?",
            "alternativas": [
                "Elastic Heart",
                "Chandelier",
                "Cheap Thrills"
            ],
            "correta": 2
        }
    ],
    "Covers que Ficaram Mais Famosos que o Original": [
        {
            "pergunta": "Quem gravou originalmente 'I Will Always Love You' antes da versão de Whitney Houston?",
            "alternativas": [
                "Cher",
                "Dolly Parton",
                "Celine Dion"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem popularizou mundialmente 'Nothing Compares 2 U' em 1990?",
            "alternativas": [
                "Annie Lennox",
                "Sinéad O'Connor",
                "Madonna"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual banda gravou originalmente 'Torn' antes do sucesso de Natalie Imbruglia?",
            "alternativas": [
                "The Cranberries",
                "Ednaswap",
                "Garbage"
            ],
            "correta": 1
        },
        {
            "pergunta": "Quem transformou 'Girls Just Want to Have Fun' em um grande hit nos anos 1980?",
            "alternativas": [
                "Debbie Harry",
                "Pat Benatar",
                "Cyndi Lauper"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual cantor lançou uma versão marcante de 'Hurt', originalmente do Nine Inch Nails?",
            "alternativas": [
                "Johnny Cash",
                "Willie Nelson",
                "Bob Dylan"
            ],
            "correta": 0
        }
    ],
    "Histórias Engraçadas por Trás de Músicas Famosas": [
        {
            "pergunta": "Qual música nasceu de uma melodia que Paul McCartney disse ter sonhado?",
            "alternativas": [
                "Help!",
                "Yesterday",
                "Yellow Submarine"
            ],
            "correta": 1
        },
        {
            "pergunta": "O riff inicial de qual música do Guns N' Roses começou como um exercício/brincadeira de guitarra de Slash?",
            "alternativas": [
                "November Rain",
                "Patience",
                "Sweet Child o' Mine"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual música do Blur manteve como título final o simples nome provisório usado no estúdio?",
            "alternativas": [
                "Song 2",
                "Parklife",
                "Coffee & TV"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual hit de Lou Bega reaproveita a base de uma composição instrumental de Pérez Prado?",
            "alternativas": [
                "Mambo No. 5",
                "Macarena",
                "Blue"
            ],
            "correta": 0
        },
        {
            "pergunta": "Qual hit do Hanson tem um título formado por sílabas sem significado literal específico?",
            "alternativas": [
                "MMMBop",
                "This Time Around",
                "Where's the Love"
            ],
            "correta": 0
        }
    ],
    "Curiosidades sobre Fãs e Fandoms Famosos": [
        {
            "pergunta": "Como são conhecidos os fãs de Taylor Swift?",
            "alternativas": [
                "Beliebers",
                "Swifties",
                "Little Monsters"
            ],
            "correta": 1
        },
        {
            "pergunta": "Qual nome é usado para os fãs de Justin Bieber?",
            "alternativas": [
                "Beliebers",
                "Directioners",
                "Arianators"
            ],
            "correta": 0
        },
        {
            "pergunta": "Como é conhecido o fandom do BTS?",
            "alternativas": [
                "MOA",
                "STAY",
                "ARMY"
            ],
            "correta": 2
        },
        {
            "pergunta": "Qual é o nome do fandom de Lady Gaga?",
            "alternativas": [
                "Selenators",
                "Little Monsters",
                "Lovatics"
            ],
            "correta": 1
        },
        {
            "pergunta": "Como são conhecidos os fãs de Beyoncé?",
            "alternativas": [
                "BeyHive",
                "Lambs",
                "Barbz"
            ],
            "correta": 0
        }
    ]
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
