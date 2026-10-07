# Simulador de Rede de Filas

M8 - Simulação e Métodos Analíticos, turma 691

Alunos:

```
Alice Martofel Guzas
Bryan Leandro Almerindo Brasil
Júnior Fernando Stahl
Luiza Ilha Rosito
```

## Requisitos

Python 3. Não há dependências externas.

## Como rodar

No terminal, dentro da pasta do projeto:

```
python3 main.py
```

(ou `python main.py`, dependendo da instalação)

O programa simula o modelo definido no próprio `main.py` e imprime, para cada fila:

* o tempo acumulado e a probabilidade de cada estado (número de clientes na fila);
* o número de clientes perdidos;

e, ao final, o tempo global da simulação.

## Como simular outro modelo

O modelo fica no dicionário `REDE_TANDEM`, no final do `main.py`. Cada chave é o nome de uma fila e o valor é a sua configuração:

| Campo | Obrigatório | Descrição |
|---|---|---|
| `num_servidores` | sim | Número de servidores da fila |
| `capacidade` | sim | Capacidade máxima (clientes em atendimento + esperando). Para fila "infinita", use um valor grande, como `100000` |
| `atendimento_min`, `atendimento_max` | sim | Intervalo do tempo de atendimento (distribuição uniforme) |
| `chegada_min`, `chegada_max` | não | Intervalo entre chegadas externas. Omita se a fila não recebe clientes de fora da rede |
| `primeira_chegada` | não | Instante da primeira chegada externa (não consome aleatório) |
| `roteamento` | sim | Dicionário `{"fila_destino": probabilidade}`. A probabilidade que faltar para somar 1 significa sair da rede. `{}` = sempre sai da rede |

Exemplo de uma rede com duas filas, onde 40% dos clientes da `fila1` seguem para a `fila2` e o restante sai:

```python
REDE_TANDEM = {
    "fila1": {
        "num_servidores": 1,
        "capacidade": 5,
        "chegada_min": 1, "chegada_max": 3,
        "atendimento_min": 2, "atendimento_max": 4,
        "primeira_chegada": 1.0,
        "roteamento": {"fila2": 0.4},
    },
    "fila2": {
        "num_servidores": 2,
        "capacidade": 8,
        "atendimento_min": 3, "atendimento_max": 6,
        "roteamento": {},
    },
}
```

Antes de simular, o programa valida o modelo: a soma das probabilidades de cada fila não pode passar de 1 e todo destino precisa existir.

## Parâmetros da simulação

Na chamada `simular(...)` (final do `main.py`) é possível ajustar:

* `quantidade_aleatorios`: quantos números pseudoaleatórios usar (padrão `100000`). A simulação termina ao consumir o último;
* `seed`, `gerador_a`, `gerador_c`, `gerador_m`: parâmetros do gerador congruente linear `X = (a*X + c) mod M` (padrão: semente 12345, a = 16807, c = 0, M = 2^31 - 1).

## Convenções adotadas

* As filas começam vazias.
* O destino de um cliente é sorteado quando ele **entra** em atendimento, antes do sorteio do tempo de atendimento (mesma convenção do simulador do módulo 3).
* Quando há um único destino com probabilidade 1, a escolha é determinística e não consome aleatório.
* Em caso de empate entre eventos no mesmo instante, a chegada é processada antes da saída.
* Cliente que chega a uma fila cheia (vindo de fora ou de outra fila) é contabilizado como perdido.

## Modelo da entrega

O modelo já configurado no `main.py` é o do enunciado:

* Fila 1: G/G/1, chegadas entre 2..4, atendimento entre 1..2, primeiro cliente no tempo 2,0; vai para a Fila 2 (0,2) ou Fila 3 (0,8).
* Fila 2: G/G/2/5, atendimento entre 4..6; vai para a Fila 1 (0,3), Fila 3 (0,5) ou sai (0,2).
* Fila 3: G/G/2/10, atendimento entre 5..15; vai para a Fila 2 (0,7) ou sai (0,3).

Com 100.000 aleatórios, o tempo global da simulação é 50786,0429.
