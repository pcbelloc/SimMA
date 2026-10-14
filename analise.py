"""Calcula os índices do M9 usando os estados do simulador original."""
import sys
from formulas import LCG
from simulacao import m4, carregar_modelo


def simular(arquivo, semente=None, imprimir=True):
    modelo = carregar_modelo(arquivo)
    semente = modelo['seeds'][0] if semente is None else semente
    sim = m4(LCG(semente), modelo, modelo['rndnumbersPerSeed'])
    if not imprimir:
        sim.imprimir_relatorio = lambda: None
    if imprimir:
        print(f'Semente: {semente}')
    sim.executar()
    filas = {}
    for nome, fila in modelo['queues'].items():
        tempos = sim.tempos_acumulados[nome]
        probabilidades = {i: t / sim.tempo_global for i, t in tempos.items()}
        servidores = fila['servers']
        media_servico = (fila['minService'] + fila['maxService']) / 2
        mu = 60 / media_servico  # atendimentos/hora por servidor
        n = sum(i * p for i, p in probabilidades.items())
        ocupados = sum(min(i, servidores) * p for i, p in probabilidades.items())
        d = ocupados * mu  # estimativa pela fórmula do M9
        u = ocupados / servidores
        w = 60 * n / d if d else 0  # minutos por visita à fila
        filas[nome] = dict(tempos=tempos, probabilidades=probabilidades,
                           servidores=servidores, capacidade=fila['capacity'],
                           media_servico=media_servico, mu=mu,
                           N=n, D=d, U=u, W=w,
                           perdas=sim.perdas[nome],
                           perdas_h=60 * sim.perdas[nome] / sim.tempo_global)
        if imprimir:
            print(f'{nome}: N={n:.6f} equipamentos; D={d:.6f} atendimentos/h; '
                  f'U={100*u:.6f}%; W={w:.6f} min/visita; '
                  f'perdas/h={filas[nome]["perdas_h"]:.6f}')
    return dict(semente=semente, tempo=sim.tempo_global,
                aleatorios=sim.rnd_consumidos, filas=filas)


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        sys.exit('Uso: python analise.py modelos/inicial.yml [semente]')
    simular(sys.argv[1], int(sys.argv[2]) if len(sys.argv) == 3 else None)
