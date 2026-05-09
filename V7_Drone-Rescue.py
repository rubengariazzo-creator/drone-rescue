# on importe le module json pour lire le fichier de configuration
import json
# on importe le module random pour les tirages aleatoires
import random

# on ouvre le fichier config.json en mode lecture seule
with open("config.json", "r") as f:
    # on charge tout le contenu du fichier dans un dictionnaire cfg
    cfg = json.load(f)

# on recupere la taille de la grille (12) depuis la configuration
T = cfg["taille"]

# definition de la fonction qui genere des positions aleatoires uniques
def positions_aleatoires(n, excl, occ):
    # n est le nombre de positions a generer
    # excl est une liste de positions interdites (par ex l'hopital)
    # occ est une liste de positions deja occupees (batiments, drones, etc.)
    pos = []                     # liste vide qui va contenir les positions
    # tant qu'on n'a pas encore genere assez de positions
    while len(pos) < n:
        # on tire une ligne au hasard entre 0 et T-1
        r = random.randint(0, T-1)
        # on tire une colonne au hasard entre 0 et T-1
        c = random.randint(0, T-1)
        # on verifie si cette case est dans la liste des exclus
        exclu = False
        for (ex, ey) in excl:
            if (ex, ey) == (r, c):
                exclu = True
                break
        # on verifie si cette case est dans la liste des occupees
        occupe = False
        for (ox, oy) in occ:
            if (ox, oy) == (r, c):
                occupe = True
                break
        # si la case n'est ni exclue ni deja occupee, on l'accepte
        if not exclu and not occupe:
            pos.append((r, c))      # on ajoute la position a la liste
            occ.append((r, c))      # on la marque comme occupee pour la suite
    # on retourne la liste des positions generees
    return pos

# on cree une liste vide pour stocker toutes les positions occupees
occ = []
# on genere les batiments (obstacles) en utilisant la fonction
batiments = positions_aleatoires(cfg["nb_batiments"], [], occ)

# on initialise l'hopital a None, on va le choisir ensuite
hopital = None
# tant qu'on n'a pas trouve un emplacement pour l'hopital
while hopital is None:
    # on tire une ligne aleatoire
    r = random.randint(0, T-1)
    # on tire une colonne aleatoire
    c = random.randint(0, T-1)
    # on verifie si cette case est deja occupee par autre chose
    deja_pris = False
    for (x, y) in occ:
        if (x, y) == (r, c):
            deja_pris = True
            break
    # si la case est libre, on l'attribue a l'hopital
    if not deja_pris:
        hopital = (r, c)
        # on ajoute cette position a la liste des occupees
        occ.append(hopital)

# on cree une liste vide pour les survivants
survivants = []
# on genere les positions des survivants (en excluant l'hopital)
pos_surv = positions_aleatoires(cfg["nb_survivants"], [hopital], occ)
# on initialise un compteur d'identifiant a 1
i = 1
# on parcourt chaque position generee
for p in pos_surv:
    # on ajoute un dictionnaire representant un survivant
    survivants.append({"id": i, "pos": p})
    # on incremente le compteur pour le prochain survivant
    i = i + 1

# on cree une liste vide pour les tempetes
tempetes = []
# on genere les positions des tempetes
pos_temp = positions_aleatoires(cfg["nb_tempetes"], [], occ)
# on reinitialise le compteur a 1
i = 1
# on parcourt chaque position generee
for p in pos_temp:
    # on ajoute un dictionnaire representant une tempete
    tempetes.append({"id": i, "pos": p})
    i = i + 1

# on cree une liste vide pour les drones
drones = []
# on genere les positions des drones
pos_drones = positions_aleatoires(cfg["nb_drones"], [], occ)
# on reinitialise le compteur a 1
i = 1
# on parcourt chaque position generee
for p in pos_drones:
    # on ajoute un dictionnaire representant un drone avec tous ses attributs
    drones.append({
        "id": i, # numero du drone
        "pos": p, # position (ligne, colonne)
        "batt": cfg["batterie_initiale"], # batterie initiale
        "etat": "actif", # etat (actif, desactive, immobile)
        "charge": None, # survivant transporte (None = rien)
        "desact": 0 # compteur de tours de desactivation
    })
    i = i + 1

