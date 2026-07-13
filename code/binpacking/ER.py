import numpy as np
from itertools import product
BoxTV = lambda a,b,c:c*np.ones((b,a))
def PP(M,h,a,b,c,i,j):
    l,L = M.shape
    H = lambda x,y:M[x,y] if 0 <= x < l and 0<= y < L else h
    ESP = True
    for p in range(i,i+b):
        for q in range(j,j+a):
            ESP = (ESP and (H(p,q)==H(i,j)))
    return ESP and (M[i,j] + c <= h)
Carre = lambda Ensemble:product(Ensemble, Ensemble)
def MP(M,h):
  l,L = M.shape
  H = lambda i,j: M[i,j] if 0 <= i < l and 0 <= j < L else h
  return np.array([[1 if H(i,j) < max([min(H(i+p,j),H(i,j+q)) for p,q in Carre([-1,1])]) else 0 for j in range(L)] for i in range(l)])
Coin = lambda H,h,i,j:H(i,j) < max([min(H(i+p,j),H(i,j+q)) for p,q in Carre([-1,1])])
def LP(M,h):
  l,L = M.shape
  H = lambda x,y:M[x,y] if 0 <= x < l and 0<= y < L else h
  return [(i,j) for i,j in product(range(l),range(L)) if Coin(H,h,i,j)]
def EPP(M,h,a,b,c):
  l,L = M.shape
  H = lambda x,y:M[x,y] if 0 <= x < l and 0<= y < L else h
  Liste = []
  for i,j in LP(M,h):
    for p,q in Carre([-1,1]):
      if H(i,j) < min(H(i+p,j),H(i,j+q)) and PP(M,h,a,b,c,i-((p+1)//2)*(b-1),j-((q+1)//2)*(a-1)):
        Liste.append((i-((p+1)//2)*(b-1),j-((q+1)//2)*(a-1)))
  return Liste
M = np.array([[3,3,3,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,0,0,0,0,0,0],
              [3,3,3,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,0,0,0,0,0,0],
              [3,3,3,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0],
              [3,3,3,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0],
              [3,3,3,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0],
              [8,8,8,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0],
              [8,8,8,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0],
              [8,8,8,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0],
              [8,8,8,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0],
              [8,8,8,3,3,65,65,65,65,14,14,14,14,14,46,46,46,46,46,3,3,3,3,0,0]
              ])
A = np.random.randint(0, 100, size=(2000, 1000), dtype=int)
print(EPP(A,150,200,300,30))