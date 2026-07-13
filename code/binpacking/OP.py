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
def Conf_Aleatoire(L,l,h,UCs,S = np.ones(4),n=1):
  #Descritisé les dimensions du conteneur
  L,l,h = int(floor(n*L)),int(floor(n*l)),int(floor(n*h))
  TV = np.zeros((l,L))
  #Le conteneur vide initialement
  Conf = {}
  E_Coin = {(i*(l-1),j*(L-1)) for i,j in Carre(range(2))}
  while True:
    UCP = []
    M = 0
    for uc,k in product(UCs,range(6)):
      a,b,c = uc.Orient(n,k)
      Epp = EPP(TV,h,a,b,c,E_Coin)
      Len = len(Epp)
      if Len >= max(1,M):
        if (Len > M):
          M = Len
          UCP = [(uc,k,Epp)]
        else :
          UCP.append((uc,k,Epp))
    if M == 0:
      break
    p1 = randrange(len(UCP))
    a,b,c = UCP[p1][0].Orient(n,UCP[p1][1])
    Epp = UCP[p1][2]
    Epp1 = []
    Score = inf
    for i,j in Epp:
      Liste = []
      for p,q in Carre(range(2)):
        X = [i+p*(b-1),j+q*(a-1)]
        if(X[(p+q)%2]!=q*((1-p)*(L-1)+p*(l-1))):
          r = (a+b+(a-b)*(2*p-1)*(2*q-1))//2
          s = (p+q-2*p*q)*(a+1)-1
          w3 = np.array([q,1-q])
          dx = (2*p-1)*np.dot(Matrice(p),w3)
          du,dv = int(dx[0]),int(dx[1])
          for k in range(r):
            w1 = np.array([b-1,a-1])
            w2 = np.array([s,k])
            x = p*w1+(1-2*p)*np.dot(Matrice(p+q),w2)
            u,v = int(x[0]),int(x[1])
            if u*v == 0 or H(TV,h)(i+u+du,j+v+dv) != TV[i+u,j+v]:
              Liste.append(TV[i+u,j+v])
      Num = len(Liste)
      MoyenDiff = (1/Num)*sum(abs(Haut - TV[i,j]) for Haut in Liste)
      ParaVect = np.array([Num,MoyenDiff,j,TV[i,j]])
      Sc = np.dot(S,ParaVect)
      if Sc <= Score:
        if Sc < Score:
          Score = Sc
          Epp1 = [(i,j)]
        else:
          Epp1.append((i,j))
    p2 = randrange(len(Epp1))
    i,j = Epp1[p2]
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
'''
while True:
  S = np.array([randrange(1000),randrange(1000),randrange(1000),randrange(1000)])
  Conf = Conf_Aleatoire(L, l, h, UCs,S)
  if (Nombre(Conf) >= 18):
    break
print(tuple(S))
print(Conf)
'''
Unite = UC(0,5,15,30)
a,b,c = Unite.Orient(1,2)
print(BoxTV(a,b,c))
















