import matplotlib.pyplot as plt

class ExecutionPlotter:
    def __init__(self, simulator):
        self.sim = simulator
        # Récupérer la liste des PIDs triée pour l'affichage (P1 en haut)
        pids = sorted(self.sim.processes.keys())
        self.y_map = {pid: i for i, pid in enumerate(reversed(pids))}

    def plot(self):
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # 1. Calculer la borne de temps max pour l'axe X
        max_time = self.sim.clock + 2
        
        # 2. Dessiner les lignes de vie (horizontales)
        for pid, y in self.y_map.items():
            ax.hlines(y, 0, max_time, colors='black', linewidth=1)
            ax.text(-1, y, pid, fontsize=12, fontweight='bold', va='center', ha='right')

        # 3. Dessiner les messages (Flèches) depuis les logs du simulateur
        for msg in self.sim.message_log:
            y_start = self.y_map[msg["src"]]
            y_end = self.y_map[msg["dst"]]
            
            # Styles selon le type
            if msg["type"] == "MARKER":
                color = 'red'
                style = '--'
                width = 1
                label = "" # On n'écrit pas "MARKER" pour ne pas surcharger
            else:
                color = 'blue'
                style = '-'
                width = 1.5
                # On affiche le contenu (ex: "M1")
                label = str(msg["content"]) if msg["content"] else ""

            # Flèche
            ax.annotate("",
                        xy=(msg["t_rcv"], y_end), xycoords='data',
                        xytext=(msg["t_send"], y_start), textcoords='data',
                        arrowprops=dict(arrowstyle='-|>', color=color, 
                                        linestyle=style, linewidth=width, alpha=0.7))
            
            # Texte du message (au milieu)
            if label:
                mid_time = (msg["t_send"] + msg["t_rcv"]) / 2
                mid_y = (y_start + y_end) / 2
                ax.text(mid_time, mid_y + 0.1, label, fontsize=8, color='blue', ha='center',
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))

        # 4. Dessiner les points de Snapshot (S_i)
        snapshot_xs = []
        snapshot_ys = []
        
        for pid, time in self.sim.snapshot_log.items():
            y = self.y_map[pid]
            ax.plot(time, y, 'ro', markersize=10, zorder=10)
            ax.text(time, y + 0.25, f"S_{pid}", color='red', ha='center', fontweight='bold')
            
            snapshot_xs.append(time)
            snapshot_ys.append(y)

        # 5. Tracer la Ligne de Coupure (Consistent Cut)
        if snapshot_xs:
            # On trie les points par Y pour tracer une ligne brisée propre
            sorted_points = sorted(zip(snapshot_ys, snapshot_xs))
            sy = [p[0] for p in sorted_points]
            sx = [p[1] for p in sorted_points]
            ax.plot(sx, sy, color='orange', linestyle=':', linewidth=2, label='Coupure (Snapshot)')

        # Décoration
        ax.set_xlabel("Temps Logique")
        ax.set_title("Diagramme Espace-Temps : Exécution du Snapshot Chandy-Lamport")
        ax.set_yticks([]) # Cacher les ticks Y
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        # Légende
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='blue', lw=2, label='Application Msg'),
            Line2D([0], [0], color='red', lw=1, linestyle='--', label='Marker Msg'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', label='Prise d\'État Local'),
            Line2D([0], [0], color='orange', linestyle=':', label='Ligne de Coupure')
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()
        plt.show()