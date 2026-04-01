import json
import random

# Charger la configuration
with open("config.json") as f:
    cfg = json.load(f)

T = cfg["taille"]

# Generating terrain (ref à minecraft)
def pos_aleas(n, excl, occ):
    pos = []
    while len(pos) < n:
        r, c = random.randint(0, T-1), random.randint(0, T-1)
        if (r, c) not in excl and (r, c) not in occ:
            pos.append((r, c))
            occ.add((r, c))
    return pos

occ = set()
batiments = pos_aleas(cfg["nb_batiments"], [], occ)
hopital = None
while hopital is None:
    r, c = random.randint(0, T-1), random.randint(0, T-1)
    if (r, c) not in occ:
        hopital = (r, c)
        occ.add(hopital)

survivants = []
for i, p in enumerate(pos_aleas(cfg["nb_survivants"], [hopital], occ), 1):
    survivants.append({"id": i, "pos": p})

tempetes = []
for i, p in enumerate(pos_aleas(cfg["nb_tempetes"], [], occ), 1):
    tempetes.append({"id": i, "pos": p})

drones = []
for i, p in enumerate(pos_aleas(cfg["nb_drones"], [], occ), 1):
    drones.append({"id": i, "pos": p, "batt": cfg["batterie_initiale"],
                   "etat": "actif", "charge": None, "desact": 0})

# grille
def grille():
    g = [['.' for _ in range(T)] for _ in range(T)]
    for r, c in batiments: g[r][c] = 'B'
    g[hopital[0]][hopital[1]] = 'H'
    for s in survivants: r, c = s["pos"]; g[r][c] = f"S{s['id']}"
    for t in tempetes: r, c = t["pos"]; g[r][c] = 'T'
    for d in drones: r, c = d["pos"]; g[r][c] = f"D{d['id']}"
    return g

def afficher():
    g = grille()
    print("   " + " ".join(f"{chr(65+i):2}" for i in range(T)))
    for i in range(T):
        print(f"{i:2} " + " ".join(f"{g[i][j]:2}" for j in range(T)))

def afficher_drones():
    print("Drones :")
    for d in drones:
        charge = d["charge"] or "aucun"
        print(f"  D{d['id']} : pos={chr(65+d['pos'][1])}{d['pos'][0]}, "
              f"batt={d['batt']}, état={d['etat']}, charge={charge}")

# recharge hopi
def recharger_drones(journal, tour):
    for d in drones:
        if d["pos"] == hopital :
            ancienne = d["batt"]
            d["batt"] = min(d["batt"] + cfg["recharge_hospital"], cfg["batterie_max"])
            if d["batt"] > ancienne:
                journal.append(f"Tour {tour} : D{d['id']} recharge sur hôpital → batt={d['batt']}.")

# Déplacement
def deplacement_valide(dest):
    r, c = dest
    return 0 <= r < T and 0 <= c < T and (r, c) not in batiments

def deplacer_drone(d, dest, score, journal, tour):
    r, c = dest
    cout = 1
    # Vérifier si on prend un survivant
    for s in survivants:
        if s["pos"] == (r, c) and d["charge"] is None:
            cout += 2
            break
    d["batt"] -= cout
    if d["batt"] < 0:
        d["batt"] = 0
        if d["etat"] == "actif":
            d["etat"] = "immobile"
            journal.append(f"Tour {tour} : D{d['id']} à court de batterie → immobile.")
    # Récupération du survivant
    for i, s in enumerate(survivants):
        if s["pos"] == (r, c) and d["charge"] is None:
            d["charge"] = s["id"]
            del survivants[i]
            journal.append(f"Tour {tour} : D{d['id']} récupère S{s['id']} (+2 énergie).")
            break
    # Dépser à l'hopi
    if (r, c) == hopital and d["charge"] is not None:
        score += 1
        journal.append(f"Tour {tour} : D{d['id']} sauve S{d['charge']} → +1 point.")
        d["charge"] = None
    # Déplacement effectif
    d["pos"] = dest
    return score, journal

