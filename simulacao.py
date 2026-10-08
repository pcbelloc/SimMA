import sys
import math
import yaml
from formulas import LCG


class m4:
    def __init__(self, gerador, modelo, max_rnd=100000, numeros=None):
        self.gerador = gerador
        self.filas = modelo['queues']
        # Os mesmos parâmetros de antes, agora separados pelo nome da fila.
        self.servidores = {nome: fila['servers'] for nome, fila in self.filas.items()}
        self.capacidade = {nome: fila.get('capacity', -1) for nome, fila in self.filas.items()}
        self.cheg_min = {nome: fila.get('minArrival') for nome, fila in self.filas.items()}
        self.cheg_max = {nome: fila.get('maxArrival') for nome, fila in self.filas.items()}
        self.atend_min = {nome: fila['minService'] for nome, fila in self.filas.items()}
        self.atend_max = {nome: fila['maxService'] for nome, fila in self.filas.items()}
        self.numeros = numeros
        self.max_rnd = len(numeros) if numeros is not None else max_rnd
        self.tempo_global = 0.0
        self.estado = {nome: 0 for nome in self.filas}
        self.perdas = {nome: 0 for nome in self.filas}
        self.rnd_consumidos = 0
        self.tempos_acumulados = {}
        self.eventos = []
        self.chegadas = modelo.get('arrivals', {})
        self.rede = {nome: [] for nome in self.filas}
        for nome in self.filas:
            capacidade = self.capacidade[nome]
            self.tempos_acumulados[nome] = {i: 0.0 for i in range(max(0, capacidade) + 1)}
        for ligacao in modelo.get('network', []):
            if ligacao['probability'] > 0:
                self.rede[ligacao['source']].append((ligacao['target'], ligacao['probability']))
        for destinos in self.rede.values():
            destinos.sort(key=lambda x: x[1])  # Mesma ordem usada no módulo 3.

    def gerar_tempo(self, min_val, max_val):
        if self.rnd_consumidos >= self.max_rnd:
            raise ValueError('O limite de aleatórios já foi atingido.')
        aleatorio = self.gerador.random() if self.numeros is None else self.numeros[self.rnd_consumidos]
        self.rnd_consumidos += 1
        return min_val + (max_val - min_val) * aleatorio

    def agendar_evento(self, tempo, tipo, fila, destino=None):
        self.eventos.append((tempo, tipo, fila, destino))
        self.eventos.sort(key=lambda x: x[0])

    def iniciar_atendimento(self, fila):
        # O destino fica guardado na saída, como no simulador do módulo 3.
        destino = None
        destinos = self.rede[fila]
        if len(destinos) == 1 and destinos[0][1] == 1:
            destino = destinos[0][0]
        elif destinos:
            aleatorio = self.gerar_tempo(0, 1)
            for nome, probabilidade in destinos:
                if aleatorio <= probabilidade:
                    destino = nome
                    break
                aleatorio -= probabilidade
            if self.rnd_consumidos == self.max_rnd:
                return False
        tempo_saida = self.tempo_global + self.gerar_tempo(self.atend_min[fila], self.atend_max[fila])
        self.agendar_evento(tempo_saida, 'SAIDA', fila, destino)
        return self.rnd_consumidos < self.max_rnd

    def receber_cliente(self, fila):
        # Usado tanto na chegada externa quanto na transferência entre filas.
        if self.capacidade[fila] == -1 or self.estado[fila] < self.capacidade[fila]:
            self.estado[fila] += 1
            self.tempos_acumulados[fila].setdefault(self.estado[fila], 0.0)
            if self.estado[fila] <= self.servidores[fila]:
                return self.iniciar_atendimento(fila)
        else:
            self.perdas[fila] += 1
        return True

    def executar(self):
        for fila, tempo in self.chegadas.items():
            self.agendar_evento(tempo, 'CHEGADA', fila)

        while self.rnd_consumidos < self.max_rnd:
            if not self.eventos:
                break

            tempo_evento, tipo_evento, fila, destino = self.eventos.pop(0)
            delta_t = tempo_evento - self.tempo_global
            for nome in self.filas:
                self.tempos_acumulados[nome][self.estado[nome]] += delta_t
            self.tempo_global = tempo_evento

            if tipo_evento == 'CHEGADA':
                # Serviço antes da próxima chegada: ordem validada com o módulo 3.
                if not self.receber_cliente(fila):
                    break
                tempo_nova_chegada = self.tempo_global + self.gerar_tempo(self.cheg_min[fila], self.cheg_max[fila])
                self.agendar_evento(tempo_nova_chegada, 'CHEGADA', fila)

            elif tipo_evento == 'SAIDA':
                self.estado[fila] -= 1
                if self.estado[fila] >= self.servidores[fila]:
                    if not self.iniciar_atendimento(fila):
                        break
                if destino is not None:
                    if not self.receber_cliente(destino):
                        break

        self.imprimir_relatorio()

    def imprimir_relatorio(self):
        print(f'Tempo Global: {self.tempo_global:.5f}')
        print(f'Total de Aleatórios Consumidos: {self.rnd_consumidos}')
        for fila in self.filas:
            capacidade = self.capacidade[fila] if self.capacidade[fila] != -1 else 'infinita'
            print(f'\n=== {fila} | G/G/{self.servidores[fila]}/{capacidade} ===')
            print(f'Clientes Perdidos: {self.perdas[fila]}')
            for est, tempo in sorted(self.tempos_acumulados[fila].items()):
                probabilidade = (tempo / self.tempo_global) * 100 if self.tempo_global > 0 else 0
                print(f'Estado {est} | Tempo: {tempo:13.5f} | Probabilidade: {probabilidade:10.6f}%')
        print('\n')


