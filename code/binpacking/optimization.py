from pulp import LpMaximize, LpProblem, LpVariable, value
from math import floor

def trier(a, b, c):
    if b < c:
        b, c = c, b
    if a < b:
        a, b = b, a
    if b < c:
        b, c = c, b
    return a, b, c

def Maximiser(L, l, h):
    if L < l:
        L, l = l, L
    if L < h:
        L, h = h, L
    return L, l, h

def Probleme(L, l, a, b):
    if l > L:
        l, L = L, l
    if a < b:
        a, b = b, a
    
    prob = LpProblem("Optimisation de chargement", LpMaximize)
    m = LpVariable("m", lowBound=0, cat='Integer')
    n = LpVariable("n", lowBound=0, cat='Integer')

    # On maximise le nombre de blocs placés
    prob += m + n, "Objectif"
    prob += a*m + b*n <= L, "Contrainte_L"
    prob += m <= floor(l / a), "Contrainte_l_m"
    prob += n <= floor(l / b), "Contrainte_l_n"

    prob.solve()
    return prob

def Nomb_Max1(L, l, h, a, b, c):
    L, l, h = Maximiser(L, l, h)
    a, b, c = trier(a, b, c)
    
    prob = Probleme(L, l, a, b)
    prob.solve()
    
    m = value(prob.variables()[0])
    n = value(prob.variables()[1])
    
    A1 = m * floor((l - b * floor(l / b)) / c)
    A2 = floor((L - m * a - n * b) / c) * floor((l - a * floor(l / a)) / b)

    return floor(h / a) * (m + n) + (A1 + A2) * floor(h / b) + floor(h / c) * (m + n)

print(Nomb_Max1(100, 90, 60, 13, 12, 41))

