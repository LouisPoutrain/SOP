import heapq
from events import Event
from message import MessageType

class Simulator:
    def __init__(self):
        self.clock = 0.0
        self.events = []
        self.processes = {}
        
        # --- NOUVEAU : Historique pour la visualisation ---
        # Liste de tuples : (src_pid, dst_pid, t_send, t_rcv, content, msg_type)
        self.message_log = [] 
        # Dictionnaire : {pid: t_snapshot}
        self.snapshot_log = {} 

    def register_process(self, process):
        self.processes[process.pid] = process

    def get_process(self, pid):
        return self.processes.get(pid)

    def schedule(self, delay, receiver, action, params=None):
        trigger_time = self.clock + delay
        event = Event(trigger_time, receiver, action, params)
        heapq.heappush(self.events, event)

    # --- NOUVEAU : Méthodes de logging ---
    def log_message(self, src, dst, delay, message):
        """Enregistre un envoi de message pour le dessin."""
        t_send = self.clock
        t_rcv = t_send + delay
        # On stocke tout ce dont le Plotter a besoin
        entry = {
            "src": src, 
            "dst": dst, 
            "t_send": t_send, 
            "t_rcv": t_rcv, 
            "content": message.content, 
            "type": message.msg_type
        }
        self.message_log.append(entry)

    def log_snapshot(self, pid):
        """Enregistre le moment où un processus fige son état."""
        if pid not in self.snapshot_log:
            self.snapshot_log[pid] = self.clock

    def run(self):
        print(f"--- Démarrage de la simulation ---")
        while self.events:
            current_event = heapq.heappop(self.events)
            self.clock = current_event.timestamp
            if current_event.params is not None:
                current_event.action(current_event.params)
            else:
                current_event.action()
        print(f"--- Fin de la simulation à t={self.clock} ---")

