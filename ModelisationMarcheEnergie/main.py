import multiprocessing
import threading
import random
import signal
import queue
import time
import sys
import os

def t_consommateur(achats_market, q_market, full, empty, mutex, i):
    while True:
        j = 0
        full.acquire()
        with mutex:
            achats_market.value += q_market.get()
        empty.release()

def consommateur(pid_market, achats_market, q_market, full_market, empty_market, mutex_market, nT):
    pid_market.value = os.getpid()
    ## On crée nos threads chargées d'effectuer les transactions
    t_cons = []
    for i in range(nT):
        t_cons.append(threading.Thread(target = t_consommateur, args = (achats_market[i], q_market[i], full_market[i], empty_market[i], mutex_market[i], i)))
    ## On les lance
    for i in range(nT):
        t_cons[i].start()
    ## On attend qu'elles se terminent
    for i in range(nT):
        t_cons[i].join()    

def producteur(go, pause_homes, mutex_pause, flag, mutex_flag, conso_homes, produ_homes, carac, q_market, q_neighbour, full_market, empty_market, mutex_market, mutex_homes, i):
    produ_init = produ_homes[i] 
    conso_init = conso_homes[i]
    produ_homes[i] = 0
    conso_homes[i] = 0
    t1 = time.time()
    ## pour être sur
    while go.value != -1:
        t2 = time.time()
        ## Tant que go == 0 on a pas le droit de partir
        if go.value == 0:
            flag.value = 0
            pause_homes.value = 1
            mutex_pause.acquire()
            mutex_pause.release()
            pause_homes.value = 0
        ## On regarde si on consomme
        attendre = random.random()
        while attendre > 0.3:
            time.sleep(t2-t1)
            attendre = random.random()    
        ## On consomme
        t1 = time.time()
        a = random.randint(-2,2)
        b = random.randint(-2,2)
        produ_homes[i] += produ_init + a
        conso_homes[i] += conso_init + b
        consommation = produ_init - conso_init + a - b
        if consommation > 2:
            if carac == 1:
                ## On vend au marché
                empty_market.acquire()
                with mutex_market:
                    q_market.put(consommation)
                full_market.release()
            elif carac == 2:
                ## On donne à ses voisins
                with mutex_homes:
                    q_neighbour.put(consommation)
            else:
                ## On donne si preneur
                with mutex_homes:
                    if not q_neighbour.empty():
                        q_neighbour.put(consommation)
                ## Sinon on vend au marché
                if consommation > 2:
                    empty_market.acquire()
                    with mutex_market:
                        q_market.put(consommation)
                    full_market.release()
        if consommation < -2:
            ## On tente d'abord de récupéré de l'énergie laissé par ses voisins
            consobis = consommation
            while consobis < -2 and not q_neighbour.empty():
                with mutex_homes:
                    if not q_neighbour.empty():
                        consobis = consobis + q_neighbour.get()
                if consobis > 2:
                    with mutex_homes:
                        q_neighbour.put(consobis)
            ## Si il nous en manque encore on l'achete au market
            if consobis < -2:
                empty_market.acquire()
                with mutex_market:
                    q_market.put(consobis)
                full_market.release()
        ## On a fini notre transaction
        with mutex_flag:
            flag.value += 1

