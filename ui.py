import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial

from simulator import Simulator
from process import Process
from schema import ExecutionPlotter


class SimulationUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOP - Simulation Snapshot")
        self.geometry("960x640")

        self.events = []
        self.event_counter = 0
        self.show_plot_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Top: Process IDs
        proc_frame = ttk.LabelFrame(container, text="Processus")
        proc_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(proc_frame, text="IDs (ex: P1,P2,P3)").pack(side=tk.LEFT, padx=5)
        self.process_ids_entry = ttk.Entry(proc_frame, width=40)
        self.process_ids_entry.insert(0, "P1,P2,P3")
        self.process_ids_entry.pack(side=tk.LEFT, padx=5)

        # Events list
        events_frame = ttk.LabelFrame(container, text="Événements")
        events_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("time", "type", "src", "dst", "content")
        self.events_tree = ttk.Treeview(events_frame, columns=columns, show="headings", height=8)
        self.events_tree.heading("time", text="Temps")
        self.events_tree.heading("type", text="Type")
        self.events_tree.heading("src", text="Source")
        self.events_tree.heading("dst", text="Cible")
        self.events_tree.heading("content", text="Contenu")
        self.events_tree.column("time", width=80, anchor=tk.CENTER)
        self.events_tree.column("type", width=100, anchor=tk.CENTER)
        self.events_tree.column("src", width=80, anchor=tk.CENTER)
        self.events_tree.column("dst", width=80, anchor=tk.CENTER)
        self.events_tree.column("content", width=300, anchor=tk.W)
        self.events_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        buttons_frame = ttk.Frame(events_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Supprimer sélection", command=self._remove_selected).pack(side=tk.LEFT)
        ttk.Button(buttons_frame, text="Vider la liste", command=self._clear_events).pack(side=tk.LEFT, padx=5)

        # Add message section
        add_msg_frame = ttk.LabelFrame(container, text="Ajouter un message")
        add_msg_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(add_msg_frame, text="Temps").grid(row=0, column=0, padx=5, pady=2)
        self.msg_time_entry = ttk.Entry(add_msg_frame, width=8)
        self.msg_time_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(add_msg_frame, text="Source").grid(row=0, column=2, padx=5, pady=2)
        self.msg_src_entry = ttk.Entry(add_msg_frame, width=8)
        self.msg_src_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(add_msg_frame, text="Cible").grid(row=0, column=4, padx=5, pady=2)
        self.msg_dst_entry = ttk.Entry(add_msg_frame, width=8)
        self.msg_dst_entry.grid(row=0, column=5, padx=5, pady=2)

        ttk.Label(add_msg_frame, text="Contenu").grid(row=0, column=6, padx=5, pady=2)
        self.msg_content_entry = ttk.Entry(add_msg_frame, width=30)
        self.msg_content_entry.grid(row=0, column=7, padx=5, pady=2)

        ttk.Button(add_msg_frame, text="Ajouter", command=self._add_message_event).grid(row=0, column=8, padx=5, pady=2)

        # Add snapshot section
        add_snap_frame = ttk.LabelFrame(container, text="Ajouter un snapshot")
        add_snap_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(add_snap_frame, text="Temps").grid(row=0, column=0, padx=5, pady=2)
        self.snap_time_entry = ttk.Entry(add_snap_frame, width=8)
        self.snap_time_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(add_snap_frame, text="Processus").grid(row=0, column=2, padx=5, pady=2)
        self.snap_pid_entry = ttk.Entry(add_snap_frame, width=8)
        self.snap_pid_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Button(add_snap_frame, text="Ajouter", command=self._add_snapshot_event).grid(row=0, column=4, padx=5, pady=2)

        # Run section
        run_frame = ttk.Frame(container)
        run_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Checkbutton(run_frame, text="Afficher le graphique", variable=self.show_plot_var).pack(side=tk.LEFT)
        ttk.Button(run_frame, text="Lancer la simulation", command=self._run_simulation).pack(side=tk.RIGHT)

        # Output
        output_frame = ttk.LabelFrame(container, text="Résultats")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text = tk.Text(output_frame, height=10, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _get_process_ids(self):
        raw = self.process_ids_entry.get().strip()
        if not raw:
            raise ValueError("Veuillez saisir au moins un ID de processus.")
        parts = [p.strip() for p in raw.replace(";", ",").replace(" ", ",").split(",")]
        pids = [p for p in parts if p]
        if len(pids) < 2:
            raise ValueError("Au moins 2 processus sont nécessaires.")
        # Uniques tout en conservant l'ordre
        seen = set()
        unique = []
        for pid in pids:
            if pid not in seen:
                unique.append(pid)
                seen.add(pid)
        return unique

    def _add_message_event(self):
        try:
            time_val = float(self.msg_time_entry.get())
            src = self.msg_src_entry.get().strip()
            dst = self.msg_dst_entry.get().strip()
            content = self.msg_content_entry.get().strip()
            if not src or not dst or not content:
                raise ValueError("Source, cible et contenu sont obligatoires.")
            pids = self._get_process_ids()
            if src not in pids or dst not in pids:
                raise ValueError("Source ou cible inconnue.")
            self._add_event({
                "time": time_val,
                "type": "MESSAGE",
                "src": src,
                "dst": dst,
                "content": content,
            })
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def _add_snapshot_event(self):
        try:
            time_val = float(self.snap_time_entry.get())
            pid = self.snap_pid_entry.get().strip()
            if not pid:
                raise ValueError("Processus obligatoire.")
            pids = self._get_process_ids()
            if pid not in pids:
                raise ValueError("Processus inconnu.")
            self._add_event({
                "time": time_val,
                "type": "SNAPSHOT",
                "pid": pid,
                "src": pid,
                "dst": "-",
                "content": "-",
            })
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def _add_event(self, event):
        self.event_counter += 1
        event_id = f"evt-{self.event_counter}"
        event["id"] = event_id
        self.events.append(event)
        self.events_tree.insert("", tk.END, iid=event_id, values=(
            event.get("time"),
            event.get("type"),
            event.get("src", ""),
            event.get("dst", ""),
            event.get("content", "")
        ))

    def _remove_selected(self):
        selection = self.events_tree.selection()
        if not selection:
            return
        for item in selection:
            self.events_tree.delete(item)
            self.events = [e for e in self.events if e.get("id") != item]

    def _clear_events(self):
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)
        self.events = []

    def _run_simulation(self):
        try:
            pids = self._get_process_ids()
            if not self.events:
                raise ValueError("Ajoutez au moins un événement.")

            sim = Simulator()
            processes = {}
            for pid in pids:
                proc = Process(pid, sim)
                processes[pid] = proc
                sim.register_process(proc)

            # Topologie mesh (tous connectés)
            for pid, proc in processes.items():
                incoming = [p for p in pids if p != pid]
                outgoing = [p for p in pids if p != pid]
                proc.setup_topology(incoming=incoming, outgoing=outgoing)

            # Planification des événements
            for event in sorted(self.events, key=lambda e: e["time"]):
                time_val = event["time"]
                if event["type"] == "MESSAGE":
                    src = processes[event["src"]]
                    dst = event["dst"]
                    content = event["content"]
                    action = partial(src.send_message, dst, content)
                    sim.schedule(time_val, src, action)
                elif event["type"] == "SNAPSHOT":
                    proc = processes[event["pid"]]
                    sim.schedule(time_val, proc, proc.initiate_snapshot)

            # Exécution
            sim.run()

            # Résultats
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "=" * 40 + "\n")
            self.output_text.insert(tk.END, "RÉSULTATS DU SNAPSHOT GLOBAL\n")
            self.output_text.insert(tk.END, "=" * 40 + "\n")
            for pid in pids:
                proc = processes[pid]
                self.output_text.insert(tk.END, f"\nProcessus {pid}:\n")
                self.output_text.insert(tk.END, f"  > État Local capturé : {proc.snapshot_local_state}\n")
                self.output_text.insert(tk.END, "  > État des canaux entrants :\n")
                if not proc.channel_states:
                    self.output_text.insert(tk.END, "    (Aucun message capturé)\n")
                else:
                    for neighbor, msgs in proc.channel_states.items():
                        if msgs:
                            self.output_text.insert(tk.END, f"    From {neighbor}: {msgs}\n")
                        else:
                            self.output_text.insert(tk.END, f"    From {neighbor}: <Vide>\n")

            if self.show_plot_var.get():
                plotter = ExecutionPlotter(sim)
                plotter.plot()

        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))


if __name__ == "__main__":
    app = SimulationUI()
    app.mainloop()
