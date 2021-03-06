class Job:
    STATE_CREATED = "CREATED"
    STATE_FINISHED = "FINISHED"

    def __init__(self, job_id, classification_threshold, cost_ratio, classification_fn, initial_votes_amount, title_field, content_field):
        self.job_id = job_id
        self.state = self.STATE_CREATED
        self.classification_threshold = classification_threshold
        self.cost_ratio = cost_ratio
        self.classification_fn = classification_fn
        self.initial_votes_num = initial_votes_amount
        self.title_field = title_field
        self.content_field = content_field


class Item:
    STATE_FREE = "FREE"
    STATE_ASSIGNED = "ASSIGNED"
    STATE_WAITING = "WAITING"
    STATE_FINISHED = "FINISHED"

    def __init__(self, job_id = None, item_id = None, attributes_names = None, item_values = None):
        self.job_id = job_id
        self.internal_id = item_id
        self.attributes_names = attributes_names
        self.values = item_values
        self.votes = {} #votes = {worker_id: vote,...}
        self.state = self.STATE_FREE

    @staticmethod
    def get_title(title_field, attributes_names, values):
        title_index = attributes_names.index(title_field)
        return values[title_index]

    @staticmethod
    def get_content(content_field, attributes_names, values):
        content_index = attributes_names.index(content_field)
        return values[content_index]

    @staticmethod
    def is_valid_vote(item, worker_id):
        return item['state'] == Item.STATE_ASSIGNED and str(worker_id) not in item['votes'].keys()


class DBCrowdJob:
    def __init__(self, mongo, job_id):
        self.mongo = mongo
        self.job_id = job_id
        self.job = self.get_job() #load it if exists, if not is empty

    def job_id(self):
        return self.job.job_id

    def classification_threshold(self):
        return self.job.classification_threshold

    def cost_ratio(self):
        return self.job.cost_ratio

    def classification_fn(self):
        return self.job.classification_fn

    def create_job(self, job_id, classification_threshold, cost_ratio, classification_fn,
                   initial_votes_amount, title_field, content_field):
        job = Job(job_id, classification_threshold, cost_ratio, classification_fn,
                  initial_votes_amount, title_field, content_field)
        self.mongo.db.jobs.insert_one(job.__dict__)

    def create_items(self, attributes_names, items_values):
        items = []
        for item_id, item_values in enumerate(items_values):
            attrs = [attr_name for attr_name in attributes_names]
            vals = [val for val in item_values]
            item = Item(self.job_id, item_id, attrs, vals)
            items.append(item.__dict__)

        self.mongo.db.items.insert_many(items)

        return items

    def get_item_by_id(self, internal_id):
        return self.mongo.db.items.find_one({'job_id': self.job_id, "internal_id": internal_id})

    def get_items(self):
        return list(self.mongo.db.items.find({'job_id': self.job_id}))

    def get_items_by_state(self, state):
        return list(self.mongo.db.items.find({"job_id": self.job_id, "state": state}))

    def get_active_items(self):
        return list(self.mongo.db.items.find({"$and": [{"job_id": self.job_id},
                                                       {"state": {"$ne": Item.STATE_FINISHED}}]}))

    def update_item_votes(self, internal_id, votes):
        self.mongo.db.items.update_one({'job_id': self.job_id, 'internal_id': internal_id},
                                       {"$set": {'votes': votes}}, upsert=False)

    def free_item(self, internal_id):
        self.mongo.db.items.update_one({'job_id': self.job_id, 'internal_id': internal_id},
                                       {"$set": {'state': Item.STATE_FREE}}, upsert=False)

    def wait_item(self, internal_id):
        self.mongo.db.items.update_one({'job_id': self.job_id, 'internal_id': internal_id},
                                       {"$set": {'state': Item.STATE_WAITING}}, upsert=False)

    def finish_item(self, internal_id):
        self.mongo.db.items.update_one({'job_id': self.job_id, 'internal_id': internal_id},
                                       {"$set": {'state': Item.STATE_FINISHED}}, upsert=False)

    def assign_item(self, internal_id):
        self.mongo.db.items.update_one({'job_id': self.job_id, 'internal_id': internal_id},
                                       {"$set": {'state': Item.STATE_ASSIGNED}}, upsert=False)

    def finish_item(self, internal_id):
        self.mongo.db.items.update_one({'job_id': self.job_id, 'internal_id': internal_id},
                                       {"$set": {'state': Item.STATE_FINISHED}}, upsert=False)

    def get_job(self):
        return self.mongo.db.jobs.find_one({'job_id': self.job_id})

    def is_in_initial_rounds(self):
        items = self.get_active_items()
        return any(len(item['votes']) < self.get_job_initial_votes_num() for item in items)

    def has_waiting_items_equal_votes_num(self):
        items = self.get_active_items()
        max_votes_num = max([len(item['votes']) for item in items])
        return all(len(item['votes']) == max_votes_num for item in items)

    def get_job_initial_votes_num(self):
        return int(self.job['initial_votes_num'])

    def get_job_classification_threshold(self):
        return float(self.job['classification_threshold'])

    def get_job_cost_ratio(self):
        return float(self.job['cost_ratio'])

    def get_job_classification_fn(self):
        return self.job['classification_fn']
