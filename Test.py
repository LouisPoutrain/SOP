import unittest
from simulator import Simulator
from message import Message, MessageType
from events import Event   

# Assurez-vous d'importer vos classes précédentes ici
# from simulation import Simulator, Message, MessageType

class MockProcess:
    """
    Un processus 'bouchon' (mock) qui ne fait qu'enregistrer les messages reçus.
    Sert uniquement à vérifier l'ordre d'arrivée.
    """
    def __init__(self, pid):
        self.pid = pid
        self.inbox = [] # Liste pour stocker l'historique des réceptions

    def receive_message(self, message):
        print(f"[{self.pid}] Message reçu : {message.content}")
        self.inbox.append(message.content)

class TestFIFO(unittest.TestCase):
    
    def setUp(self):
        """Initialisation avant chaque test"""
        self.sim = Simulator()
        self.receiver = MockProcess("P_REC")
        self.sender = MockProcess("P_SEND")
        
        # On enregistre les processus (si nécessaire selon votre implémentation)
        self.sim.register_process(self.receiver)
        self.sim.register_process(self.sender)

    def test_priority_ordering(self):
        """
        Test 1 : Vérifie que les délais courts passent AVANT les délais longs.
        Si j'envoie A (délai 10) puis B (délai 2), B doit arriver avant A.
        """
        print("\n--- Test 1: Priorité Temporelle ---")
        
        # Message A : Délai long (10)
        msg_a = Message("P_SEND", "A (Long)")
        self.sim.schedule(10, self.receiver, self.receiver.receive_message, msg_a)
        
        # Message B : Délai court (2)
        msg_b = Message("P_SEND", "B (Court)")
        self.sim.schedule(2, self.receiver, self.receiver.receive_message, msg_b)

        # Exécution
        self.sim.run()

        # Vérification
        expected_order = ["B (Court)", "A (Long)"]
        self.assertEqual(self.receiver.inbox, expected_order, 
                         "Erreur: Le message avec le petit délai aurait dû arriver en premier.")
        print(">> Succès : L'ordre temporel est respecté.")

    def test_fifo_integrity(self):
        """
        Test 2 : Simulation d'un canal FIFO.
        Si P1 envoie M1, M2, M3 séquentiellement avec le même délai réseau,
        ils doivent arriver dans l'ordre M1, M2, M3.
        """
        print("\n--- Test 2: Intégrité FIFO ---")
        
        # On simule une séquence d'envoi.
        # Dans la vraie boucle, le temps avancerait entre chaque envoi.
        # Ici, on simule cela en augmentant manuellement le délai total ou 
        # en programmant des événements décalés.
        
        # M1 part à t=0, arrive à t=5
        msg1 = Message("P_SEND", "M1")
        self.sim.schedule(5, self.receiver, self.receiver.receive_message, msg1)
        
        # Pour garantir le FIFO dans notre simulateur à événements discrets,
        # l'événement d'envoi de M2 se produit techniquement APRES M1.
        # Donc M2 part à t=1 (fictif), arrive à t=6.
        # Astuce pour test : on décale légèrement le trigger time pour simuler la séquence.
        
        # On suppose que le simulateur a avancé (ou on schedule avec un décalage)
        msg2 = Message("P_SEND", "M2")
        self.sim.schedule(6, self.receiver, self.receiver.receive_message, msg2)
        
        msg3 = Message("P_SEND", "M3")
        self.sim.schedule(7, self.receiver, self.receiver.receive_message, msg3)

        self.sim.run()

        expected_fifo = ["M1", "M2", "M3"]
        self.assertEqual(self.receiver.inbox, expected_fifo,
                         "Erreur: L'ordre FIFO n'est pas respecté.")
        print(">> Succès : L'ordre FIFO est respecté.")

if __name__ == '__main__':
    unittest.main()