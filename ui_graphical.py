import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial

from simulator import Simulator
from process import Process
from schema import ExecutionPlotter


class GraphicalSimulationUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOP - Simulation Snapshot (Graphique)")
        # Maximize window at startup (cross-platform)
        try:
            self.state('zoomed')  # Works on Windows and macOS
        except:
            self.geometry("1400x900")  # Fallback for other systems
        
        self.events = []
        self.event_counter = 0
        self.show_plot_var = tk.BooleanVar(value=True)
        self.mode_var = tk.StringVar(value="message")
        self.pending_message = None
        
        # Process states tracking
        self.process_states = {}  # {pid: {"messages_to": [...], "messages_from": [...], "snapshots": [...]}}

        self.time_scale = 12  # pixels per time unit
        self.top_margin = 60
        self.left_margin = 60
        self.max_time = 40
        self.delay = 5

        self._build_ui()
        self._draw_canvas()

    def _build_ui(self):
        # Main scrollable container
        main_canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the scrollable interface
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel to canvas
        main_canvas.bind("<MouseWheel>", lambda e: self._on_main_mousewheel(e, main_canvas))
        main_canvas.bind("<Button-4>", lambda e: self._on_main_mousewheel(e, main_canvas))
        main_canvas.bind("<Button-5>", lambda e: self._on_main_mousewheel(e, main_canvas))
        
        # Also bind to scrollable_frame for better event capture
        scrollable_frame.bind("<MouseWheel>", lambda e: self._on_main_mousewheel(e, main_canvas))
        scrollable_frame.bind("<Button-4>", lambda e: self._on_main_mousewheel(e, main_canvas))
        scrollable_frame.bind("<Button-5>", lambda e: self._on_main_mousewheel(e, main_canvas))
        
        container = ttk.Frame(scrollable_frame, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Top controls
        top = ttk.Frame(container)
        top.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top, text="Processus (ex: P1,P2,P3)").pack(side=tk.LEFT)
        self.process_ids_entry = ttk.Entry(top, width=30)
        self.process_ids_entry.insert(0, "P1,P2,P3")
        self.process_ids_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(top, text="Temps max").pack(side=tk.LEFT, padx=(10, 0))
        self.max_time_entry = ttk.Entry(top, width=6)
        self.max_time_entry.insert(0, str(self.max_time))
        self.max_time_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="Mettre à jour", command=self._update_diagram).pack(side=tk.LEFT, padx=5)

        # Middle layout with resizable panes
        middle = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        middle.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANE - Canvas with scrollbars
        left = ttk.Frame(middle)
        middle.add(left, weight=3)

        canvas_frame = ttk.LabelFrame(left, text="Insertion graphique")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame for canvas + scrollbars
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas
        self.canvas = tk.Canvas(canvas_container, bg="white", xscrollcommand=h_scrollbar.set, 
                               yscrollcommand=v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbars to scroll canvas
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)

        self.canvas.bind("<Button-1>", self._on_canvas_click)
        # Allow mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down

        # RIGHT PANE - Vertical stack of control panels
        right = ttk.Frame(middle)
        middle.add(right, weight=1)

        # Mode + content
        mode_frame = ttk.LabelFrame(right, text="Mode")
        mode_frame.pack(fill=tk.X, padx=0, pady=5)

        ttk.Radiobutton(mode_frame, text="Message", value="message", variable=self.mode_var).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="Snapshot", value="snapshot", variable=self.mode_var).pack(anchor=tk.W, padx=5, pady=2)

        content_frame = ttk.LabelFrame(right, text="Contenu du message")
        content_frame.pack(fill=tk.X, padx=0, pady=5)
        self.msg_content_entry = ttk.Entry(content_frame)
        self.msg_content_entry.insert(0, "Msg")
        self.msg_content_entry.pack(fill=tk.X, padx=5, pady=5)
        
        # Message status label
        self.msg_status = ttk.Label(content_frame, text="Cliquez sur source puis destination", 
                                     font=("Helvetica", 8, "italic"), foreground="gray")
        self.msg_status.pack(padx=5, pady=2)

        # Events list with resizable inner panes
        right_paned = ttk.PanedWindow(right, orient=tk.VERTICAL)
        right_paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        events_frame = ttk.LabelFrame(right_paned, text="Événements")
        right_paned.add(events_frame, weight=2)

        columns = ("time", "type", "src", "dst", "content")
        self.events_tree = ttk.Treeview(events_frame, columns=columns, show="headings")
        self.events_tree.heading("time", text="Temps")
        self.events_tree.heading("type", text="Type")
        self.events_tree.heading("src", text="Src")
        self.events_tree.heading("dst", text="Dst")
        self.events_tree.heading("content", text="Contenu")
        # Use stretch=True for responsive columns
        for col in columns:
            self.events_tree.column(col, stretch=True, anchor=tk.CENTER if col != "content" else tk.W)
        self.events_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        buttons_frame = ttk.Frame(events_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Supprimer", command=self._remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Vider", command=self._clear_events).pack(side=tk.LEFT, padx=2)

        # Events log (real-time display)
        log_frame = ttk.LabelFrame(right_paned, text="Journal des événements")
        right_paned.add(log_frame, weight=1)
        self.events_log = tk.Text(log_frame, wrap=tk.WORD, font=("Helvetica", 8))
        self.events_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)

        # Process states (real-time display)
        states_frame = ttk.LabelFrame(right_paned, text="États des Processus")
        right_paned.add(states_frame, weight=1)
        self.states_text = tk.Text(states_frame, wrap=tk.WORD, font=("Helvetica", 7))
        self.states_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)

        # Run section
        run_frame = ttk.Frame(container)
        run_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Checkbutton(run_frame, text="Afficher le graphique", variable=self.show_plot_var).pack(side=tk.LEFT)
        ttk.Button(run_frame, text="Lancer la simulation", command=self._run_simulation).pack(side=tk.RIGHT)

        # Output
        output_frame = ttk.LabelFrame(container, text="Résultats")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)
        self.output_text = tk.Text(output_frame, height=6, wrap=tk.WORD, font=("Helvetica", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)        
        # Bind scroll wheel to all widgets recursively
        self._bind_mousewheel_recursive(container, main_canvas)

    def _bind_mousewheel_recursive(self, widget, main_canvas):
        """Recursively bind mousewheel events to widget and all children"""
        # Bind to current widget
        widget.bind("<MouseWheel>", lambda e: self._on_main_mousewheel(e, main_canvas), add=True)
        widget.bind("<Button-4>", lambda e: self._on_main_mousewheel(e, main_canvas), add=True)
        widget.bind("<Button-5>", lambda e: self._on_main_mousewheel(e, main_canvas), add=True)
        
        # Recursively bind to all children
        try:
            for child in widget.winfo_children():
                self._bind_mousewheel_recursive(child, main_canvas)
        except:
            pass
    def _parse_process_ids(self):
        raw = self.process_ids_entry.get().strip()
        if not raw:
            raise ValueError("Veuillez saisir au moins un ID de processus.")
        parts = [p.strip() for p in raw.replace(";", ",").replace(" ", ",").split(",")]
        pids = [p for p in parts if p]
        if len(pids) < 2:
            raise ValueError("Au moins 2 processus sont nécessaires.")
        seen = set()
        unique = []
        for pid in pids:
            if pid not in seen:
                unique.append(pid)
                seen.add(pid)
        return unique

    def _update_diagram(self):
        try:
            self.max_time = float(self.max_time_entry.get())
            if self.max_time <= 0:
                raise ValueError
            self._draw_canvas()
        except ValueError:
            messagebox.showerror("Erreur", "Temps max invalide.")

    def _draw_canvas(self):
        self.canvas.delete("all")
        pids = self._parse_process_ids()
        self.y_map = {}

        width = max(int(self.left_margin + self.max_time * self.time_scale + 40), 700)
        height = max(self.canvas.winfo_height(), 400)
        self.canvas.config(scrollregion=(0, 0, width, height))

        # Grid/time labels (vertical grid lines at bottom)
        for t in range(0, int(self.max_time) + 1, 5):
            x = self.left_margin + t * self.time_scale
            self.canvas.create_line(x, self.top_margin - 10, x, height - 20, fill="#efefef")
            self.canvas.create_text(x, height - 5, text=str(t), anchor=tk.N, fill="#999")

        # Lifelines (horizontal lines for each process)
        spacing = (height - self.top_margin - 40) / max(1, len(pids) - 1) if len(pids) > 1 else height - self.top_margin - 40
        for idx, pid in enumerate(pids):
            y = self.top_margin + idx * spacing
            self.y_map[pid] = y
            self.canvas.create_text(15, y, text=pid, font=("Helvetica", 11, "bold"), anchor=tk.E)
            self.canvas.create_line(self.left_margin, y, self.left_margin + self.max_time * self.time_scale, y,
                                    fill="black")

        # Redraw existing events
        for event in self.events:
            if event["type"] == "MESSAGE":
                self._draw_message(event)
            elif event["type"] == "SNAPSHOT":
                self._draw_snapshot(event)

    def _nearest_process(self, x):
        pid = min(self.y_map.keys(), key=lambda p: abs(self.y_map[p] - x))
        return pid

    def _time_from_y(self, y):
        t = (y - self.left_margin) / self.time_scale
        if t < 0:
            t = 0
        return round(t, 1)

    def _on_canvas_click(self, event):
        try:
            pids = self._parse_process_ids()
            if not pids:
                return
            pid = self._nearest_process(event.y)
            time_val = self._time_from_y(event.x)

            if self.mode_var.get() == "snapshot":
                self._add_event({
                    "time": time_val,
                    "type": "SNAPSHOT",
                    "pid": pid,
                    "src": pid,
                    "dst": "-",
                    "content": "-",
                })
                self._draw_snapshot(self.events[-1])
                return

            # Message mode
            if self.pending_message is None:
                self.pending_message = {"src": pid, "time": time_val}
                self.msg_status.config(text=f"Source: {pid} @ t={time_val:.1f} → Cliquez destination", foreground="orange")
                self.canvas.delete("pending")
                x = self.left_margin + time_val * self.time_scale
                self.canvas.create_oval(x - 4, self.y_map[pid] - 4, x + 4, self.y_map[pid] + 4,
                                        fill="orange", outline="red", width=2, tags="pending")
                # Draw a vertical line to help locate the source
                self.canvas.create_line(x, self.top_margin - 10, x, self.canvas.winfo_height() - 20, 
                                       fill="orange", dash=(4, 4), tags="pending")
            else:
                src = self.pending_message["src"]
                time_val_src = self.pending_message["time"]
                dst = pid
                content = self.msg_content_entry.get().strip() or "Msg"
                self.pending_message = None
                self.canvas.delete("pending")
                self.msg_status.config(text="Cliquez sur source puis destination", foreground="gray")

                if src == dst:
                    messagebox.showerror("Erreur", "Source et destination doivent être différentes.")
                    return

                self._add_event({
                    "time": time_val_src,
                    "type": "MESSAGE",
                    "src": src,
                    "dst": dst,
                    "content": content,
                })
                self._draw_message(self.events[-1])

        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling on diagram canvas (macOS trackpad + wheel mice)"""
        # Determine scroll direction - macOS trackpad uses event.delta
        try:
            delta = event.delta if hasattr(event, 'delta') else 0
            num = event.num if hasattr(event, 'num') else 0
            
            if delta != 0:
                direction = 1 if delta < 0 else -1
            elif num == 5:
                direction = 1
            elif num == 4:
                direction = -1
            else:
                return
            
            # Scroll canvas
            if event.state & 0x1:  # Shift key - horizontal scroll
                self.canvas.xview_scroll(direction * 3, tk.UNITS)
            else:  # Vertical scroll
                self.canvas.yview_scroll(direction * 3, tk.UNITS)
        except:
            pass
        return "break"
    
    def _on_main_mousewheel(self, event, canvas):
        """Handle mouse wheel scrolling on main interface canvas (macOS trackpad + wheel mice)"""
        # Determine scroll direction - macOS trackpad uses event.delta
        try:
            delta = event.delta if hasattr(event, 'delta') else 0
            num = event.num if hasattr(event, 'num') else 0
            
            if delta != 0:
                direction = 1 if delta < 0 else -1
            elif num == 5:
                direction = 1
            elif num == 4:
                direction = -1
            else:
                return
            
            # Scroll main canvas
            canvas.yview_scroll(direction * 3, tk.UNITS)
        except:
            pass
        return "break"

    def _draw_message(self, event):
        src = event["src"]
        dst = event["dst"]
        t_send = event["time"]
        t_rcv = t_send + self.delay

        x1 = self.left_margin + t_send * self.time_scale
        x2 = self.left_margin + t_rcv * self.time_scale
        y1 = self.y_map[src]
        y2 = self.y_map[dst]

        self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill="#1f77b4", width=2)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        self.canvas.create_text(mid_x, mid_y - 8, text=event["content"], fill="#1f77b4", font=("Helvetica", 9))

    def _draw_snapshot(self, event):
        pid = event["pid"]
        t = event["time"]
        x = self.left_margin + t * self.time_scale
        y = self.y_map[pid]
        self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="red", outline="")
        self.canvas.create_text(x, y - 12, text=f"S_{pid}", fill="red", anchor=tk.S)

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
        # Log the event and update states
        self._log_event(event)
        self._update_process_states()

    def _remove_selected(self):
        selection = self.events_tree.selection()
        if not selection:
            return
        for item in selection:
            self.events_tree.delete(item)
            self.events = [e for e in self.events if e.get("id") != item]
        self._redraw_log()
        self._update_process_states()
        self._draw_canvas()

    def _clear_events(self):
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)
        self.events = []
        self.process_states = {}
        self._redraw_log()
        self._update_process_states()
        self._draw_canvas()

    def _log_event(self, event):
        """Add event to log display."""
        log_text = self.events_log.get("1.0", tk.END)
        if log_text.strip():
            self.events_log.insert(tk.END, "\n")
        
        if event["type"] == "MESSAGE":
            msg = f"T={event['time']:.1f}: {event['src']} → {event['dst']} ({event['content']})"
        else:  # SNAPSHOT
            msg = f"T={event['time']:.1f}: SNAPSHOT {event['pid']}"
        
        self.events_log.insert(tk.END, msg)
        self.events_log.see(tk.END)

    def _redraw_log(self):
        """Redraw entire log from events."""
        self.events_log.delete("1.0", tk.END)
        for i, event in enumerate(sorted(self.events, key=lambda e: e["time"])):
            if i > 0:
                self.events_log.insert(tk.END, "\n")
            
            if event["type"] == "MESSAGE":
                msg = f"T={event['time']:.1f}: {event['src']} → {event['dst']} ({event['content']})"
            else:  # SNAPSHOT
                msg = f"T={event['time']:.1f}: SNAPSHOT {event['pid']}"
            
            self.events_log.insert(tk.END, msg)

    def _update_process_states(self):
        """Update and display process states based on current events."""
        pids = self._parse_process_ids()
        
        # Initialize states for all processes
        for pid in pids:
            if pid not in self.process_states:
                self.process_states[pid] = {"messages_to": [], "messages_from": [], "snapshots": []}
        
        # Clear existing data
        for pid in pids:
            self.process_states[pid] = {"messages_to": [], "messages_from": [], "snapshots": []}
        
        # Populate from events
        for event in sorted(self.events, key=lambda e: e["time"]):
            if event["type"] == "MESSAGE":
                src = event["src"]
                dst = event["dst"]
                msg = f"→ {dst} @ t={event['time']:.1f} ({event['content']})"
                self.process_states[src]["messages_to"].append(msg)
                
                msg_in = f"← {src} @ t={event['time'] + self.delay:.1f} ({event['content']})"
                self.process_states[dst]["messages_from"].append(msg_in)
            
            elif event["type"] == "SNAPSHOT":
                pid = event["pid"]
                snap = f"Snapshot @ t={event['time']:.1f}"
                self.process_states[pid]["snapshots"].append(snap)
        
        # Display in states text widget
        self.states_text.delete("1.0", tk.END)
        for pid in pids:
            self.states_text.insert(tk.END, f"\n{'='*35}\n")
            self.states_text.insert(tk.END, f"PROCESSUS {pid}\n")
            self.states_text.insert(tk.END, f"{'='*35}\n")
            
            state = self.process_states[pid]
            
            self.states_text.insert(tk.END, f"Snapshots:\n")
            if state["snapshots"]:
                for snap in state["snapshots"]:
                    self.states_text.insert(tk.END, f"  • {snap}\n")
            else:
                self.states_text.insert(tk.END, f"  (aucun)\n")
            
            self.states_text.insert(tk.END, f"\nMessages envoyés:\n")
            if state["messages_to"]:
                for msg in state["messages_to"]:
                    self.states_text.insert(tk.END, f"  • {msg}\n")
            else:
                self.states_text.insert(tk.END, f"  (aucun)\n")
            
            self.states_text.insert(tk.END, f"\nMessages reçus:\n")
            if state["messages_from"]:
                for msg in state["messages_from"]:
                    self.states_text.insert(tk.END, f"  • {msg}\n")
            else:
                self.states_text.insert(tk.END, f"  (aucun)\n")

    def _run_simulation(self):
        try:
            pids = self._parse_process_ids()
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
    app = GraphicalSimulationUI()
    app.mainloop()
