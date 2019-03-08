import requests
import json


class PlatformCrowdJob:
    MULTIPLE_VOTES_PER_ITEM = 3
    SINGLE_VOTES_PER_ITEM = 1

    def __init__(self, crowd_platform, job_id=None):
        self.crowd_platform = crowd_platform
        self.job_id = job_id

    def create(self, crowd_price, items_per_worker, title, instructions):
        self.job_id = self.crowd_platform.create_job(title, instructions)
        self.crowd_platform.set_job_payment(self.job_id, crowd_price)
        self.crowd_platform.set_job_items_max_votes(self.job_id, self.MULTIPLE_VOTES_PER_ITEM)
        self.crowd_platform.set_job_items_per_page(self.job_id, items_per_worker)

    def create_dummy_items(self, amount):
        dummy_item = DummyItem()
        for key in range(amount):
            self.crowd_platform.create_item(self.job_id, dummy_item.title, dummy_item.content)

    def set_max_votes(self, amount):
        self.crowd_platform.set_job_items_max_votes(self.job_id, amount)


class DummyItem:
    def __init__(self):
        self.title = "Dummy title created via API"
        self.content = "Dummy content created via API"


class CrowdPlatform:
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

    def create_item(self, job_id, item):
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
    def create_item(self, job_id, title, content):
        request_url = f"{self.BASE_URL}/{job_id}/units.json"

        data = {'title': title, 'content': content}

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