# fonction qui construit une grille a partir des entites du jeu
def construire_grille():
    # on cree une grille vide de taille T x T remplie de points
    g = [['.' for _ in range(T)] for _ in range(T)]
    # on place les batiments (obstacles)
    for r, c in batiments:
        g[r][c] = 'B'
    # on place l'hopital
    g[hopital[0]][hopital[1]] = 'H'
    # on place chaque survivant avec son identifiant
    for s in survivants:
        r, c = s["pos"]
        g[r][c] = "S%d" % s["id"]
    # on place chaque tempete (toutes ont le symbole T)
    for t in tempetes:
        r, c = t["pos"]
        g[r][c] = 'T'
    # on place chaque drone avec son identifiant
    for d in drones:
        r, c = d["pos"]
        g[r][c] = "D%d" % d["id"]
    # on retourne la grille complete
    return g

# fonction pour afficher la grille a l'ecran
def afficher_grille():
    # on obtient la grille actuelle
    g = construire_grille()
    # on prepare l'en-tete des colonnes (lettres A, B, C...)
    entete = "   "
    for i in range(T):
        # chr(65+i) donne A pour i=0, B pour i=1, etc.
        entete = entete + " %2s" % chr(65+i)
    print(entete)
    # on affiche chaque ligne de la grille
    for i in range(T):
        # on commence la ligne par le numero de ligne (sur 2 caracteres)
        ligne = "%2d " % i
        # on ajoute chaque colonne de la ligne
        for j in range(T):
            ligne = ligne + " %2s" % g[i][j]
        print(ligne)

# fonction pour afficher l'etat de tous les drones
def afficher_drones():
    print("Drones :")
    # on parcourt chaque drone
    for d in drones:
        # si le drone ne porte pas de survivant, on ecrit "aucun"
        if d["charge"] is None:
            charge = "aucun"
        else:
            # sinon on affiche l'identifiant du survivant porte
            charge = "S%d" % d["charge"]
        # on affiche les informations du drone
        print("  D%d : pos=%s%d, batt=%d, etat=%s, charge=%s" % (
            d["id"], chr(65+d["pos"][1]), d["pos"][0],
            d["batt"], d["etat"], charge))

# fonction pour recharger les drones qui sont sur l'hopital
def recharger_drones(journal, tour):
    # on parcourt tous les drones
    for d in drones:
        # si le drone est sur la case de l'hopital
        if d["pos"] == hopital:
            # on garde en memoire sa batterie avant recharge
            ancienne = d["batt"]
            # on ajoute la quantite de recharge, sans depasser la batterie max
            if d["batt"] + cfg["recharge_hospital"] > cfg["batterie_max"]:
                d["batt"] = cfg["batterie_max"]
            else:
                d["batt"] = d["batt"] + cfg["recharge_hospital"]
            # si la batterie a augmente, on enregistre dans le journal
            if d["batt"] > ancienne:
                journal.append("Tour %d : D%d recharge sur hopital donc batt=%d" % (tour, d["id"], d["batt"]))

# fonction qui verifie si un deplacement est possible
def deplacement_valide(dest):
    # dest est un tuple (ligne, colonne)
    r, c = dest
    # si la destination est hors de la grille, on refuse
    if r < 0 or r >= T or c < 0 or c >= T:
        return False
    # si la destination est un batiment, on refuse
    for (br, bc) in batiments:
        if (br, bc) == (r, c):
            return False
    # sinon le deplacement est valide
    return True

