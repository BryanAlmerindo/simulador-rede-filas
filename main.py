""" M6 - Simulador de rede de filas (topologia generica) """

""" Etapa 1 - Gerador de numeros pseudoaleatorios """
# (mesma logica do M4: metodo congruente linear, X = (a*X + c) mod M)

X = None
a = None
c = None
M = None
count = None


class FimDaSimulacao(Exception):
    pass


def NextRandom():
    global X
    global count

    if count == 0:
        raise FimDaSimulacao()

    # Metodo Congruente Linear
    X = (a * X + c) % M

    # Cada aleatorio solicitado consome uma unidade do contador
    count -= 1

    # Normalizacao intervalo 0, 1
    return X / M


def simular(config_filas, seed=12345, gerador_a=16807, gerador_c=0, gerador_m=2**31 - 1, quantidade_aleatorios=100000):
    """
    Roda a simulacao de uma rede de filas ate consumir `quantidade_aleatorios`
    numeros pseudoaleatorios (ou a rede esvaziar antes disso).

    config_filas: dict "fila_id" -> {
        "num_servidores": int,
        "capacidade": int,
        "atendimento_min": float, "atendimento_max": float,
        "chegada_min": float, "chegada_max": float,     # omitir se a fila nao
                                                          # recebe chegada externa
        "primeira_chegada": float,                       # opcional: fixa o
                                                          # instante do 1o cliente
                                                          # externo sem sortear
        "roteamento": {"outra_fila": probabilidade, ...},  # {} = sempre sai da rede
    }

    A probabilidade que "sobrar" no roteamento (1 - soma do dicionario)
    tambem significa "sai da rede". Quando so existe um destino com
    probabilidade 1.0 a escolha e deterministica e nao consome aleatorio.

    IMPORTANTE (mesma convencao do simulador de referencia do modulo 3): o
    destino de um cliente e sorteado no momento em que ele ENTRA em
    atendimento (nao quando termina). Isso importa porque muda a ordem dos
    aleatorios consumidos: destino primeiro, depois o tempo de atendimento.

    Retorna (filas, tempo_global). Cada filas[fila_id] tem "times" (tempo
    acumulado por estado, indice 0..capacidade) e "clientes_perdidos".
    """
    global X, a, c, M, count
    X = seed
    a = gerador_a
    c = gerador_c
    M = gerador_m
    count = quantidade_aleatorios

    """ Etapa 3 - Rede de filas """

    filas = {}
    for fila_id, cfg in config_filas.items():
        estado_fila = dict(cfg)
        estado_fila["fila"] = []  # timestamps dos clientes esperando
        estado_fila["servidores"] = [None] * cfg["num_servidores"]  # None = livre, senao (tempo_saida, destino)
        estado_fila["prox_chegada"] = (
            cfg.get("primeira_chegada", float('inf')) if "chegada_min" in cfg else float('inf')
        )
        estado_fila["clientes_perdidos"] = 0
        estado_fila["times"] = [0.0] * (cfg["capacidade"] + 1)
        filas[fila_id] = estado_fila

    tempo_atual = 0.0

    def clientes_no_sistema(fila_id):
        cfg = filas[fila_id]
        em_atendimento = sum(1 for s in cfg["servidores"] if s is not None)
        return len(cfg["fila"]) + em_atendimento

    def decide_destino(fila_id):
        """ Decide para qual fila um cliente vai ao terminar o atendimento
        nesta fila_id. Retorna None se o cliente sai da rede. So sorteia
        aleatorio quando a decisao nao e deterministica. """
        roteamento = filas[fila_id]["roteamento"]
        if not roteamento:
            return None

        if len(roteamento) == 1:
            (destino, prob), = roteamento.items()
            if prob >= 1.0:
                return destino

        r = NextRandom()
        acumulado = 0.0
        for destino, prob in roteamento.items():
            acumulado += prob
            if r < acumulado:
                return destino
        return None  # sobra de probabilidade = sai da rede

    def inicia_atendimento(fila_id, idx):
        """ Coloca um cliente pra ser atendido no servidor `idx` da fila_id:
        decide o destino dele (pro futuro) e sorteia o tempo de atendimento,
        NESSA ordem -- igual ao simulador de referencia. """
        cfg = filas[fila_id]
        destino = decide_destino(fila_id)
        tempo_atendimento = cfg["atendimento_min"] + (cfg["atendimento_max"] - cfg["atendimento_min"]) * NextRandom()
        cfg["servidores"][idx] = (tempo_atual + tempo_atendimento, destino)

    def tenta_entrar(fila_id):
        """ Tenta colocar um cliente (chegada externa ou vindo de outra fila
        da rede) na fila_id. Se ela ja estiver cheia, o cliente e perdido. """
        cfg = filas[fila_id]

        if clientes_no_sistema(fila_id) >= cfg["capacidade"]:
            cfg["clientes_perdidos"] += 1
            return

        livre = None
        for i in range(cfg["num_servidores"]):
            if cfg["servidores"][i] is None:
                livre = i
                break

        if livre is not None:
            inicia_atendimento(fila_id, livre)
        else:
            cfg["fila"].append(tempo_atual)

    def chegada(fila_id):
        tenta_entrar(fila_id)
        cfg = filas[fila_id]
        intervalo = cfg["chegada_min"] + (cfg["chegada_max"] - cfg["chegada_min"]) * NextRandom()
        cfg["prox_chegada"] = tempo_atual + intervalo

    def saida(fila_id, idx):
        cfg = filas[fila_id]

        # O destino desse cliente ja tinha sido decidido quando ele entrou
        # em atendimento (em inicia_atendimento) -- aqui so usamos.
        _, destino = cfg["servidores"][idx]

        # Ordem importa (e é a mesma do simulador de referencia): primeiro
        # coloca em atendimento quem estava esperando NESTA fila (se
        # houver), e só DEPOIS manda o cliente que saiu para o destino.
        if len(cfg["fila"]) > 0:
            cfg["fila"].pop(0)
            inicia_atendimento(fila_id, idx)
        else:
            cfg["servidores"][idx] = None

        if destino is not None:
            tenta_entrar(destino)

    """ Etapa 2 - Loop """
    try:
        while count > 0:
            # proximo evento entre TODAS as filas da rede; empate entre
            # chegada e saida no mesmo instante -> chegada primeiro.
            melhor = None
            for fila_id, cfg in filas.items():
                if "chegada_min" in cfg:
                    candidato = (cfg["prox_chegada"], 0, fila_id, "chegada", None)
                    if melhor is None or candidato < melhor:
                        melhor = candidato

                for i, s in enumerate(cfg["servidores"]):
                    if s is not None:
                        candidato = (s[0], 1, fila_id, "saida", i)
                        if melhor is None or candidato < melhor:
                            melhor = candidato

            proximo_tempo, _, proxima_fila, tipo_evento, idx_servidor = melhor

            for fila_id in filas:
                estado = clientes_no_sistema(fila_id)
                filas[fila_id]["times"][estado] += (proximo_tempo - tempo_atual)

            tempo_atual = proximo_tempo

            if tipo_evento == "chegada":
                chegada(proxima_fila)
            else:
                saida(proxima_fila, idx_servidor)
    except FimDaSimulacao:
        pass

    return filas, tempo_atual


