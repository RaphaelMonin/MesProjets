import matplotlib.pyplot as plt
import statistics as s
import math as m
import random as rd
import time
import sys
from scipy.optimize import minimize
import numpy as np

def cercleCirconscrit(pA,pB,pC):
    '''Renvoie les coordonnées du centre et le rayon du cercle passant par les trois points'''
    xa, ya = pA
    xb, yb = pB
    xc, yc = pC
    xm1 = (xb + xa)/2
    ym1 = (yb + ya)/2
    xm2 = (xc + xb)/2
    ym2 = (yc + yb)/2
    xVm1 = yb-ya
    yVm1 = xa-xb
    xVm2 = yc-yb
    yVm2 = xb-xc
    k2 = (yVm1*xm1-xVm1*ym1-xm2*yVm1+ym2*xVm1)/(xVm2*yVm1-xVm1*yVm2)
    xC = xm2 + k2*xVm2
    yC = ym2 + k2*yVm2
    R = ((xC-xa)**2 + (yC-ya)**2)**(1/2)
    return (((xC,yC),R))

def est_dans(p,cercle):
    '''Renvoie True si p est dans le cercle, False sinon'''
    centre, rayon = cercle
    if centre == "tous les points":
        return False
    if rayon == 0:
        return p == centre
    distance = m.sqrt((p[0]-centre[0])**2+(p[1]-centre[1])**2)
    return distance <= rayon

def b_mdmax3(R):
    '''Renvoie le plus petit cercle contenant l'ensemble de points R,
    R contenant au maximum 3 points'''
    if len(R) == 0:
        centre = "tous les points"
        rayon = 0
    elif len(R) == 1:
        centre = R[0]
        rayon = 0
    elif len(R) == 2:
        centre = ((R[0][0]+R[1][0])/2, (R[0][1]+R[1][1])/2)
        rayon = m.sqrt((R[0][0]-centre[0])**2+(R[0][1]-centre[1])**2)
    else:
        for i in range(len(R)):
            cercle = b_mdmax3(R[:i]+R[i+1:])
            if est_dans(R[i],cercle):
                return cercle
        centre, rayon = cercleCirconscrit(R[0],R[1],R[2])
    return (centre,rayon)

def B_MINIDISK(P,R):
    '''Renvoie le plus petit cercle contenant l'ensemble
    de points P avec l'ensemble de points R à son bord'''
    if len(P) == 0 or len(R) == 3:
        cercle = b_mdmax3(R)
    else:
        i = rd.randint(0,len(P)-1)
        p = P[i]
        cercle = B_MINIDISK(P[:i]+P[i+1:], R)
        if not est_dans(p,cercle):
            cercle = B_MINIDISK(P[:i]+P[i+1:], R+[p])
    return cercle

def B_MINIDISK_FRONT(P,R):
    '''Renvoie le plus petit cercle contenant l'ensemble
    de points P avec l'ensemble de points R à son bord'''
    if len(P) == 0 or len(R) == 3:
        cercle = b_mdmax3(R)
    else:
        p = P[0]
        cercle = B_MINIDISK_FRONT(P[1:], R)
        if not est_dans(p,cercle):
            cercle = B_MINIDISK_FRONT(P[1:], [p]+R)
    return cercle

def resolve(P):
    ''' Résoud le problème de la séparabilité circulaire'''
    #Cas triviaux
    if len(P) == 1:
        return P[0], 0
    if len(P) == 0:
        return "Pas de points"
    cons = []
    for i in range(len(P)):
        cons.append({'type': 'ineq',
                     'fun': lambda x, i=i: x[2] - x[0] * P[i][0] - x[1] * P[i][1] - (
                                 P[i][0] ** 2 + P[i][1] ** 2)})

    x0 = np.array([0, 0, 0])
    res = minimize(func, x0, constraints=cons)

    A = -0.5 * res.x[0]
    B = -0.5 * res.x[1]
    R2 = res.x[2] + 0.25 * (res.x[0] ** 2 + res.x[1] ** 2)
    return ((A, B), R2 ** 0.5)


#La fonction
def func(x):
    return 1/4*(x[0]**2+x[1]**2) + x[2]

sys.setrecursionlimit(20100)
avec = []
sans = []
nouv = []
#nombre = [10, 100, 500, 1000, 2000, 3000, 4000, 5000, 8000, 10000]
nombre = [10, 50, 100, 250, 500, 750, 1000, 1500, 2000]
for nb in nombre:
    print(nb)
    ta = []
    tb = []
    tc = []
    for j in range(10):
        P = []
        for i in range(nb):
            P.append((round(rd.gauss(0,5),2),round(rd.gauss(0,5),2)))
        t1 = time.time()
        cercle1 = B_MINIDISK(P,[])
        t2= time.time()
        cercle2 = B_MINIDISK_FRONT(P,[])
        t3= time.time()
        cercle3 = resolve(P)
        t4 = time.time()
        ta.append(t2-t1)
        tb.append(t3-t2)
        tc.append(t4-t3)
    avec.append(round(s.mean(ta),4))
    sans.append(round(s.mean(tb),4))
    nouv.append(round(s.mean(tc),4))

plt.plot(nombre, nouv)
plt.plot(nombre, avec)
plt.plot(nombre, sans)
plt.xlabel("Nombre de points")
plt.ylabel("Temps en s")
plt.legend(['Scipy', 'Welzl (sans optimisation)', 'Welzl (avec optimisation)'])
plt.title("Temps de résolution moyen en fonction du nombre de points")
plt.show()

print(avec)
print(sans)
print(nouv)