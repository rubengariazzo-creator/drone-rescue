import json
import random
import numpy as np

# ---------- Configuration ----------
def charger_config(fichier):
    with open(fichier, 'r') as f:
        return json.load(f)

# ---------- Génération aléatoire des positions ----------
def positions_aleatoires(n, exclude, occupees, taille):
    positions = []
    while len(positions) < n:
        r = random.randint(0, taille-1)
        c = random.randint(0, taille-1)
        if (r, c) not in exclude and (r, c) not in occupees:
            positions.append((r, c))
            occupees.add((r, c))
    return positions

def initialiser_jeu(config):
    t = config["taille"]
    occupees = set()
    # Bâtiments
    batiments = positions_aleatoires(config["nb_batiments"], [], occupees, t)
    # Hôpital
    hospital = None
    while hospital is None:
        r = random.randint(0, t-1)
        c = random.randint(0, t-1)
        if (r, c) not in occupees:
            hospital = (r, c)
            occupees.add(hospital)
    # Survivants (dictionnaires)
    survivants = []
    for i, (r, c) in enumerate(positions_aleatoires(config["nb_survivants"], [hospital], occupees, t), 1):
        survivants.append({"id": i, "pos": (r, c)})
    # Tempêtes (dictionnaires)
    tempetes = []
    for i, (r, c) in enumerate(positions_aleatoires(config["nb_tempetes"], [], occupees, t), 1):
        tempetes.append({"id": i, "pos": (r, c)})
    # Drones (dictionnaires)
    drones = []
    for i, (r, c) in enumerate(positions_aleatoires(config["nb_drones"], [], occupees, t), 1):
        drones.append({
            "id": i,
            "pos": (r, c),
            "batterie": config["batterie_initiale"],
            "etat": "actif",
            "charge": None,
            "desactivation": 0
        })
    return drones, tempetes, survivants, hospital, batiments, t

# ---------- Grille (numpy) ----------
def construire_grille(drones, tempetes, survivants, hospital, batiments, taille):
    grille = np.full((taille, taille), '.', dtype='<U2')
    for r, c in batiments:
        grille[r, c] = 'B'
    hr, hc = hospital
    grille[hr, hc] = 'H'
    for s in survivants:
        r, c = s["pos"]
        grille[r, c] = f"S{s['id']}"
    for t in tempetes:
        r, c = t["pos"]
        grille[r, c] = 'T'
    for d in drones:
        r, c = d["pos"]
        grille[r, c] = f"D{d['id']}"
    return grille

def afficher_grille(grille, taille):
    # En-tête des colonnes (lettres)
    entete = "   " + " ".join(chr(ord('A') + i) for i in range(taille))
    print(entete)
    for i in range(taille):
        ligne = f"{i:2} " + " ".join(f"{grille[i, j]:2}" for j in range(taille))
        print(ligne)

def afficher_drones(drones):
    print("Drones :")
    for d in drones:
        charge = d["charge"] if d["charge"] else "aucun"
        print(f"  D{d['id']} : pos={chr(ord('A')+d['pos'][1])}{d['pos'][0]}, "
              f"batt={d['batterie']}, état={d['etat']}, charge={charge}")

# ---------- Déplacements ----------
def valider_deplacement(grille, dest, taille):
    r, c = dest
    return 0 <= r < taille and 0 <= c < taille and grille[r, c] != 'B'

def deplacer_drone(d, dest, grille, survivants, hospital, score, journal, tour, config):
    r, c = dest
    ancien_r, ancien_c = d["pos"]
    # Mise à jour grille
    grille[ancien_r, ancien_c] = '.'
    grille[r, c] = f"D{d['id']}"
    # Coût énergétique : 1 par case, +2 si on prend un survivant (une seule fois)
    cout = 1
    if grille[r, c].startswith('S') and d["charge"] is None:
        cout += 2  # coût pour prendre le survivant
    d["batterie"] -= cout
    if d["batterie"] < 0:
        d["batterie"] = 0
        if d["etat"] == "actif":
            d["etat"] = "immobile"
            journal.append(f"Tour {tour} : D{d['id']} à court de batterie → immobile.")
    # Récupération survivant
    if grille[r, c].startswith('S') and d["charge"] is None:
        for i, s in enumerate(survivants):
            if s["pos"] == (r, c):
                d["charge"] = s["id"]
                del survivants[i]
                journal.append(f"Tour {tour} : D{d['id']} récupère S{s['id']} (coût +2).")
                break
    # Dépôt à l'hôpital
    if (r, c) == hospital and d["charge"] is not None:
        score += 1
        journal.append(f"Tour {tour} : D{d['id']} sauve S{d['charge']} → +1 point.")
        d["charge"] = None
    # Recharge
    if (r, c) == hospital:
        d["batterie"] = min(d["batterie"] + config["recharge_hospital"], config["batterie_max"])
        journal.append(f"Tour {tour} : D{d['id']} recharge → batterie = {d['batterie']}.")
    d["pos"] = dest
    return score, journal