# fonction pour deplacer un drone (gestion complete du deplacement)
def deplacer_drone(d, dest, score, journal, tour):
    # d est le dictionnaire du drone, dest est la destination
    r, c = dest
    old_r, old_c = d["pos"]
    # on enregistre le deplacement dans le journal
    journal.append("Tour %d : D%d se deplace de %s%d vers %s%d" % (
        tour, d["id"], chr(65+old_c), old_r, chr(65+c), r))
    # cout energetique de base = 1
    cout = 1
    # on verifie si la case d'arrivee contient un survivant et si le drone est vide
    for s in survivants:
        if s["pos"] == (r, c) and d["charge"] is None:
            # si c'est le cas, on ajoute 2 au cout
            cout = cout + 2
            break
    # on soustrait le cout a la batterie
    d["batt"] = d["batt"] - cout
    # si la batterie devient negative, on la met a zero
    if d["batt"] < 0:
        d["batt"] = 0
        # et si le drone etait actif, il devient immobile
        if d["etat"] == "actif":
            d["etat"] = "immobile"
            journal.append("Tour %d : D%d a court de batterie et s immobilise" % (tour, d["id"]))
    # recuperation d'un survivant si la case en contient un
    i = 0
    while i < len(survivants):
        s = survivants[i]
        if s["pos"] == (r, c) and d["charge"] is None:
            # le drone charge le survivant
            d["charge"] = s["id"]
            # on supprime ce survivant de la liste
            del survivants[i]
            journal.append("Tour %d : D%d recupere S%d (+2 energie)" % (tour, d["id"], s["id"]))
            break
        i = i + 1
    # depot a l'hopital : si le drone arrive sur l'hopital avec un survivant
    if (r, c) == hopital and d["charge"] is not None:
        # on augmente le score de 1
        score = score + 1
        journal.append("Tour %d : D%d sauve S%d vous gagnez +1 point !!" % (tour, d["id"], d["charge"]))
        # le drone n'a plus de survivant
        d["charge"] = None
    # on met a jour la position du drone
    d["pos"] = (r, c)
    # on retourne le nouveau score et le journal mis a jour
    return score, journal

# fonction pour deplacer une tempete (deplacement aleatoire)
def deplacer_tempete(t, journal, tour):
    # t est le dictionnaire de la tempete
    r, c = t["pos"]
    # liste des 8 directions possibles (dont les diagonales)
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    # on essaye au maximum 20 fois de trouver une direction valide
    for _ in range(20):
        # on choisit un index au hasard dans la liste des directions
        idx = random.randint(0, len(directions)-1)
        dr, dc = directions[idx]
        nr, nc = r+dr, c+dc
        # on verifie que la nouvelle case est dans la grille
        if 0 <= nr < T and 0 <= nc < T:
            # on verifie que ce n'est pas un batiment
            ok = True
            for (br, bc) in batiments:
                if (br, bc) == (nr, nc):
                    ok = False
                    break
            if ok:
                # on deplace la tempete
                t["pos"] = (nr, nc)
                journal.append("Tour %d : Tempete %d bouge en %s%d" % (tour, t["id"], chr(65+nc), nr))
                # on verifie les collisions avec les drones actifs
                for d in drones:
                    if d["pos"] == (nr, nc) and d["etat"] == "actif":
                        d["etat"] = "desactive"
                        d["desact"] = 2
                        journal.append("Tour %d : Tempete %d touche D%d qui est desactive 2 tours" % (tour, t["id"], d["id"]))
                # on retourne le journal apres le deplacement
                return journal
    # si aucune direction valide n'a ete trouvee, la tempete ne bouge pas
    return journal

# fonction pour mettre a jour les compteurs de desactivation des drones
def update_desactivation(journal, tour):
    # on parcourt tous les drones
    for d in drones:
        # si le drone est desactive
        if d["etat"] == "desactive":
            # on decremente son compteur
            d["desact"] = d["desact"] - 1
            # si le compteur atteint 0 ou moins, on reactive le drone
            if d["desact"] <= 0:
                d["etat"] = "actif"
                journal.append("Tour %d : D%d reactive" % (tour, d["id"]))

# debut de la boucle principale du jeu
score = 0                  # score initial
tour = 1                   # numero du premier tour
# on cree le fichier journal.txt en ecrasant l'ancien
with open("journal.txt", "w") as f:
    f.write("Journal de la partie !\n")

