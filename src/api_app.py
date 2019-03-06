# app.py - a minimal flask api using flask_restful
from flask import Flask, request, jsonify
from flask_restplus import Api, Resource, fields, Namespace
from flask_pymongo import PyMongo
import pandas as pd
import os
#import helpers.algorithms_utils as alg_utils
from .smart_stop import decision_function_bayes
from .model.model import PlatformCrowdJob, FigureEight
from .db.layer import CrowdJob, Item
from .assign_strategies.strategies import RandomStrategy


app = Flask(__name__)

db_path = os.getenv('DB_PATH') or 'localhost'
db_port = os.getenv('DB_PORT') or 27017
db_name = os.getenv('DB_NAME') or 'api'

app.config["MONGO_URI"] = f"mongodb://{db_path}:{db_port}/{db_name}"
mongo = PyMongo(app)

api = Api(app, version='1.0', title='CrowdAI API', description='The CrowdAI API',
          default ='crowdai', default_label='methods')



class Jobs(Resource):
    @api.doc(params={
        'api_key': 'api_key',
        'file:items_file': 'file with items',
        'title': 'Job title',
        'instructions': 'Job instructions',
        'crowd_cost': 'Payment for each crowd vote',
        'classification_fn': 'Aggregation Function(MV, EM,...)',
        'threshold': 'Classification Threshold',
        'initial_votes_amount': 'Amount of votes per item to collect after running adaptive'
    })
    def post(self):
        # platform = request.form.get('platform') TO-DO
        api_key = request.form.get('api_key')
        items_file = request.files.get('items_file')
        title = request.form.get('title')
        instructions = request.form.get('instructions')
        title_field = request.form.get('title_field')
        content_field = request.form.get('content_field')
        cost_ratio = request.form.get('crowd_cost')
        classification_fn = request.form.get('classification_fn')
        classification_threshold = request.form.get('threshold')
        initial_votes_amount = request.form.get('initial_votes_amount')


        #items_per_worker = 1
        #Create job, set job attributes
        #voting_strategy = PlatformFactory(platform, api_key) # to do factory
        #crowd_job = PlatformCrowdJob(api_key, FigureEight(api_key), classification_fn, cost_ratio, items_per_worker, title, instructions)
        # crowd_job.create() #creates 2 platform jobs



        job_id = 1
        crowd_job = CrowdJob(mongo, job_id)
        crowd_job.create_job(job_id, classification_threshold, cost_ratio, classification_fn, initial_votes_amount, title_field, content_field)

        datafile = pd.read_csv(items_file)
        file_headers = list(datafile)
        file_values = datafile.values

        crowd_job.create_items(file_headers, file_values)

        # items created and posted
        # crowd_job.create_items(crowd_job.multiple_job_id, file_headers, file_values)

        # first vote for each item
        # crowd_job.collect_votes_results(crowd_job.multiple_job_id)

        '''
        items_predicted_classified = [item.internal_id for item in crowd_job.items]
        must_get_more_votes = True

        while (must_get_more_votes):
            total_votes_aux = {}

            #repost items -> get 1 more vote
            for internal_id in items_predicted_classified:
                crowd_job.republish_item(internal_id)

            #await and get results
            crowd_job.wait_for_results(items_predicted_classified)

            total_votes = get_formatted_items_votes(crowd_job)

            results = decision_function_bayes(len(total_votes),
                                              total_votes_aux,
                                              classification_threshold,
                                              cost_ratio,
                                              classification_fn)

            # Stop when there are no more items that can be classified
            items_predicted_classified = alg_utils.get_items_predicted_classified(results)
            must_get_more_votes = len(items_predicted_classified) > 0
        # end while

        items_classification = alg_utils.classify_items(total_votes, gt, majority_voting, .5)

        return items_classification, total_votes
        '''

        response = {"message": "job finished"}
        return jsonify(response)

class Tasks(Resource):
    @api.doc(params={
        'job_id': 'Job ID',
        'worker_id': 'Worker Uuid'
    })
    def get(self, job_id, worker_id):
        crowd_job = CrowdJob(mongo, job_id)
        free_items = crowd_job.get_items_by_state(Item.STATE_FREE)
        item = RandomStrategy().get_assignment(worker_id, free_items) #different strategies can be set
        response = {'items': []}
        if bool(item):
            crowd_job.assign_item(item['internal_id']) #change state to assigned
            json_item = {
                            "id": item['internal_id'],
                            "title": Item().get_title(crowd_job.job['title_field'], item['attributes_names'], item['values']),
                            "content": Item().get_content(crowd_job.job['content_field'], item['attributes_names'], item['values'])
                         }
            response['items'].append(json_item)

        return jsonify(response)

class Votes(Resource):
    @api.doc(params={
        'job_id': 'Job ID',
        'worker_id': 'Worker Uuid',
        'item_id': 'Item ID',
        'vote': 'Vote'
    })
    def post(self, job_id, worker_id, item_id, vote):
        crowd_job = CrowdJob(mongo, job_id)
        item = crowd_job.get_item_by_id(item_id)
        item['votes'][str(worker_id)] = vote
        crowd_job.update_item_votes(item_id, item['votes'])
        crowd_job.free_item(item_id)  # change state to assigned

        #run stopping rule
        if crowd_job.is_initial_reached():
            items = crowd_job.get_items()
            total_votes = self.get_formatted_items_votes(items)
            items_predicted_classified = [item.internal_id for item in crowd_job.items]

            results = decision_function_bayes(len(total_votes),
                                              total_votes,
                                              crowd_job.get_classification_threshold(),
                                              crowd_job.cost_ratio(),
                                              crowd_job.classification_fn())

        response = {"message": "vote submitted"}
        return jsonify(response)

    def get_formatted_items_votes(self, items):
        # reformat to {item_id: {worker_id:[vote]}}
        total_votes = {}
        for item in items:
            total_votes[item['internal_id']] = {}
            for worker_id, vote in item['votes'].items():
                total_votes[item['internal_id']][worker_id] = [vote]


api.add_resource(Jobs, '/jobs', endpoint='jobs')
api.add_resource(Tasks, '/tasks/<int:job_id>/<string:worker_id>', endpoint='tasks')
api.add_resource(Votes, '/votes/<int:job_id>/<string:worker_id>/<int:item_id>/<int:vote>', endpoint='votes')

if __name__ == '__main__':
    app.run(debug=False)