""" Etapa 4 - Resultados """


def imprimir_resultados(filas, tempo_global):
    for fila_id, cfg in filas.items():
        print(f"\nResultado da {fila_id} (G/G/{cfg['num_servidores']}/{cfg['capacidade']})")
        print("Estado / Tempo acumulado / Probabilidade")
        for i, t in enumerate(cfg["times"]):
            if t > 0:  # so mostra estados que ocorreram
                print(f"{i}: {t} ({100 * t / tempo_global}%)")
        print("Clientes perdidos: " + str(cfg["clientes_perdidos"]))
    print("\nTempo global da simulacao: " + str(tempo_global))


# Rede trabalho

REDE_TANDEM = {
    "fila1": {                      # G/G/1
        "num_servidores": 1,
        "capacidade": 100000,
        "chegada_min": 2,       # chegadas entre 2..4
        "chegada_max": 4,
        "atendimento_min": 1,  # atendimento entre 1..2
        "atendimento_max": 2,
        "primeira_chegada": 2.0,
        "roteamento": {"fila2": 0.2, "fila3": 0.8},
    },
    "fila2": {                      # G/G/2/5
        "num_servidores": 2,
        "capacidade": 5,
        "atendimento_min": 4,
        "atendimento_max": 6,
        "roteamento": {"fila1": 0.3, "fila3": 0.5},
    },
    "fila3": {                      # G/G/2/10
        "num_servidores": 2,
        "capacidade": 10,
        "atendimento_min": 5,
        "atendimento_max": 15,
        "roteamento": {"fila2": 0.7},
    },
}

def validar_rede(config_filas):
    for fila_id, cfg in config_filas.items():
        rot = cfg.get("roteamento", {})
        if sum(rot.values()) > 1.0 + 1e-9:
            raise ValueError(f"{fila_id}: soma das probabilidades > 1")
        for destino in rot:
            if destino not in config_filas:
                raise ValueError(f"{fila_id}: destino inexistente '{destino}'")

if __name__ == "__main__":
    validar_rede(REDE_TANDEM)
    filas, tempo_global = simular(REDE_TANDEM, quantidade_aleatorios=100000)
    imprimir_resultados(filas, tempo_global)
