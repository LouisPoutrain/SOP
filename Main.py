from simulator import Simulator
# Assurez-vous que Process est bien importé depuis votre fichier process.py
from process import Process 
# Assurez-vous que ExecutionPlotter est bien importé depuis votre fichier shema.py
from shema import ExecutionPlotter 

def run_simulation():
    # 1. Initialisation du simulateur
    sim = Simulator()

    # 2. Création des processus
    p1 = Process("P1", sim)
    p2 = Process("P2", sim)
    p3 = Process("P3", sim)
    p4 = Process("P4", sim)

    sim.register_process(p1)
    sim.register_process(p2)
    sim.register_process(p3)
    sim.register_process(p4)

    # 3. Configuration de la topologie
    p1.setup_topology(incoming=["P4", "P2"], outgoing=["P2", "P4"])
    p2.setup_topology(incoming=["P1", "P3"], outgoing=["P3", "P1"])
    p3.setup_topology(incoming=["P2", "P4"], outgoing=["P4", "P2"])
    p4.setup_topology(incoming=["P3", "P1"], outgoing=["P1", "P3"])

    # Helper pour planifier des envois
    def schedule_send(time, src_proc, target_pid, content):
        action = lambda: src_proc.send_message(target_pid, content)
        sim.schedule(time, src_proc, action)

    print("--- Configuration du scénario ---")

    # 4. Scénario
    schedule_send(1, p1, "P2", "M1 (Pre-Snap)")
    schedule_send(2, p2, "P3", "M2 (Pre-Snap)")
    schedule_send(3, p4, "P1", "M3 (Pre-Snap)")

    # T=10 : P3 Initie le Snapshot
    sim.schedule(10, p3, p3.initiate_snapshot)

    # Messages critiques pendant le snapshot
    schedule_send(12, p1, "P2", "M4 (In-Flight?)")
    schedule_send(13, p2, "P3", "M5 (In-Flight?)")
    
    # Message post-snapshot
    schedule_send(25, p3, "P4", "M6 (Post-Snap)")

    # 5. Lancer la simulation
    sim.run()

    # 6. Affichage Console
    print("\n" + "="*40)
    print(" RÉSULTATS DU SNAPSHOT GLOBAL")
    print("="*40)
    
    all_processes = [p1, p2, p3, p4]
    for p in all_processes:
        print(f"\nProcessus {p.pid}:")
        print(f"  > État Local capturé : {p.snapshot_local_state}")
        print("  > État des canaux entrants :")
        if not p.channel_states:
            print("    (Aucun message capturé)")
        else:
            for neighbor, msgs in p.channel_states.items():
                if msgs:
                    print(f"    From {neighbor}: {msgs}")
                else:
                    print(f"    From {neighbor}: <Vide>")

    # --- CORRECTION IMPORTANTE ---
    return sim

if __name__ == "__main__":
    # On récupère l'objet sim retourné par la fonction
    sim = run_simulation()
    
    print("\nGénération du graphique...")
    plotter = ExecutionPlotter(sim)
    plotter.plot()