def carregar_modelo(arquivo):
    # Aceita a marca !PARAMETERS do YAML fornecido pelo professor.
    yaml.SafeLoader.add_constructor('!PARAMETERS', yaml.SafeLoader.construct_mapping)
    with open(arquivo, encoding='utf-8-sig') as entrada:
        modelo = yaml.safe_load(entrada)
    if not isinstance(modelo, dict) or not isinstance(modelo.get('queues'), dict) or not modelo['queues']:
        raise ValueError('O YAML deve informar as filas em queues.')
    for nome, fila in modelo['queues'].items():
        servidores = fila['servers']
        capacidade = fila.get('capacity', -1)
        if type(servidores) is not int or servidores < 1:
            raise ValueError(f'{nome}: servers deve ser inteiro positivo.')
        if type(capacidade) is not int or (capacidade != -1 and capacidade < servidores):
            raise ValueError(f'{nome}: capacity deve ser -1 ou inteiro >= servers.')
        intervalos = ['Service']
        if nome in modelo.get('arrivals', {}):
            intervalos.append('Arrival')
        for intervalo in intervalos:
            minimo, maximo = fila['min' + intervalo], fila['max' + intervalo]
            if not math.isfinite(minimo) or not math.isfinite(maximo) or not 0 < minimo <= maximo:
                raise ValueError(f'{nome}: intervalo {intervalo} inválido.')
    for nome, tempo in modelo.get('arrivals', {}).items():
        if nome not in modelo['queues'] or not math.isfinite(tempo) or tempo < 0:
            raise ValueError('Fila ou instante inválido em arrivals.')
    somas = {nome: 0.0 for nome in modelo['queues']}
    for ligacao in modelo.get('network', []):
        origem, destino, probabilidade = ligacao['source'], ligacao['target'], ligacao['probability']
        if origem not in somas or destino not in somas or not 0 <= probabilidade <= 1:
            raise ValueError('Ligação ou probabilidade inválida em network.')
        somas[origem] += probabilidade
    if any(soma > 1 + 1e-12 for soma in somas.values()):
        raise ValueError('As probabilidades de uma origem não podem somar mais que 1.')
    sementes = modelo.get('seeds', [])
    limite = modelo.get('rndnumbersPerSeed', 100000)
    if not isinstance(sementes, list) or any(type(s) is not int for s in sementes):
        raise ValueError('seeds deve ser uma lista de inteiros.')
    if type(limite) is not int or limite < 1:
        raise ValueError('rndnumbersPerSeed deve ser inteiro positivo.')
    if not sementes:
        numeros = modelo.get('rndnumbers', [])
        if not isinstance(numeros, list) or not numeros or any(not 0 <= n < 1 for n in numeros):
            raise ValueError('Informe seeds ou uma lista rndnumbers com valores em [0, 1).')
    return modelo


if __name__ == '__main__':
    try:
        arquivo = sys.argv[1] if len(sys.argv) > 1 else 'modelos/entrega.yml'
        modelo = carregar_modelo(arquivo)
        sementes = modelo.get('seeds', [])
        for semente in sementes or [None]:
            meu_gerador = LCG(semente) if semente is not None else LCG()
            numeros = modelo.get('rndnumbers') if semente is None else None
            sim = m4(meu_gerador, modelo, modelo.get('rndnumbersPerSeed', 100000), numeros)
            print(f'Semente: {semente}' if semente is not None else 'Lista de aleatórios fornecida no YAML')
            sim.executar()
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as erro:
        sys.exit(f'Erro no modelo: {erro}')
