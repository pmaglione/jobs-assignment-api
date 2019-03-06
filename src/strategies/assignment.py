import random

class AssignStrategy():
    def get_assignment(self, worker_id, items):
        pass

class RandomStrategy(AssignStrategy):
    def get_assignment(self, worker_id, items):
        assignable_items = [item for item in items if str(worker_id) not in item['votes'].keys()]
        if len(assignable_items) > 0:
            return random.choice(assignable_items)
        else:
            return {}