import matplotlib.pyplot as plt
from scipy.optimize import minimize
import numpy as np
import random as rd
import math as m
import time as t

def aff_points(P):
    '''Prépare l'affichage de l'ensemble de points P'''
    x, y = [], []
    for i in range(len(P)):
        x.append(P[i][0])
        y.append(P[i][1])
    plt.scatter(x,y)

def aff_circle(centre, rayon):
    '''Prépare l'affichage du cercle de centre centre et de rayon rayon'''
    if centre == "tous les points":
        return
    circ = plt.Circle(centre,radius = rayon, color='b', fill=False)
    ax=plt.gca()
    ax.add_patch(circ)
    plt.axis('scaled')

def résolution_equation(Pint, Pext):
    cons = []
    for i in range(len(Pint)):
        cons.append({'type': 'ineq',
                     'fun': lambda x, i=i, Pint=Pint: x[2] - x[0] * Pint[i][0] - x[1] * Pint[i][1] - (Pint[i][0] ** 2 + Pint[i][1] ** 2)})

    for i in range(len(Pext)):
        cons.append({'type': 'ineq',
                     'fun': lambda x, i=i, Pext=Pext: -x[2] + x[0] * Pext[i][0] + x[1] * Pext[i][1] + (Pext[i][0] ** 2 + Pext[i][1] ** 2)})

    x0 = np.array([0, 0, 0])
    res = minimize(func, x0, constraints=cons)

    A = -0.5 * res.x[0]
    B = -0.5 * res.x[1]
    R2 = res.x[2] + 0.25 * (res.x[0] ** 2 + res.x[1] ** 2)
    return ((A, B), R2 ** 0.5)

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

#La fonction
def func(x):
    return 1/4*(x[0]**2+x[1]**2) + x[2]

def resolve(P1,P2):
    ''' Résoud le problème de la séparabilité circulaire'''
    #Cas triviaux
    if len(P1) == 0:
        return "Pass"
    if len(P1) == 1:
        return (P1[0], 0)
    cercle = résolution_equation(P1, P2)
    for i in range(len(P1)):
        if ((P1[i][0] - cercle[0][0]) ** 2 + (P1[i][1] - cercle[0][1]) ** 2 > 1.01 * (cercle[1] ** 2)):
            return "Pas de cercle"
    for i in range(len(P2)):
        if ((P2[i][0] - cercle[0][0]) ** 2 + (P2[i][1] - cercle[0][1]) ** 2 <= 0.99 * (cercle[1] ** 2)):
            return "Pas de cercle"
    return cercle

def est_dans(p,cercle):
    '''Renvoie True si p est dans le cercle, False sinon'''
    if cercle == "Pas de cercle":
        return False
    if cercle == "Pass":
        return True
    centre = cercle[0]
    rayon = cercle[1]
    #if centre == "tous les points":
    #    return False
    if rayon == 0:
        return p == centre
    distance = m.sqrt((p[0]-centre[0])**2+(p[1]-centre[1])**2)
    return distance <= 1.001*rayon

def est_pas_dans(p,cercle):
    '''Renvoie True si p est dans le cercle, False sinon'''
    if cercle == "Pas de cercle":
        return False
    if cercle == "Pass":
        return True
    centre = cercle[0]
    rayon = cercle[1]
    #if centre == "tous les points":
    #    return False
    if rayon == 0:
        return p != centre
    distance = m.sqrt((p[0]-centre[0])**2+(p[1]-centre[1])**2)
    return distance > 0.999*rayon

def B_MINIDISK_FRONT(P,R,Pe,Re):
    '''Renvoie le plus petit cercle contenant l'ensemble
    de points P avec l'ensemble de points R à son bord'''
    if len(Pe) == 0 and (len(P) == 0 or len(R) == 3):
        if len(Re) == 0:
            cercle = b_mdmax3(R)
        else:
            cercle = resolve(R,Re)
    else:
        if len(Pe) == 0:
            choix = 0
        elif len(P) == 0:
            choix = 1
        else:
            choix = rd.randint(0,1)
        if choix == 1:
            p = Pe[0]
            cercle = B_MINIDISK_FRONT(P, R, Pe[1:], Re)
            if est_dans(p,cercle):
                cercle = B_MINIDISK_FRONT(P, R, Pe[1:], [p]+Re)
        else:
            p = P[0]
            cercle = B_MINIDISK_FRONT(P[1:], R, Pe, Re)
            if est_pas_dans(p,cercle):
                cercle = B_MINIDISK_FRONT(P[1:], [p]+R, Pe, Re)
    return cercle


#Les points
P1=[]
for i in range(100):
    P1.append((round(rd.gauss(-5,5),2),round(rd.gauss(-5,5),2)))

P2=[]
for i in range(100):
    P2.append((round(rd.gauss(5,5),2),round(rd.gauss(4,5),2)))

# Deux ensemble disjoints
if 1 == 0:
    P1 = []
    for i in range(5):
        P1.append((rd.uniform(-3, 0.5), rd.uniform(-3, 0.5)))

    P2 = []
    for i in range(4):
        P2.append((rd.uniform(0, 3), rd.uniform(0, 3)))

#Des points sur un cercle
if 1 == 0:
    P1 = []
    for i in range(5):
        a = 0.6*rd.random() * m.pi * 2
        P1.append((m.cos(a), m.sin(a)))
    P2 = []
    for i in range(5):
        a = -0.6*rd.random() * m.pi * 2
        P2.append((m.cos(a), m.sin(a)))

#Des points
if 1 == 0:
    P1 = []
    P1.append((0,1))
    P1.append((0,-1))
    P2 = []
    P2.append((0.25,0))
    P2.append((-1,1))

#On résoud

t1 = t.time()
cercle1 = resolve(P1,P2)
t2 = t.time()
cercle1 = B_MINIDISK_FRONT(P1, [], P2, [])
t3 = t.time()
print(t2-t1)
print(t3-t2)
print("1 ", cercle1)
cercle2 = resolve(P2,P1)
cercle2 = B_MINIDISK_FRONT(P2, [], P1, [])
print("2 ", cercle2)

#Affichage
aff_points(P1)
aff_points(P2)
if cercle1 != "Pas de cercle" and cercle1 != "Pass":
    aff_circle(cercle1[0], cercle1[1])
if cercle2 != "Pas de cercle" and cercle2 != "Pass":
    aff_circle(cercle2[0], cercle2[1])
plt.show()