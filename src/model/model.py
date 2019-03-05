import requests
import json

class PlatformCrowdJob():
    MULTIPLE_VOTES_PER_ITEM = 3
    SINGLE_VOTES_PER_ITEM = 1

    def __init__(self, api_key, crowd_platform, classification_fn, crowd_price, items_per_worker, title, instructions):
        self.api_key = api_key
        self.crowd_platform = crowd_platform
        self.classification_fn = classification_fn
        self.crowd_price = crowd_price
        self.items_per_worker = items_per_worker
        self.title = title
        self.instructions = instructions
        self.multiple_job_id = None
        self.single_job_id = None
        self.items = []

    def create(self):
        # initial multiple votes job
        self.multiple_job_id = self.crowd_platform.create_job(self.title, self.instructions)
        self.crowd_platform.set_job_payment(self.multiple_job_id, self.crowd_price)
        self.crowd_platform.set_job_items_max_votes(self.multiple_job_id, self.MULTIPLE_VOTES_PER_ITEM)
        self.crowd_platform.set_job_items_per_page(self.multiple_job_id, self.items_per_worker)

        # single votes job
        self.single_job_id = self.crowd_platform.create_job(self.title, self.instructions)
        self.crowd_platform.set_job_payment(self.single_job_id, self.crowd_price)
        self.crowd_platform.set_job_items_max_votes(self.single_job_id, self.SINGLE_VOTES_PER_ITEM)
        self.crowd_platform.set_job_items_per_page(self.single_job_id, self.items_per_worker)

    def create_items(self, job_id, attributes_names, items_values):
        for key, item_values in enumerate(items_values):
            external_id = self.crowd_platform.create_item(job_id, attributes_names, item_values)
            self.items.append(Item(job_id, key, attributes_names, item_values, external_id))

    def collect_votes_results(self, job_id):
        self.crowd_platform.get_results(job_id, self.items)

    #only republish in single vote job
    def republish_item(self, internal_id):
        item = [item for item in self.items if item.internal_id == internal_id]
        external_id = self.crowd_platform.create_item(self.single_job_id, item.attributes_names, item.values)
        item.add_external_id(external_id)

    def wait_for_results(self, pending_items):
        self.crowd_platform.wait_for_results(pending_items)


class Item():
    #corresponding to csv header and row value
    def __init__(self, multiple_job_id, item_id, attributes_names, item_values, external_id):
        self.multiple_job_id = multiple_job_id
        self.single_job_id = None
        self.internal_id = item_id
        self.external_ids = [external_id]
        self.attributes_names = attributes_names
        self.values = item_values
        self.votes = {} #votes = {worker_id: vote,...}

    # returns last external id
    def external_id(self):
        return self.external_ids[-1:][0]

    def add_external_id(self, external_id):
        self.external_ids.append(external_id)

    def add_vote(self, worker_id, vote):
        self.votes[worker_id] = vote

class CrowdPlatform():
    def __init__(self, api_key):
        self.api_key = api_key

    def create_job(self, title, instructions):
        pass

    def set_job_payment(self, job_id, price):
        pass

    def set_job_items_max_votes(self, job_id, num_votes):
        pass

    def set_job_items_per_page(self, job_id, num_items):
        pass

    def pause_job(self, job_id):
        pass

    def resume_job(self, job_id):
        pass

    def cancel_job(self, job_id):
        pass

    def get_job_items(self, job_id):
        pass

    def create_item(self, job_id, attributes_names, item_values):
        pass

    def get_results(self, job_id, items):
        pass

    def get_item_result(self, item_id):
        pass

    def stop_contributor(self, job_id, worker_id):
        pass

    def wait_for_results(self, pending_items):
        pass


