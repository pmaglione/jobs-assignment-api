import warnings
warnings.filterwarnings("ignore")

#input adapters
def input_adapter(responses):
    '''
    :param responses:
    :return: Psi
    '''
    Psi = [[] for _ in responses.keys()]
    i = 0
    for obj_id, obj_responses in responses.items():
        k = 0
        for worker_id, worker_response in obj_responses.items():
            Psi[i].append((k, worker_response[0]))
            k += 1
        i += 1
    return Psi

def input_adapter_single(responses):
    '''
    :param responses:
    :return: Psi, N
    '''
    #recreate array
    responses_aux = {}
    i = 0
    for key, response in responses.items():
        responses_aux[i] = response
        i += 1
    responses = responses_aux
    
    responses = {0: responses}
    Psi = [[] for _ in responses.keys()]
    for obj_id, obj_responses in responses.items():
        for worker_id, worker_response in obj_responses.items():
            Psi[obj_id].append((worker_id, worker_response[0]))
    return Psi

def invert(N, M, Psi):
    """
    Inverts the observation matrix. Need for performance reasons.
    :param N:
    :param M:
    :param Psi:
    :return:
    """
    inv_Psi = [[] for _ in range(N)]
    for obj in range(M):
        for s, val in Psi[obj]:
            inv_Psi[s].append((obj, val))
    return inv_Psi
#end

def classify_items_with_expert(votes, gt, cf, th):
    items_classification = []
    for i, v in votes.items():
        prob = cf(input_adapter_single(v))
        if (prob > th):
            items_classification.append(1)
        elif (prob <= .3):
            items_classification.append(0)
        else:
            items_classification.append(gt[i]) #if .3 < prob < th get expert vote

    return items_classification

def classify_items(votes, gt, cf, th):
    items_classification = []
    for i, v in votes.items():
        p_in = cf(input_adapter_single(v))
        p_out = 1 - p_in
        if (p_out > th):
            items_classification.append(0)
        else:
            items_classification.append(1)

    return items_classification

def get_items_predicted_classified(results):
    return {i:v for i,v in results.items() if v == True}

#end

#cost utils

def get_total_cost(votes, cr):
    total_votes_amount = sum([len(v) for i, v in votes.items()]) 

    return total_votes_amount * cr

def get_crowd_cost(item_votes, cr):
    return len(item_votes) * cr
#end
    
#metrics
class Metrics:

    @staticmethod
    #k penalization for false negatives
    def compute_metrics(items_classification, gt, lr = 1):
        # FP == False Inclusion
        # FN == False Exclusion
        fp = fn = tp = tn = 0.
        for i in range(len(gt)):
            gt_val = gt[i]
            cl_val = items_classification[i]

            if gt_val and not cl_val:
                fn += 1
            if not gt_val and cl_val:
                fp += 1
            if gt_val and cl_val:
                tp += 1
            if not gt_val and not cl_val:
                tn += 1
                        

        recall = tp / (tp + fn)
        precision = tp / (tp + fp)
        loss = (fp + (fn * lr)) / len(gt)
        
        return loss, recall, precision
    
# end


# reformat to {item_id: {worker_id:[vote]}}
def get_formatted_items_votes(items):
    total_votes = {}
    for item in items:
        total_votes[item['internal_id']] = {}
        for worker_id, vote in item['votes'].items():
            total_votes[item['internal_id']][int(worker_id)] = [int(vote)]

    return total_votes
