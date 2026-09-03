from formulas import LCG

class m4:
    def __init__(self, gerador, servidores, capacidade, cheg_min, cheg_max, atend_min, atend_max, max_rnd=100000):
        self.gerador = gerador
        self.servidores = servidores
        self.capacidade = capacidade
        self.cheg_min = cheg_min
        self.cheg_max = cheg_max
        self.atend_min = atend_min
        self.atend_max = atend_max
        self.max_rnd = max_rnd
        self.tempo_global = 0.0 
        self.estado = 0
        self.perdas = 0
        self.rnd_consumidos = 0
        self.tempos_acumulados = {i: 0.0 for i in range(capacidade + 1)}
        self.eventos = [] 

    def gerar_tempo(self, min_val, max_val):
        self.rnd_consumidos += 1
        aleatorio = self.gerador.random() 
        return min_val + (max_val - min_val) * aleatorio

    def agendar_evento(self, tempo, tipo):
        self.eventos.append((tempo, tipo))
        self.eventos.sort(key=lambda x: x[0]) 

    def executar(self):
        self.agendar_evento(3.0, 'CHEGADA')

        while self.rnd_consumidos < self.max_rnd:
            if not self.eventos:
                break

            tempo_evento, tipo_evento = self.eventos.pop(0)
            delta_t = tempo_evento - self.tempo_global
            self.tempos_acumulados[self.estado] += delta_t
            self.tempo_global = tempo_evento

            if tipo_evento == 'CHEGADA':
                if self.rnd_consumidos < self.max_rnd:
                    tempo_nova_chegada = self.tempo_global + self.gerar_tempo(self.cheg_min, self.cheg_max)
                    self.agendar_evento(tempo_nova_chegada, 'CHEGADA')

                if self.estado < self.capacidade:
                    self.estado += 1
                    if self.estado <= self.servidores:
                        if self.rnd_consumidos < self.max_rnd:
                            tempo_saida = self.tempo_global + self.gerar_tempo(self.atend_min, self.atend_max)
                            self.agendar_evento(tempo_saida, 'SAIDA')
                else:
                    self.perdas += 1

            elif tipo_evento == 'SAIDA':
                self.estado -= 1
                if self.estado >= self.servidores:
                    if self.rnd_consumidos < self.max_rnd:
                        tempo_saida = self.tempo_global + self.gerar_tempo(self.atend_min, self.atend_max)
                        self.agendar_evento(tempo_saida, 'SAIDA')

        self.imprimir_relatorio()

    def imprimir_relatorio(self):
        print(f"=== G/G/{self.servidores}/{self.capacidade} ===")
        print(f"Tempo Global: {self.tempo_global:.5f}") #.5f pra precisão (pesquisei e estava q o melhor é 4-6 pra precisão, deopis disso muda pouco d+ o vlr)
        print(f"Clientes Perdidos: {self.perdas}")
        print(f"Total de Aleatórios Consumidos: {self.rnd_consumidos}")
        for est, tempo in self.tempos_acumulados.items():
            probabilidade = (tempo / self.tempo_global) * 100 if self.tempo_global > 0 else 0
            print(f"Estado {est} | Tempo: {tempo:13.5f} | Probabilidade: {probabilidade:6.2f}%")
        print("\n")

if __name__ == "__main__":
    meu_gerador_1 = LCG()
    sim_1 = m4(meu_gerador_1, servidores=1, capacidade=5, cheg_min=2, cheg_max=5, atend_min=3, atend_max=5)
    sim_1.executar()

    meu_gerador_2 = LCG()
    sim_2 = m4(meu_gerador_2, servidores=2, capacidade=5, cheg_min=2, cheg_max=5, atend_min=3, atend_max=5)
    sim_2.executar()