class FigureEight(CrowdPlatform):
    BASE_URL = "https://api.figure-eight.com/v1/jobs"

    'curl -X POST --data-urlencode "job[title]={some_title}" --data-urlencode "job[instructions]={some_instructions}" https://api.figure-eight.com/v1/jobs.json?key={api_key}'
    def create_job(self, title, instructions):
        request_url = f"{self.BASE_URL}.json"

        payload = {
            'key': self.api_key,
            'job': {
                'title': title,
                'instructions': instructions
            }
        }

        headers = {'content-type': 'application/json'}
        response = requests.post(request_url, data=json.dumps(payload), headers=headers)
        if not response.status_code == 200:
            raise ValueError("Error during API call")

        res_json = response.json()

        return res_json['id']

    'curl -X POST -d "unit[data][{column1}]={some_data_1}" -d "unit[data][{column2}]={some_data_2}" https://api.figure-eight.com/v1/jobs/{job_id}/units.json?key={api_key}'
    def create_item(self, job_id, attributes_names, item_values):
        request_url = f"{self.BASE_URL}/{job_id}/units.json"

        data = {attr_val: item_values[attr_key] for attr_key, attr_val in enumerate(attributes_names)}

        payload = {
            'key': self.api_key,
            'unit': {
                'data': data
            }
        }

        headers = {'content-type': 'application/json'}
        response = requests.post(request_url, data=json.dumps(payload), headers=headers)
        if not response.status_code == 200:
            raise ValueError("Error during API call")

        res_json = response.json()

        return res_json['id']



    'curl -X GET "https://api.figure-eight.com/v1/jobs/{job_id}/judgments.json?key={api_key}&page={1}"'
    def get_results(self, job_id, items):
        results = {}
        page = 1
        all_items_received = False
        while not all_items_received:
            request_url = f"{self.BASE_URL}/{job_id}/judgments.json?key={self.api_key}&page={page}"

            response = requests.get(request_url)
            if not response.status_code == 200:
                raise ValueError("Error during API call")

            response_json = response.json()

            #100 items per call
            #increment page until all items are received
            if bool(response_json): #if received empty hash
                all_items_received = True
            else:
                results = {**results, **response_json}
                page += 1
        #end while

        for item in items:
            platform_item_vote = [judgment for judgment in results if judgment['unit_id'] == item.external_id()][0]
            item.add_vote(platform_item_vote['worker_id'], platform_item_vote['judgment'])

        return items

    def wait_for_results(self, job_id, pending_items):
        received_all_judgments = False
        while not received_all_judgments:
            results = {}
            page = 1
            received_all_items = False
            while not received_all_items:
                request_url = f"{self.BASE_URL}/{job_id}/judgments.json?key={self.api_key}&page={page}"

                response = requests.get(request_url)
                if not response.status_code == 200:
                    raise ValueError("Error during API call")

                response_json = response.json()

                # 100 items per call
                # increment page until all items are received
                if bool(response_json):  # if received empty hash
                    received_all_items = True
                else:
                    results = {**results, **response_json}
                    page += 1
            # end while

            answered_items = 0
            for item in pending_items:
                platform_item_vote = [judgment for judgment in results if judgment['unit_id'] == item.external_id()][0]
                if not bool(platform_item_vote):
                    break
                else:
                    answered_items += 1
            #end for

            if answered_items == len(pending_items):
                received_all_judgments = True

        #end while

        #add votes
        for item in pending_items:
            platform_item_vote = [judgment for judgment in results if judgment['unit_id'] == item.external_id()][0]
            item.add_vote(platform_item_vote['worker_id'], platform_item_vote['judgment'])

    'curl -X PUT --data-urlencode "job[payment_cents]={20}" https://api.figure-eight.com/v1/jobs/{job_id}.json?key={api_key}'
    def set_job_payment(self, job_id, cents):
        request_url = f"{self.BASE_URL}/{job_id}.json"

        payload = {
            'key': self.api_key,
            'job': {
                'payment_cents': cents
            }
        }

        headers = {'content-type': 'application/json'}
        requests.put(request_url, data=json.dumps(payload), headers=headers)

    'curl -X PUT --data-urlencode "job[judgments_per_unit]={3}" https://api.figure-eight.com/v1/jobs/{job_id}.json?key={api_key}'
    def set_job_items_max_votes(self, job_id, num_votes):
        request_url = f"{self.BASE_URL}/{job_id}.json"

        payload = {
            'key': self.api_key,
            'job': {
                'judgments_per_unit': num_votes
            }
        }

        headers = {'content-type': 'application/json'}
        response = requests.put(request_url, data=json.dumps(payload), headers=headers)
        if not response.status_code == 200:
            raise ValueError("Error during API call")

    'curl -X PUT --data-urlencode "job[units_per_assignment]={n}" https://api.figure-eight.com/v1/jobs/{job_id}.json?key={api_key}'
    def set_job_items_per_page(self, job_id, num_items):
        request_url = f"{self.BASE_URL}/{job_id}.json"

        payload = {
            'key': self.api_key,
            'job': {
                'units_per_assignment': num_items
            }
        }

        headers = {'content-type': 'application/json'}
        response = requests.put(request_url, data=json.dumps(payload), headers=headers)
        if not response.status_code == 200:
            raise ValueError("Error during API call")

    'curl -X PUT --data-urlencode "job[cml]={some_new_cml}" https://api.figure-eight.com/v1/jobs/{job_id}.json?key={api_key}'
    def set_job_cml(self, cml):
        pass

    def pause_job(self, job_id):
        'curl -X GET https://api.figure-eight.com/v1/jobs/{job_id/pause.json?key={api_key}'

    def resume_job(self, job_id):
        'curl -X GET https://api.figure-eight.com/v1/jobs/{job_id}/resume.json?key={api_key}'

    def cancel_job(self, job_id):
        'curl -X GET https://api.figure-eight.com/v1/jobs/{job_id}/cancel.json?key={api_key}'

    def get_job_items(self, job_id):
        'curl -X GET "https://api.figure-eight.com/v1/jobs/{job_id}/judgments.json?key={api_key}&page={1}"'

    def get_item_result(self, item_id):
        "curl -X GET https://api.figure-eight.com/v1/jobs/{job_id}/units/{unit_id}/judgments.json?key={api_key}"

    def stop_contributor(self, job_id, worker_id):
        "curl -X PUT -d 'reason={input_reason}' -d 'manual=true' https://api.figure-eight.com/v1/jobs/{job_id}/workers/{worker_id}/reject.json?key={api_key}"
