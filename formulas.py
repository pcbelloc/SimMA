class LCG:
    def __init__(self, semente=42, a=1664525, c=1013904223, m=2**32):
        self.x = semente
        self.a = a
        self.c = c
        self.m = m

    def random(self):
        self.x = (self.a * self.x + self.c) % self.m
        return self.x / self.m


# Foi usado os mesmo numero da ultima atividade de numero pseurandom!!! to reutilizando. (fazendo "mini" biblioteca pros calc)