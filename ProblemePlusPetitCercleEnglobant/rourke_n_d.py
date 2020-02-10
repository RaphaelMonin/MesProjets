import matplotlib.pyplot as plt
from scipy.optimize import minimize
import numpy as np
import random as rd
import time

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


def resolve(P):
    ''' Résoud le problème de la séparabilité circulaire'''
    #Cas triviaux
    if len(P) == 1:
        return P[0], 0
    if len(P) == 0:
        return "Pas de points"
    n = len(P[0])+1
    cons = []
    for i in range(len(P)):
        cons.append({'type': 'ineq',
                     'fun': lambda x, n=n, i=i, P=P: test(x, i, n, P)})

    x0 = np.zeros(n)
    res = minimize(func, x0, args = n, constraints=cons)

    centre = []
    for i in range(n-1):
        centre.append(-0.5 * res.x[i])
    interR2 = 0
    for i in range(n-1):
        interR2 += res.x[i] ** 2
    R2 = res.x[n-1] + 0.25 * interR2
    return (centre, R2 ** 0.5)


def test(x, i, n, P):
    inter = 0
    for j in range(n-1):
        inter = inter + x[j] * P[i][j] + P[i][j] ** 2
    fin = x[n-1] - inter
    return fin

#La fonction
def func(x, n):
    inter = 0
    for i in range(n-1):
        inter += x[i]**2
    return inter*0.25 +x[n-1]

#Les points
nb_points = 20
dimension = 40
P=[]
for i in range(nb_points):
    P.append([round(rd.gauss(0,5),2) for i in range(dimension)])

if 1 == 0:
    P = []
    P.append((1,0))
    P.append((0,1))

#Affichage
print("Les points : ")
for i in range(len(P)):
    print(P[i])

#On résoud
t1 = time.time()
cercle = resolve(P)
t2 = time.time()
print("Temps de résolution : ", t2-t1)
print("Points à l'interieur ou au bord, distance")
for i in range(len(P)):
    distance = 0
    for j in range(len(P[0])):
        distance += (P[i][j]-cercle[0][j]) ** 2
    if (distance) <= 1.01*(cercle[1] ** 2):
        print(True, cercle[1] ** 2 - distance)
    else:
        print(False)

aff_points(P)
if cercle != "Pas de points":
    print("Solution : ", cercle)
    aff_circle(cercle[0], cercle[1])
else:
    print(cercle)
plt.show()