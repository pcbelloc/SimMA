from formulas import LCG


class Fila:
    def __init__(self, servidores, capacidade):
        self.servidores = servidores
        self.capacidade = capacidade
        self.estado = 0
        self.perdas = 0
        self.tempos_acumulados = {i: 0.0 for i in range(capacidade + 1)}

    def Status(self):
        return self.estado

    def Capacity(self):
        return self.capacidade

    def Servers(self):
        return self.servidores

    def In(self):
        self.estado += 1

    def Out(self):
        self.estado -= 1

    def Loss(self):
        self.perdas += 1


class TandemSim:
    def __init__(self, gerador,
                 servidores1, capacidade1, atend1_min, atend1_max,
                 servidores2, capacidade2, atend2_min, atend2_max,
                 cheg_min, cheg_max, max_rnd=100000):
        self.gerador = gerador
        self.fila1 = Fila(servidores1, capacidade1)
        self.fila2 = Fila(servidores2, capacidade2)

        self.cheg_min, self.cheg_max = cheg_min, cheg_max
        self.atend1_min, self.atend1_max = atend1_min, atend1_max
        self.atend2_min, self.atend2_max = atend2_min, atend2_max

        self.max_rnd = max_rnd
        self.rnd_consumidos = 0
        self.tempo_global = 0.0
        self.eventos = []

    def gerar_tempo(self, min_val, max_val):
        self.rnd_consumidos += 1
        aleatorio = self.gerador.random()
        return min_val + (max_val - min_val) * aleatorio

    def agendar_evento(self, tempo, tipo):
        self.eventos.append((tempo, tipo))
        self.eventos.sort(key=lambda x: x[0])

    def acumula_tempo(self, delta_t):
        self.fila1.tempos_acumulados[self.fila1.estado] += delta_t
        self.fila2.tempos_acumulados[self.fila2.estado] += delta_t

    def executar(self):
        self.agendar_evento(3.0, 'CHEGADA')

        while self.rnd_consumidos < self.max_rnd:
            if not self.eventos:
                break

            tempo_evento, tipo_evento = self.eventos.pop(0)
            delta_t = tempo_evento - self.tempo_global
            self.acumula_tempo(delta_t)
            self.tempo_global = tempo_evento

            if tipo_evento == 'CHEGADA':
                self.processa_chegada()
            elif tipo_evento == 'SAIDA':
                self.processa_saida()
            elif tipo_evento == 'PASSAGEM':
                self.processa_passagem()

        self.imprimir_relatorio()

    def processa_chegada(self):
        if self.fila1.Status() < self.fila1.Capacity():
            self.fila1.In()
            if self.fila1.Status() <= self.fila1.Servers():
                if self.rnd_consumidos < self.max_rnd:
                    t = self.tempo_global + self.gerar_tempo(self.atend1_min, self.atend1_max)
                    self.agendar_evento(t, 'PASSAGEM')
        else:
            self.fila1.Loss()

        if self.rnd_consumidos < self.max_rnd:
            t = self.tempo_global + self.gerar_tempo(self.cheg_min, self.cheg_max)
            self.agendar_evento(t, 'CHEGADA')

    def processa_saida(self):
        self.fila2.Out()
        if self.fila2.Status() >= self.fila2.Servers():
            if self.rnd_consumidos < self.max_rnd:
                t = self.tempo_global + self.gerar_tempo(self.atend2_min, self.atend2_max)
                self.agendar_evento(t, 'SAIDA')

    def processa_passagem(self):
        self.fila1.Out()
        if self.fila1.Status() >= self.fila1.Servers():
            if self.rnd_consumidos < self.max_rnd:
                t = self.tempo_global + self.gerar_tempo(self.atend1_min, self.atend1_max)
                self.agendar_evento(t, 'PASSAGEM')

        if self.fila2.Status() < self.fila2.Capacity():
            self.fila2.In()
            if self.fila2.Status() <= self.fila2.Servers():
                if self.rnd_consumidos < self.max_rnd:
                    t = self.tempo_global + self.gerar_tempo(self.atend2_min, self.atend2_max)
                    self.agendar_evento(t, 'SAIDA')
        else:
            self.fila2.Loss()

    def imprimir_relatorio(self):
        for nome, fila in [("Fila1", self.fila1), ("Fila2", self.fila2)]:
            print(f"=== {nome}: G/G/{fila.servidores}/{fila.capacidade} ===")
            print(f"Clientes Perdidos: {fila.perdas}")
            for est, tempo in fila.tempos_acumulados.items():
                prob = (tempo / self.tempo_global) * 100 if self.tempo_global > 0 else 0
                print(f"Estado {est} | Tempo: {tempo:13.5f} | Probabilidade: {prob:6.2f}%")
            print()
        print(f"Tempo Global: {self.tempo_global:.5f}")
        print(f"Total de Aleatórios Consumidos: {self.rnd_consumidos}")


if __name__ == "__main__":
    gerador = LCG(semente=42)
    sim = TandemSim(
        gerador,
        servidores1=2, capacidade1=4, atend1_min=5, atend1_max=6,   # Fila1: G/G/2/4
        servidores2=3, capacidade2=5, atend2_min=2, atend2_max=4,   # Fila2: G/G/3/5
        cheg_min=1, cheg_max=3
    )
    sim.executar()