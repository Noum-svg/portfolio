#Les bibliothéque
import numpy as np
from math import floor,ceil,inf
from itertools import product
from random import randint,randrange
#La Fonction de prolongement d'une matrice
H = lambda M,h:lambda i,j:M[i,j] if 0 <= i < M.shape[0] and 0<= j < M.shape[1] else h
#Le carée cartesienne une ensemble
Carre = lambda Ensemble:product(Ensemble, Ensemble)
#Le cube cartesienne une ensemble
Cube = lambda Ensemble:product(Ensemble, Ensemble,Ensemble)
#La puissance de la matrice J = [[0,1],[1,0]] par p
Matrice = lambda p: 1/2*np.dot(np.dot(np.array([[1,1],[1,-1]]),np.diag([1,1-2*(p%2)])),np.array([[1,1],[1,-1]]))
#Triée (a,b,c)
def Sorte(a, b, c):
    if b < c:
        b, c = c, b
    if a < b:
        a, b = b, a
#Fonction qui donne La top view d'une matrice orienté a,b,c
BoxTV = lambda a,b,c:c*np.ones((b,a))
#Fonction qui donne les coin d une Top view
Coin = lambda H,h,i,j:H(i,j) < max([min(H(i+p,j),H(i,j+q)) for p,q in Carre([-1,1])])
#Verification est ce que une posstion est possible
def PP(M,h,a,b,c,i,j):
    l,L = M.shape
    ESP = True
    for p in range(i,i+b):
        for q in range(j,j+a):
            ESP = (ESP and (H(M,h)(p,q)==H(M,h)(i,j)))
    return ESP and (M[i,j] + c <= h)
