from src.strategies.smart_stop_module import decision_function_bayes
from src.helpers.algorithms_utils import get_formatted_items_votes
from src.connectors.db import Item
from src.strategies.aggregation import AggregationFunctionFactory


class StopManagement:
    @staticmethod
    def manage_round(db_job, platform_job):
        if db_job.is_in_initial_rounds():  # still collecting initial votes in some
            StopManagement.free_waiting_initial_items(db_job)
        elif db_job.has_waiting_items_equal_votes_num():  # if all waiting items has same num of votes
            StopManagement.manage_stop(db_job, platform_job)

    @staticmethod
    def manage_stop(db_job, platform_job):
        items = db_job.get_items_by_state(Item.STATE_WAITING)
        total_votes = get_formatted_items_votes(items)

        results = decision_function_bayes(len(items),
                                          total_votes,
                                          db_job.get_job_classification_threshold(),
                                          db_job.get_job_cost_ratio(),
                                          AggregationFunctionFactory.get_function(db_job.get_job_classification_fn()))

        # True = must continue, False = stop
        continue_amount = len([1 for i, v in results.items() if v == True])
        platform_job.set_max_votes(1)  # set max 1 vote per item
        platform_job.create_dummy_items(continue_amount)

        for item_id, item_decision in results.items():
            if item_decision:
                db_job.free_item(item_id)  # True = continue collecting, set free
            else:
                db_job.finish_item(item_id)  # False = stop, set item finished

    @staticmethod
    def free_waiting_initial_items(db_job):
        items = db_job.get_items_by_state(Item.STATE_WAITING)
        for item in items:
            if len(item['votes']) < db_job.get_job_initial_votes_num():  # free items if votes < initial
                db_job.free_item(item['internal_id'])
