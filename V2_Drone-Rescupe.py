import json
import random

# Charger la configuration
with open("config.json") as f:
    cfg = json.load(f)

T = cfg["taille"]

# génération random des positions
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

def afficher(g):
    print("   " + " ".join(f"{chr(65+i):2}" for i in range(T)))
    for i in range(T):
        print(f"{i:2} " + " ".join(f"{g[i][j]:2}" for j in range(T)))

def afficher_drones():
    print("Drones :")
    for d in drones:
        charge = d["charge"] or "aucun"
        print(f"  D{d['id']} : pos={chr(65+d['pos'][1])}{d['pos'][0]}, "
              f"batt={d['batt']}, état={d['etat']}, charge={charge}")

# déplacements
def deplacement_valide(g, dest):
    r, c = dest
    return 0 <= r < T and 0 <= c < T and g[r][c] != 'B'

def deplacer_drone(d, dest, g, score, journal, tour):
    r, c = dest
    old_r, old_c = d["pos"]
    cout = 1
    if g[r][c].startswith('S') and d["charge"] is None:
        cout += 1
    d["batt"] -= cout
    if d["batt"] < 0:
        d["batt"] = 0
        if d["etat"] == "actif":
            d["etat"] = "immobile"
            journal.append(f"Tour {tour} : D{d['id']} à court de batterie → immobile.")
    # Récupération
    if g[r][c].startswith('S') and d["charge"] is None:
        for i, s in enumerate(survivants):
            if s["pos"] == (r, c):
                d["charge"] = s["id"]
                del survivants[i]
                journal.append(f"Tour {tour} : D{d['id']} récupère S{s['id']} (+2 énergie).")
                break
    # Dépôt
    if (r, c) == hopital and d["charge"] is not None:
        score += 1
        journal.append(f"Tour {tour} : D{d['id']} sauve S{d['charge']} → +1 point.")
        d["charge"] = None
    # Recharge
    if (r, c) == hopital:
        d["batt"] = min(d["batt"] + cfg["recharge_hospital"], cfg["batterie_max"])
        journal.append(f"Tour {tour} : D{d['id']} recharge → batt={d['batt']}.")
    # Mise à jour position et grille
    g[old_r][old_c] = '.'
    g[r][c] = f"D{d['id']}"
    d["pos"] = dest
    return score, journal

def deplacer_tempete(t, g, journal, tour):
    r, c = t["pos"]
    dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    random.shuffle(dirs)
    for dr, dc in dirs:
        nr, nc = r+dr, c+dc
        if 0 <= nr < T and 0 <= nc < T and g[nr][nc] != 'B':
            g[r][c] = '.'
            g[nr][nc] = 'T'
            t["pos"] = (nr, nc)
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

# boucle principale
score, tour = 0, 1
g = grille()
with open("journal.txt", "w") as f: f.write("=== Journal du jeu Drone Rescue ===\n")
while True:
    print(f"\n--- Tour {tour} ---")
    afficher(g)
    print(f"Score : {score} | Survivants restants : {len(survivants)}")
    afficher_drones()

    # Phase drones (3 déplacements max, chacun une fois)
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
            if not deplacement_valide(g, dest): print("Déplacement impossible."); continue
            score, journal = deplacer_drone(d, dest, g, score, [], tour)
            deplaces.append(id_d)
            print("Déplacement effectué.")
            afficher(g)
        except: print("Format invalide. Exemple : C 5")

    # Phase tempêtes : 2 aléatoires
    print("\nPhase tempêtes : 2 tempêtes se déplacent aléatoirement.")
    if len(tempetes) >= 2:
        indices = random.sample(range(len(tempetes)), 2)
        for idx in indices:
            journal = deplacer_tempete(tempetes[idx], g, [], tour)
            print(f"Tempête {tempetes[idx]['id']} a bougé.")
    else:
        indices = []
    afficher(g)

    # Phase météo : autres 50%
    print("\nPhase météo : les autres tempêtes ont 50% de chance de bouger.")
    for idx in range(len(tempetes)):
        if idx not in indices and random.random() < 0.5:
            journal = deplacer_tempete(tempetes[idx], g, [], tour)
            print(f"Tempête {tempetes[idx]['id']} a bougé (météo).")
    afficher(g)

    # Désactivations
    update_desactivation([], tour)

    # Journal
    with open("journal.txt", "a") as f:
        f.write(f"\n--- Tour {tour} ---\n")
        for ligne in journal:
            f.write(ligne + "\n")
    journal = []

    # Fin de partie
    if len(survivants) == 0:
        print("\nTous les survivants sauvés ! Victoire !")
        break
    if all(d["etat"] != "actif" for d in drones):
        print("\nTous les drones hors service. Défaite.")
        break
    if tour >= 100:
        print("\nLimite de tours atteinte.")
        break
    tour += 1

with open("score_final.txt", "w") as f:
    f.write(f"Score final : {score}\n")
print(f"\nScore final : {score}")