if __name__ == '__main__':
    ## On choisit le nombre de producteur et consommateur
    nH = int(sys.argv[1])
    nT = int(sys.argv[2])
    ## On crée notre queue et nos variables du nombre de d'achat au marché par queue, mutexes et semaphores pour le market
    q_market = []
    mutex_market = []
    full_market = []
    empty_market = []
    achats_market = []
    for i in range(nT):
        q_market.append(multiprocessing.Queue())
        mutex_market.append(multiprocessing.Lock())
        full_market.append(multiprocessing.Semaphore(0))
        empty_market.append(multiprocessing.Semaphore(5))
        achats_market.append(multiprocessing.Value('i', 0))
    ## Variable paratgé qui sert à transmettre le pid du market au process principal 
    pid_market = multiprocessing.Value('i', -1)
    ## On crée notre variable signal de depart
    NV = 5
    go = multiprocessing.Value('i', 0)
    ## On crée nos queues,  mutexes et flags pour les homes
    flag = []
    q_neighbour = []
    mutex_homes = []
    mutex_flag = []
    mutex_pause = []
    for i in range(nH//NV+1):
        q_neighbour.append(multiprocessing.Queue())
        mutex_flag.append(multiprocessing.Lock())
        mutex_homes.append(multiprocessing.Lock())
        flag.append(multiprocessing.Value('i', 0))
        mutex_pause.append(multiprocessing.Lock())
    ## On les crée ici
    pause_homes = []
    for i in range(nH):
        pause_homes.append(multiprocessing.Value('i', 0))
    ## On initialise les taux de consommations et de production de chaque home
    conso_homes_init = multiprocessing.Array('i', [random.randint(4,10) for i in range(nH)])
    conso_homes = conso_homes_init
    produ_homes_init = multiprocessing.Array('i', [random.randint(2,10) for i in range(nH)])
    produ_homes = produ_homes_init
    ## Initialisation des variable de calcul de prix
    prix_energie = [0.145]
    coeff_attenuation = 0.99
    nb_ventes_moyenne = nH*1*2/3
    coeff_modulation_vente_market = 0.01*prix_energie[0]/(nb_ventes_moyenne)
    ## Variable choix de l'utilisateur
    conti = " "
    print("\nSimulation avec ", nH, " processus foyers et ", nT, " transactions simultanées au maximum.")
    conti += input("\n\nCliquez sur ENTREE pour commencer la simulation\n\n")
    ## on crée nos processes
    prod = []
    cons = multiprocessing.Process(target = consommateur, args = (pid_market, achats_market, q_market, full_market, empty_market, mutex_market, nT))
    for i in range(nH):
        carac = i % 3 + 1        
        prod.append(multiprocessing.Process(target = producteur, args = (go, pause_homes[i], mutex_pause[i//NV], flag[i//NV], mutex_flag[i//NV], conso_homes, produ_homes, carac, q_market[i%nT], q_neighbour[i//NV], full_market[i%nT], empty_market[i%nT], mutex_market[i%nT], mutex_homes[i//NV], i)))
    ## On les bloque
    for i in range(nH//NV+1):
        mutex_pause[i].acquire()
    ## On les lances
    cons.start()
    for i in range(nH):
        prod[i].start()
    while conti == " ":
        ## On (re)part pour un tour
        go.value = 1
        for i in range(nH//NV+1):
            mutex_pause[i].release()
        somme = 0
        while somme < 40*nH:
            somme = 0
            for i in range(nH//NV+1):
                somme += flag[i].value
        for i in range(nH//NV+1):
            mutex_pause[i].acquire()
        go.value = 0
        ## On attend que tout le monde finisse son travail (quand le marché a terminé je crois)
        for i in range(nT):
            while not q_market[i].empty():
                pass
        for i in range(nH):
            while pause_homes[i].value != 1:
                pass
	## On vide les queues d'échanges d'énergie entre voisins
        for i in range(nH//NV+1):
            while not q_neighbour[i].empty():
                with mutex_homes[i]:
                    q_neighbour[i].get()
        ## On recupère la consommation et production des foyers et on les remet à zero
        consommation_homes = 0
        production_homes = 0
        for i in range(nH):
                production_homes += produ_homes[i]
                produ_homes[i] = 0
                consommation_homes += conso_homes[i]
                conso_homes[i] = 0
        ## On remet à zero les achats market en recupérant leur valeur
        achats_market_total = 0
        for i in range(nT):
            achats_market_total += achats_market[i].value
            achats_market[i].value = 0
        prix_energie.append(coeff_attenuation*prix_energie[-1]-coeff_modulation_vente_market*achats_market_total)
        print("Les ", nH, " foyers ont consommés : ", consommation_homes, " KWH")
        print("Les ", nH, " foyers ont produit : ", production_homes, " KWH")  
        print("Le marché a vendu (vendu-acheté) : ", -achats_market_total, " KWH")
        print("Le prix de l'énergie est de : ", prix_energie[-1], "€/kWh")
        conti += input("\n\nPour continuer la simulation : cliquez sur  ENTREE\n\nPour arrêter la simulation : cliquez sur ESPACE puis ENTREE\n\n")
    
    ## On arrête les homes:
    for i in range(nH//NV+1):
        mutex_pause[i].release()
    go.value = -1
    ## On les attend
    for i in range(nH):
        prod[i].join()
    ## On arrête le market
    os.kill(pid_market.value, signal.SIGTERM)
    cons.join()


