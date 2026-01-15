# main.py
from simulator import Simulator
from process import Process 
from schema import ExecutionPlotter

def run_simulation():
    # 1. Initialisation
    sim = Simulator()

    # 2. Création des processus (P1, P2, P3)
    p1 = Process("P1", sim)
    p2 = Process("P2", sim)
    p3 = Process("P3", sim)

    sim.register_process(p1)
    sim.register_process(p2)
    sim.register_process(p3)

    # 3. Topologie "Mesh" (Tout le monde connecté à tout le monde)
    # Nécessaire pour que les marqueurs circulent partout comme sur le schéma
    p1.setup_topology(incoming=["P2", "P3"], outgoing=["P2", "P3"])
    p2.setup_topology(incoming=["P1", "P3"], outgoing=["P1", "P3"])
    p3.setup_topology(incoming=["P1", "P2"], outgoing=["P1", "P2"])

    # Helper pour planifier
    def schedule_send(time, src_proc, target_pid, content):
        action = lambda: src_proc.send_message(target_pid, content)
        sim.schedule(time, src_proc, action)

    print("--- Configuration du scénario (Basé sur vos images) ---")

    # === ÉTAPE 1 : Trafic Initial (Avant Snapshot) ===
    # Correspond au message H -> F (P3 vers P2) sur votre image
    schedule_send(1, p3, "P2", "Msg H->F")
    
    # Correspond au message B -> E (P1 vers P2)
    schedule_send(2, p1, "P2", "Msg B->E")

    # === ÉTAPE 2 : Le Snapshot (Point S1) ===
    # P1 initie le snapshot après avoir envoyé B
    # Si le délai réseau est de 5 (hardcodé dans Process), le marqueur arrivera à P2 vers T=11
    sim.schedule(6, p1, p1.initiate_snapshot)

    # === ÉTAPE 3 : Le Message Critique (G -> D) ===
    # P2 envoie un message vers P1.
    # CRITIQUE : Il doit partir AVANT que P2 reçoive le marqueur de P1.
    # Le marqueur de P1 part à T=6, arrive à T=11 (si délai=5).
    # Donc on envoie G à T=8.
    # Ce message arrivera à P1 à T=13.
    # P1 ayant commencé son snapshot à T=6, il sera en train d'enregistrer le canal P2->P1.
    # P1 recevra le marqueur de retour de P2 seulement vers T=16 (approx).
    # Donc ce message sera CAPTURÉ (c21).
    schedule_send(8, p2, "P1", "Msg G->D")

    # === ÉTAPE 4 : Trafic Post-Snapshot ===
    # Correspond au message E -> J (P1 vers P3) sur votre image (droite du schéma)
    schedule_send(20, p1, "P3", "Msg E->J")

    # 5. Lancer la simulation
    sim.run()

    # 6. Affichage des résultats textuels
    print("\n" + "="*40)
    print(" RÉSULTATS DU SNAPSHOT GLOBAL")
    print("="*40)
    
    for p in [p1, p2, p3]:
        print(f"\nProcessus {p.pid}:")
        print(f"  > État Local capturé : {p.snapshot_local_state}")
        print("  > État des canaux entrants :")
        if not p.channel_states:
            print("    (Aucun message capturé)")
        else:
            for neighbor, msgs in p.channel_states.items():
                if msgs:
                    # C'est ici qu'on attend de voir "Msg G->D" chez P1
                    print(f"    From {neighbor}: {msgs}") 
                else:
                    print(f"    From {neighbor}: <Vide>")

    return sim

if __name__ == "__main__":
    sim = run_simulation()
    
    print("\nGénération du graphique...")
    plotter = ExecutionPlotter(sim)
    plotter.plot()