#L'ensemble des possitions possibles
def EPP(M,h,a,b,c,E_Coin):
  l,L = M.shape
  Liste = []
  for i,j in E_Coin:
    for p,q in Carre([-1,1]):
      if H(M,h)(i,j) < min(H(M,h)(i+p,j),H(M,h)(i,j+q)) and PP(M,h,a,b,c,i-((p+1)//2)*(b-1),j-((q+1)//2)*(a-1)):
        Liste.append((i-((p+1)//2)*(b-1),j-((q+1)//2)*(a-1)))
  return Liste
class UC:
  def __init__(self,id,a = 1,S = 1,V = 1):
    self.id = id
    self.Longest_Side = a
    self.Area_Longest_base = S
    self.Volume = V
  #La fonction qui me donne une orientation
  def Orient(self,n=1,u=0):
    a,b,c = int(ceil(n*self.Longest_Side)),int(ceil(n*self.Area_Longest_base/self.Longest_Side)),int(ceil(n*self.Volume/self.Area_Longest_base))
    Sorte(a, b, c)
    List = [(u//2)//2,(u//2)%2,u%2]
    v = np.array([a,b,c])
    for k in range(3):
      P = np.eye(3)
      for i,j in Carre(range(2)):
         P[k%2 + i*(1+k//2),k%2 + j*(1+k//2)] = Matrice(List[k])[i,j]
      v = np.dot(P,v)
    return tuple(int(x) for x in v)
  #La fonction qui donne l'ensemble des orentation possible
  def Orient_Possible(self,n=1):
      return [self.Orient(n,k) for k in range(6)]
def Conf_Aleatoire(L,l,h,UCs,n=1,S = np.ones(6),N = 1,gamma = 0.75,eps = 0.001):
  #Descritisé les dimensions du conteneur
  L,l,h = int(floor(n*L)),int(floor(n*l)),int(floor(n*h))
  TV = np.zeros((l,L))
  #Le conteneur vide initialement
  Conf = {}
  E_Coin = {(i*(l-1),j*(L-1)) for i,j in Carre(range(2))}
  Hmin,Hmax = inf,-inf
  T = len(UCs)
  while True:
    UCP = []
    EppTotal = 0
    for uc,k in product(UCs,range(6)):
      a,b,c = uc.Orient(n,k)
      Epp = EPP(TV,h,a,b,c,E_Coin)
      if len(Epp)>0:
        UCP.append((uc,k,Epp))
        EppTotal += len(Epp)
    if EppTotal == 0:
      break
    vs = np.zeros(len(UCP))
    PPrb = [[]]*len(UCP)
    Cont = 0
    Abs = 0
    UCPP = []
    Vmin = inf
    for m in range(N+2):
      if (Abs <= eps):
        Cont += 1
      if (Cont == 2):
        break
      Abs = 0
      for p1 in range(len(UCP)):
        uc = UCP[p1][0]
        a,b,c = uc.Orient(n,UCP[p1][1])
        Epp = UCP[p1][2]
        V = inf
        for i,j in Epp:
          Liste = []
          for p,q in Carre(range(2)):
            X = [i+p*(b-1),j+q*(a-1)]
            if(X[(p+q)%2]!=q*((1-p)*(L-1)+p*(l-1))):
              r = (a+b+(a-b)*(2*p-1)*(2*q-1))//2
              s = (p+q-2*p*q)*(a+1)-1
              w1 = np.array([b-1,a-1])
              w3 = np.array([q,1-q])
              dx = (2*p-1)*np.dot(Matrice(p),w3)
              du,dv = int(dx[0]),int(dx[1])
              for k in range(r):
                w2 = np.array([s,k])
                x = p*w1+(1-2*p)*np.dot(Matrice(p+q),w2)
                u,v = int(x[0]),int(x[1])
                if u*v == 0 or H(TV,h)(i+u+du,j+v+dv) != TV[i+u,j+v]:
                  Liste.append(TV[i+u,j+v])
          Num = len(Liste)
          MoyenDiff = (1/Num)*sum(abs(Haut - TV[i,j]) for Haut in Liste)
          VarHaut = (max(Hmax,c)-min(Hmin,c))/h
          Vol = -uc.Volume/(T*L*l*h)
          ParaVect = np.array([Num,MoyenDiff,VarHaut,Vol,j,TV[i,j]])
          Sc = np.dot(S,ParaVect)
          if EppTotal > len(Epp):
            for p2 in range(len(UCP)):
              if p2 != p1 :
                Sc += gamma*(len(UCP[p2][2])/(EppTotal-len(Epp)))*vs[p2]
          if Sc <= V:
            if Sc < V:
              if m == N+1 or Cont == 1:
                PPrb[p1]=[(i,j)]
              V = Sc
            elif m == N+1 or Cont == 1:
              PPrb[p1].append((i,j))
        if m <= N:
          Abs = max(Abs,abs(vs[p1]-V))
          vs[p1]=V
        if m == N+1 and Cont == 1:
          if Vmin >= vs[p1]:
            if Vmin > vs[p1]:
              UCPP = [p1]
              Vmin = vs[p1]
            else:
              UCPP.append(p1)
    p1 = randrange(len(UCPP))
    uc = UCP[UCPP[p1]][0]
    a,b,c = uc.Orient(n,UCP[UCPP[p1]][1])
    Epp = PPrb[UCPP[p1]]
    p2 = randrange(len(Epp))
    i,j = Epp[p2]
    Conf[uc] = (k,i/n,j/n,TV[i,j]/n)
    TV[i:i+b,j:j+a] += BoxTV(a,b,c)
    for p,q in Carre(range(2)):
      if Coin(H(TV,h),h,i+p*(b-1),j+q*(a-1)):
        E_Coin.add((i+p*(b-1),j+q*(a-1)))
      X = [i+p*(b-1),j+q*(a-1)]
      if (X[(p+q)%2]!=q*((1-p)*(L-1)+p*(l-1))):
        r = (a+b+(a-b)*(2*p-1)*(2*q-1))//2
        s = (p+q-2*p*q)*(a+1)-1
        for k in range(r):
          w1 = np.array([b-1,a-1])
          w2 = np.array([s,k])
          x = p*w1+(1-2*p)*np.dot(Matrice(p+q),w2)
          u,v = int(x[0]),int(x[1])
          if Coin(H(TV,h),h,i+u,j+v):
            E_Coin.add((i+u,j+v))
    UCs.remove(uc)
  return Conf
#Le nombre entré
def Nombre(Conf):
  return len(Conf)
#Le volume entrée
def Volume(Conf):
  return sum(uc.Volume for uc in Conf.keys())
L,l,h = 20,6,5
UCs = [UC(i,5,15,30) for i in range(70)]
S = np.array([20,10,9,8,5,2])
Conf = Conf_Aleatoire(L, l, h, UCs,1,S,5)
print(Nombre(Conf))
print(Volume(Conf))