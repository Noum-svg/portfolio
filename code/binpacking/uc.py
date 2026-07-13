import numpy as np 
from math import floor,ceil
from itertools import product
def Sorte(a, b, c):
    if b < c:
        b, c = c, b
    if a < b:
        a, b = b, a
Carre = lambda Ensemble:product(Ensemble, Ensemble)
Cube = lambda Ensemble:product(Ensemble, Ensemble,Ensemble)
Matrice = lambda p: 1/2*np.dot(np.dot(np.array([[1,1],[1,-1]]),np.diag([1,1-2*(p%2)])),np.array([[1,1],[1,-1]]))
 
class UC:
  def __init__(self,a = 1,S = 1,V = 1):
    self.Longest_Side = a
    self.Area_Longest_base = S
    self.Volume = V
  def Orient(self,n=1,p=0,q=0,r=0):
    a,b,c = int(ceil(n*self.Longest_Side)),int(ceil(n*self.Area_Longest_base/self.Longest_Side)),int(ceil(n*self.Volume/self.Area_Longest_base))
    Sorte(a, b, c)
    List = [p,q,r]
    v = np.array([a,b,c])
    for k in range(3):
      P = np.eye(3)
      for i,j in Carre(range(2)):
         P[k%2 + i*(1+k//2),k%2 + j*(1+k//2)] = Matrice(List[k])[i,j]
      v = np.dot(P,v)
    return tuple(v)
  def Orient_Possible(self,n=1):
      return list({self.Orient(n,p,q,r) for p,q,r in Cube(range(2))})
UniteCharge = UC(60,3000,90000)
print(UniteCharge.Orient_Possible())



