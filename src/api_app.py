from flask import Flask, request, jsonify
from flask_restplus import Api, Resource, fields
from flask_pymongo import PyMongo
from flask_cors import CORS
import pandas as pd
import os
import json
from src.connectors.db import DBCrowdJob, Item
from src.connectors.platform import PlatformCrowdJob, FigureEight
from .strategies.assignment import RandomStrategy
from .strategies.stop import StopManagement


app = Flask(__name__)
CORS(app)

db_path = os.getenv('DB_PATH') or 'localhost'
db_port = os.getenv('DB_PORT') or 27017
db_name = os.getenv('DB_NAME') or 'api'

api_key = os.getenv('CROWD_API_KEY') or 'api_key'

app.config["MONGO_URI"] = f"mongodb://{db_path}:{db_port}/{db_name}"
mongo = PyMongo(app)

api = Api(app, version='1.0', title='CrowdAI API', description='The CrowdAI API',
          default ='crowdai', default_label='methods')



class Jobs(Resource):
    @api.doc(params={
        'file:items_file': 'file with items',
        'title': 'Job title',
        'instructions': 'Job instructions',
        'crowd_cost': 'Payment for each crowd vote',
        'classification_fn': 'Aggregation Function(MV, EM,...)',
        'threshold': 'Classification Threshold',
        'initial_votes_amount': 'Amount of votes per item to collect after running adaptive'
    })
    def post(self):
        # platform = request.form.get('platform') TO-DO platform configuration
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
        #crowd_job = PlatformCrowdJob(FigureEight(api_key))
        # crowd_job.create(cost_ratio, items_per_worker, title, instructions) #creates 2 platform jobs


        job_id = 1
        crowd_job = DBCrowdJob(mongo, job_id)
        crowd_job.create_job(job_id, classification_threshold, cost_ratio,
                             classification_fn, initial_votes_amount, title_field, content_field)

        datafile = pd.read_csv(items_file)
        file_headers = list(datafile)
        file_values = datafile.values

        crowd_job.create_items(file_headers, file_values)

        # items created and posted
        # crowd_job.create_items(crowd_job.multiple_job_id, file_headers, file_values)

        # first vote for each item
        # crowd_job.collect_votes_results(crowd_job.multiple_job_id)

        response = {"message": "job finished"}
        return jsonify(response)

class Tasks(Resource):
    @api.doc(params={
        'job_id': 'Job ID',
        'worker_id': 'Worker Uuid'
    })
    def get(self, job_id, worker_id):
        db_job = DBCrowdJob(mongo, job_id)
        free_items = db_job.get_items_by_state(Item.STATE_FREE)
        item = RandomStrategy().get_assignment(worker_id, free_items)  # different strategies can be set
        response = {'items': []}
        if bool(item):
            db_job.assign_item(item['internal_id'])  # change state to assigned
            json_item = {
                            "id": item['internal_id'],
                            "title": Item().get_title(db_job.job['title_field'],
                                                      item['attributes_names'], item['values']),
                            "content": Item().get_content(db_job.job['content_field'],
                                                          item['attributes_names'], item['values'])
                         }
            response['items'].append(json_item)

        return jsonify(response)


resource_fields = api.model('CrowdVote', {
    'job_id': fields.Integer,
    'worker_id': fields.String,
    'item_id': fields.Integer,
    'vote': fields.Integer
})


class Votes(Resource):
    @api.expect(resource_fields)
    def post(self):
        data = json.loads(request.data)

        job_id = data['job_id']
        worker_id = data['worker_id']
        item_id = data['item_id']
        vote = data['vote']

        db_job = DBCrowdJob(mongo, job_id)
        item = db_job.get_item_by_id(item_id)
        item['votes'][str(worker_id)] = vote
        db_job.update_item_votes(item_id, item['votes'])
        db_job.wait_item(item_id)  # change state to waiting

        # run stopping rule
        platform_job = PlatformCrowdJob(FigureEight(api_key), job_id)
        StopManagement.manage_round(db_job, platform_job)

        response = {"message": "vote submitted"}
        return jsonify(response)


api.add_resource(Jobs, '/jobs', endpoint='jobs')
api.add_resource(Tasks, '/tasks/<int:job_id>/<string:worker_id>', endpoint='tasks')
api.add_resource(Votes, '/votes', endpoint='votes')

if __name__ == '__main__':
    app.run(debug=False)