def deplacer_tempete(t, journal, tour):
    r, c = t["pos"]
    dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    random.shuffle(dirs)
    for dr, dc in dirs:
        nr, nc = r+dr, c+dc
        if 0 <= nr < T and 0 <= nc < T and (nr, nc) not in batiments:
            t["pos"] = (nr, nc)
            # Collision avec un drone
            for d in drones:
                if d["pos"] == (nr, nc) and d["etat"] == "actif":
                    d["etat"] = "desactive"
                    d["desact"] = 2
                    journal.append(f"Tour {tour} : Tempête {t['id']} touche D{d['id']} → désactivé 2 tours.")
            return journal
    return journal

def update_desactivation(journal, tour):
    for d in drones:
        if d["etat"] == "desactive":
            d["desact"] -= 1
            if d["desact"] <= 0:
                d["etat"] = "actif"
                journal.append(f"Tour {tour} : D{d['id']} réactivé.")

# boucle du tour
score, tour = 0, 1
with open("journal.txt", "w") as f:
    f.write("Journal de la partie !\n")
while True:
    print(f"\nTour {tour}")
    afficher()
    print(f"Score : {score} | Survivants restants : {len(survivants)}")
    afficher_drones()

    # Phase drones
    deplaces = []
    for _ in range(3):
        choix = input("\nDrone à déplacer (id) ou 'f' : ").strip()
        if choix == 'f': break
        try:
            id_d = int(choix)
            if id_d in deplaces:
                print("Déjà déplacé ce tour.")
                continue
            d = next((d for d in drones if d["id"] == id_d), None)
            if not d: print("Drone inconnu."); continue
            if d["etat"] != "actif": print("Drone inactif."); continue
            if d["batt"] <= 0: print("Batterie vide."); continue
            print(f"Drone {id_d} en {chr(65+d['pos'][1])}{d['pos'][0]}")
            col, lig = input("Destination (colonne lettre ligne) : ").split()
            col = col.upper()
            dest = (int(lig), ord(col)-65)
            if not deplacement_valide(dest): print("Déplacement impossible..."); continue
            score, journal = deplacer_drone(d, dest, score, [], tour)
            deplaces.append(id_d)
            print("Déplacement fait :)")
            afficher()
        except: print("Format invalide. Exemple : C 5")

    # Phase tempetes (2 aléatoires)
    print("\nPhase tempêtes : 2 tempêtes se déplacent aléatoirement.")
    if len(tempetes) >= 2:
        indices = random.sample(range(len(tempetes)), 2)
        for idx in indices:
            journal = deplacer_tempete(tempetes[idx], [], tour)
            print(f"Tempête {tempetes[idx]['id']} a bougé.")
    else:
        indices = []
    afficher()

    # l'autre phase (autres 50%)
    print("\nPhase météo : les autres tempêtes ont 50% de chance de bouger.")
    for idx in range(len(tempetes)):
        if idx not in indices and random.random() < 0.5:
            journal = deplacer_tempete(tempetes[idx], [], tour)
            print(f"Tempête {tempetes[idx]['id']} a bougé (météo).")
    afficher()

    # Désactivations
    update_desactivation([], tour)

    # Recharge des drones sur l'hop
    recharger_drones([], tour)

    # Écriture journal
    with open("journal.txt", "a") as f:
        f.write(f"\nTour {tour}\n")
        for ligne in journal:
            f.write(ligne + "\n")
    journal = []

    # Fin de partie
    if len(survivants) == 0:
        print("\nTous les survivants sauvés ! Victoire !")
        break
    if all(d["etat"] != "actif" for d in drones):
        print("\nGAME OVER")
        break
    if tour >= 100:
        print("\nGAME OVER")
        break
    tour += 1

with open("score_final.txt", "w") as f:
    f.write(f"Score final : {score}\n")
print(f"\nScore final : {score}")