def deplacer_tempete(t, grille, drones, journal, tour, taille):
    r, c = t["pos"]
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    random.shuffle(directions)
    for dr, dc in directions:
        nr, nc = r+dr, c+dc
        if 0 <= nr < taille and 0 <= nc < taille and grille[nr, nc] != 'B':
            grille[r, c] = '.'
            grille[nr, nc] = 'T'
            t["pos"] = (nr, nc)
            for d in drones:
                if d["pos"] == (nr, nc) and d["etat"] == "actif":
                    d["etat"] = "desactive"
                    d["desactivation"] = 2
                    journal.append(f"Tour {tour} : Tempête {t['id']} touche D{d['id']} → désactivé 2 tours.")
            return journal
    return journal

def update_desactivation(drones, journal, tour):
    for d in drones:
        if d["etat"] == "desactive":
            d["desactivation"] -= 1
            if d["desactivation"] <= 0:
                d["etat"] = "actif"
                journal.append(f"Tour {tour} : D{d['id']} réactivé.")

# ---------- Journal ----------
def sauvegarder_journal(tour, journal):
    with open("journal.txt", "a") as f:
        f.write(f"\n--- Tour {tour} ---\n")
        for ligne in journal:
            f.write(ligne + "\n")

# ---------- Boucle principale ----------
def main():
    config = charger_config("config.json")
    drones, tempetes, survivants, hospital, batiments, taille = initialiser_jeu(config)
    grille = construire_grille(drones, tempetes, survivants, hospital, batiments, taille)
    score = 0
    journal = []
    tour = 1
    with open("journal.txt", "w") as f:
        f.write("=== Journal du jeu Drone Rescue ===\n")
    while True:
        print(f"\n--- Tour {tour} ---")
        afficher_grille(grille, taille)
        print(f"Score : {score} | Survivants restants : {len(survivants)}")
        afficher_drones(drones)

        # Phase drones (max 3, chacun une fois)
        deplaces = []
        for _ in range(3):
            print("\nDrone à déplacer (id) ou 'f' pour finir : ", end="")
            choix = input().strip()
            if choix.lower() == 'f':
                break
            try:
                id_d = int(choix)
            except:
                print("Id invalide.")
                continue
            if id_d in deplaces:
                print("Ce drone a déjà bougé ce tour.")
                continue
            d = next((d for d in drones if d["id"] == id_d), None)
            if not d:
                print("Drone inexistant.")
                continue
            if d["etat"] != "actif":
                print("Drone désactivé ou immobilisé.")
                continue
            if d["batterie"] <= 0:
                print("Batterie vide.")
                continue
            print(f"Drone {id_d} en {chr(ord('A')+d['pos'][1])}{d['pos'][0]}")
            print("Destination (colonne lettre ligne nombre) : ", end="")
            try:
                col, lig = input().strip().split()
                col = col.upper()
                c = ord(col) - ord('A')
                r = int(lig)
                dest = (r, c)
            except:
                print("Format invalide. Exemple : C 5")
                continue
            if not valider_deplacement(grille, dest, taille):
                print("Déplacement impossible (obstacle ou hors grille).")
                continue
            score, journal = deplacer_drone(d, dest, grille, survivants, hospital, score, journal, tour, config)
            deplaces.append(id_d)
            print("Déplacement effectué.")
            afficher_grille(grille, taille)

        # Phase tempêtes : 2 aléatoires
        print("\nPhase tempêtes : 2 tempêtes se déplacent aléatoirement.")
        if len(tempetes) >= 2:
            indices = random.sample(range(len(tempetes)), 2)
            for idx in indices:
                journal = deplacer_tempete(tempetes[idx], grille, drones, journal, tour, taille)
                print(f"Tempête {tempetes[idx]['id']} a bougé.")
        else:
            indices = []
        afficher_grille(grille, taille)

        # Phase météo : les autres 50%
        print("\nPhase météo : les tempêtes restantes ont 50% de chance de bouger.")
        for idx in range(len(tempetes)):
            if idx not in indices:
                if random.random() < 0.5:
                    journal = deplacer_tempete(tempetes[idx], grille, drones, journal, tour, taille)
                    print(f"Tempête {tempetes[idx]['id']} a bougé (météo).")
        afficher_grille(grille, taille)

        # Désactivations
        update_desactivation(drones, journal, tour)

        # Sauvegarde journal
        sauvegarder_journal(tour, journal)
        journal.clear()

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

if __name__ == "__main__":
    main()