# boucle infinie, on sortira par break quand la partie est finie
while True:
    # affichage du debut du tour
    print("\nTour %d" % tour)
    afficher_grille()
    # affichage du score et du nombre de survivants restants
    print("Score : %d | Survivants restants : %d" % (score, len(survivants)))
    afficher_drones()

    # liste des drones deja deplaces durant ce tour
    deplaces = []
    # liste des evenements du tour (initialement vide)
    journal = []
    # on autorise au maximum 3 deplacements de drones
    for _ in range(3):
        # on demande a l'utilisateur de choisir un drone
        choix = input("\nDrone a deplacer (id) ou 'f' pour finir le tour : ").strip()
        if choix == 'f':
            break
        try:
            id_d = int(choix)
            # on verifie si ce drone n'a pas deja ete deplace ce tour
            deja = False
            for did in deplaces:
                if did == id_d:
                    deja = True
                    break
            if deja:
                print("Deja deplace ce tour.")
                continue
            # on recherche le drone correspondant a l'id
            drone = None
            for d in drones:
                if d["id"] == id_d:
                    drone = d
                    break
            if drone is None:
                print("Drone inconnu.")
                continue
            # on verifie que le drone est actif
            if drone["etat"] != "actif":
                print("Drone inactif.")
                continue
            # on verifie qu'il a assez de batterie
            if drone["batt"] <= 0:
                print("Batterie vide.")
                continue
            # on affiche la position actuelle du drone
            print("Drone %d en %s%d" % (id_d, chr(65+drone["pos"][1]), drone["pos"][0]))
            # on demande la destination
            entree = input("Destination (colonne lettre ligne) : ").split()
            if len(entree) != 2:
                print("Format invalide. Exemple : C 5")
                continue
            col_lettre = entree[0].upper()
            ligne_dest = int(entree[1])
            # conversion lettre en indice de colonne (A->0, B->1, etc.)
            col_dest = ord(col_lettre) - 65
            dest = (ligne_dest, col_dest)
            # on verifie que le deplacement est valide
            if not deplacement_valide(dest):
                print("Deplacement impossible")
                continue
            # on effectue le deplacement
            score, journal = deplacer_drone(drone, dest, score, journal, tour)
            # on ajoute l'id du drone a la liste des deplaces
            deplaces.append(id_d)
            print("Deplacement effectue")
            # on reaffiche la grille apres le deplacement
            afficher_grille()
        except:
            # si une erreur survient (mauvaise saisie), on affiche un message
            print("Format invalide. Exemple : C 5")

    print("\nPhase tempetes : 2 tempetes se deplacent aleatoirement")
    if len(tempetes) >= 2:
        # on choisit deux indices differents au hasard
        idx1 = random.randint(0, len(tempetes)-1)
        idx2 = random.randint(0, len(tempetes)-1)
        while idx2 == idx1:
            idx2 = random.randint(0, len(tempetes)-1)
        indices = [idx1, idx2]
        # on deplace chaque tempete selectionnee
        for idx in indices:
            journal = deplacer_tempete(tempetes[idx], journal, tour)
            print("Tempete %d a bouge" % tempetes[idx]["id"])
    else:
        indices = []
    # on affiche la grille apres ces deplacements
    afficher_grille()

    print("\nPhase meteo : les autres tempetes ont 50%% de chance de bouger")
    # on parcourt toutes les tempetes
    for idx in range(len(tempetes)):
        # on verifie si cette tempete n'a pas deja ete deplacee
        deja_deplace = False
        for ii in indices:
            if ii == idx:
                deja_deplace = True
                break
        if not deja_deplace:
            # on tire un nombre aleatoire entre 0 et 1, si < 0.5 elle bouge
            if random.random() < 0.5:
                journal = deplacer_tempete(tempetes[idx], journal, tour)
                print("Tempete %d a bouge (meteo)" % tempetes[idx]["id"])
    # on affiche a nouveau la grille
    afficher_grille()

    # MAJ des désactivations
    update_desactivation(journal, tour)

    # recharge des drones sur l'hopital
    recharger_drones(journal, tour)

    # sauvegarde du journal
    with open("journal.txt", "a") as f:
        f.write("\nTour %d\n" % tour)
        for ligne in journal:
            f.write(ligne + "\n")

    # vérification des conditions de fin
    # si plus aucun survivant, victoire
    if len(survivants) == 0:
        print("\nTous les survivants sauves ! Victoire !")
        break
    # on verifie si tous les drones sont inactifs (aucun actif)
    tous_inactifs = True
    for d in drones:
        if d["etat"] == "actif":
            tous_inactifs = False
            break
    if tous_inactifs:
        print("\nGAME OVER")
        break
    # limite de securite de 10 tours (pour l'exemple)
    if tour >= 10:
        print("\nGAME OVER")
        break
    # on passe au tour suivant
    tour = tour + 1

# sauvegarde du score final
with open("score_final.txt", "w") as f:
    f.write("Score final : %d\n" % score)
print("\nScore final : %d" % score)