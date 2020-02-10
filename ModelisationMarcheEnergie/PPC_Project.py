import queue
import random as r
import math

def homes(idNumber, type):         ## fonction qui caractérise le comportement de notre foyer
    idNumber = iN        ## numéro unique qui caractérise le foyer
    cR[iN] = consumptionRate  ## quantité de consommation de notre foyer
    pR[iN] = productionRate  ## quantité de production de notre foyer
    product(cR[iN])  ## le foyer produit
    consum(pR[iN])  ## le foyer consomme
    if (pR[iN] > cR[iN]):      ## si notre foyer a trop d'énergie
        difference= pR[iN] - cR[iN]
        if type == 2 :          ## s'il est de type 2 il le vend au marché
            sell(difference)
        else:    ## sinon
            if giveAway(iN, difference):   ## il tente de le vendre à ses voisins
                sell(difference)   ## s'il n'a pas réussi et qu'il est de type 3 : il le vend alors au marché
        pR[iN] = cR[iN]    ## la consommation de notre foyer revient à l'équilibre
    elif (cR[iN] > pR[iN]):   ## si notre foyer a besoin d'énergie
        difference= cR[iN] - pR[iN]
        recoverEnergie(difference)    ## il en récupère: en achetant ou en recevant de l'énergie
        cR[iN] = pR[iN]  ## la consommation de notre foyer revient à l'équilibre
    internalFactors.append(quantity*coef2)

def market():
    sumExt=0
    sumInt=0
    for elem in externalFactors:
        sumExt += elem
    for elem in internalFactors:
        sumInt += elem
    #Température va s'exécuter en tant que process enfant de market et dont la valeur sera ajoutée dans internalFactors.
    currentEnergy = (coef1*energyPrice) + sumInt + sumExt
    return currentEnergy

def extFactors(valeurbinaire,événement): #un signal sera envoyé à Market avec comme argument un random entre 0 et 1
    #il faut toujours avoir au moins 2 facteurs externes
    listexternalFactors = ["C'est la crise économique!", "En ce moment, il y a un conflit politico-social","Grève"] #ajouter d'autres facteurs externes
    if valeurbinaire == 0: #si l'événement n'a plus lieu, on en cherche un autre
        valeurbinaire = 1
        nouvelévénement = r.randint(0, len(listexternalFactors-1))
        while nouvelévénement == événement:
            nouvelévénement = r.randint(0, len(listexternalFactors-1)) #génère un nouvel événement
    if valeurbinaire ==1: #l'événement a eu lieu
        print(listexternalFactors[r.randint(0, len(listexternalFactors - 1))])
    externalFactors.append(valeurbinaire * coef2) #la liste sera donc de la forme [1,1,0] par exemple
    return valeurbinaire, événement #la nouvelle valeur de l'événement ainsi que l'événement


def weather():  ## fonction qui represente les variations climatiques : elle agit sur deux paramètre : la période de l'année et la température qui dépend de la période
    # saison=?
    saison = saison + 1 % 4
    temperature = periode[saison] + r.randint(-10, 10)
    internalFactors.append(temperature * coef3)
    return temperature


def consum(consumptionRate):
    newtemperature = weather()
    #trouver formule evoluant de maniere exponentielle, car plus la température augmente moins on consomme de l'énergie
    coefficient = (consumptionRate / math.exp(-oldtemperature/100)) #on trouve oldtemperature dans la mémoire partagée
    consumptionRate= coefficient* math.exp(-newtemperature/100) #évolution de manière exponentielle
    return consumptionRate


def product(productionRate):
    quantityofProd= r.randint(0.01,10) #peut produire jusqu'à 10 fois son énergie actuelle
    return quantityofProd*productionRate


def giveAway(iN, quantity):
    qShareBetweenHomes.get = energiePresent
    did = False
    if energiePresent + quantity < 1000:   ## si notre homes peut mettre de l'énergie à disposition pour ces voisins
        qShareBetweenHomes.put(energiePresent + quantity)
        did = True
    else:      ## si elle ne peut pas
        qShareBetweenHomes.put(1000 - energiePresent - quantity)
    return did

def sell(quantity): #fonction exécutée par les homes qui ont de l'énergie à vendre
    previousQuantity = qSellMarket.get()
    qSellMarket.put(quantity + previousQuantity)
    factor = -quantity #pour baisser le prix de l'énergie
    internalFactors.append(factor * coef2)

def recoverEnergie(quantity):
    recovery = qSellMarket.get()  ## on récupère de l'énergie auprès de ces voisins
    if recovery > quantity:   ## si on a recupéré trop d'énergie
        qSellMarket.put = quantity - recovery    ## on rend ce qu'on a en trop
    elif quantity < recovery:   ## si on en a pas récupéré assez d'énergie
        previousQuantity = qBuyMarket.get() 
        qBuyMarket.put(quantity + previousQuantity)   ## on en récupère donc on rajoute cette quantité à la queue de l'énergie achetée sur le marché
    else:
        dBuyMarket.put(0)
    factor = quantity #acheter va augmenter le prix de l'énergie
    internalFactors.append(factor*coef2)




#Initialisation des paramètres
energyPrice= 0.15375 #initialisation du prix de l'énergie
coef1= 0.99 #initialisation du coef de l'énergie
type = r.randint(1, 3)  # le type de foyer est entre 1 et 3
qShareBetweenHomes = queue.Queue()
qSellMarket = queue.Queue()  ## queue représentant la quantité d'énergie vendu au marché par les foyers
qSellMarket.put(0)
qBuyMarket = queue.Queue()  ## queue représentant la quantité d'énergie achetée au marché par les foyers
qBuyMarket.put(0)
cR = []   ## tableau représentant la quantité d'énergie consommé par chaque foyer
pR = []   ## tableau représentant la quantité d'énergie produite par chaque foyer
externalFactors = [] #liste des facteurs externes, qui sera utilisée par Market pour calculer l'énergie
internalFactors= [] #liste des facteurs internes (homes et température)
periode = 10*[10]+10*[20]+10*[30]+10*[10]  ## tableau d'entiers 30 : été, 20, printemps et automne et 10 : hiver : 10 jours par saison



