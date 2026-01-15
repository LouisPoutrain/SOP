from collections import defaultdict
from message import Message, MessageType # Assurez-vous que MessageType est bien importé

class Process:
    def __init__(self, pid, simulator):
        self.pid = pid
        self.sim = simulator
        
        # --- État Local (Application) ---
        self.local_state = 0   
        self.outgoing_neighbors = [] 
        self.incoming_neighbors = [] 
        
        # --- Variables pour le Snapshot (Chandy-Lamport) ---
        self.has_recorded_state = False          
        self.snapshot_local_state = None         
        self.channel_states = defaultdict(list)  
        self.recording_channels = {}             

    def setup_topology(self, incoming, outgoing):
        """Configure les voisins."""
        self.incoming_neighbors = incoming
        self.outgoing_neighbors = outgoing
        # Initialisation : on n'enregistre aucun canal au départ
        for p in incoming:
            self.recording_channels[p] = False

    def send_message(self, target_pid, content):
        """Envoie un message d'application."""
        msg = Message(self.pid, content, MessageType.APP)
        target_proc = self.sim.get_process(target_pid)
        
        # Définition du délai
        delay = 5 
        
        # 1. Logging pour le graphique (Bonus)
        self.sim.log_message(self.pid, target_pid, delay, msg)
        
        # 2. Programmation de l'événement
        self.sim.schedule(delay, target_proc, target_proc.receive_message, msg)
        
        self.local_state += 1 

    def receive_message(self, message):
        """Dispatche le message selon son type."""
        if message.msg_type == MessageType.MARKER:
            self.handle_marker(message)
        else:
            self.handle_app_message(message)

    def handle_app_message(self, message):
        """Traitement d'un message normal."""
        sender = message.sender_pid
        
        # --- Règle Snapshot : Enregistrement des messages en transit ---
        if self.recording_channels.get(sender, False):
            self.channel_states[sender].append(message.content)
            
        # --- Logique Applicative ---
        self.local_state += 1
        print(f"[{self.pid}] Reçu '{message.content}' de {sender}. Nouvel état: {self.local_state}")

    def initiate_snapshot(self):
        """Appelé par l'initiateur (ex: P3) pour lancer l'algo."""
        print(f"*** {self.pid} INITIE LE SNAPSHOT ***")
        
        # 1. Enregistrer son état local
        self.snapshot_local_state = self.local_state
        self.has_recorded_state = True
        
        # Logging pour le graphique (Bonus)
        self.sim.log_snapshot(self.pid)
        
        # 2. Commencer à enregistrer sur TOUS les canaux entrants
        for neighbor in self.incoming_neighbors:
            self.recording_channels[neighbor] = True
            
        # 3. Envoyer un Marker sur tous les canaux sortants
        self.send_markers()

    def handle_marker(self, marker):
        """Cœur de l'algorithme Chandy-Lamport."""
        sender = marker.sender_pid
        
        # Logging console optionnel
        # print(f"[{self.pid}] Reçu MARKER de {sender}")

        if not self.has_recorded_state:
            # --- CAS 1 : Premier marqueur reçu ---
            
            # 1. Enregistrer l'état local
            self.snapshot_local_state = self.local_state
            self.has_recorded_state = True
            
            # Logging pour le graphique (Bonus)
            self.sim.log_snapshot(self.pid)
            
            # 2. Le canal d'où vient le marqueur est considéré VIDE
            self.channel_states[sender] = [] 
            self.recording_channels[sender] = False 
            
            # 3. Commencer à enregistrer sur les AUTRES canaux entrants
            for neighbor in self.incoming_neighbors:
                if neighbor != sender:
                    self.recording_channels[neighbor] = True
            
            # 4. Propager le marqueur
            self.send_markers()
            
        else:
            # --- CAS 2 : Marqueur suivant ---
            # 1. Arrêter d'enregistrer sur ce canal
            self.recording_channels[sender] = False

    def send_markers(self):
        """Envoie un Marker à tous les voisins sortants."""
        for neighbor_pid in self.outgoing_neighbors:
            target = self.sim.get_process(neighbor_pid)
            marker = Message(self.pid, None, MessageType.MARKER)
            
            # --- CORRECTION : Définir delay AVANT l'usage ---
            delay = 5
            
            # 1. Logging pour le graphique (Bonus)
            self.sim.log_message(self.pid, neighbor_pid, delay, marker)
            
            # 2. Programmation de l'événement
            self.sim.schedule(delay, target, target.receive_message, marker)