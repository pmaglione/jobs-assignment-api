import helpers.algorithms_utils as alg_utils
import numpy as np
from helpers.truth_finder import expectation_maximization
from scipy.stats import binom

#hyperparameters
drawing_simulations_amount = 50
expert_cost_increment = 2

'''
     Input:
     v - votes for item i
            ct - value between 0 and 1 for deciding if prob of data is enough or must continue
            cf - function to calculate how likely is to be classified
            cr - cost ratio between crowd to expert vote [0,1]
        Output:
            (cost_mean, cost_std)
'''
def cost_estimator(v, ct, cf, cr):
    simulated_costs = []

    for _ in range(drawing_simulations_amount):
        must_continue = True
        i_item_votes = v.copy()
        while (must_continue):
            classification_prob_in = cf(alg_utils.input_adapter_single(i_item_votes))
            classification_prob_out = 1 - classification_prob_in
            if ((classification_prob_in > ct) or (classification_prob_out > ct)):
                must_continue = False            
                simulated_costs.append(alg_utils.get_crowd_cost(i_item_votes, cr))
            else:
                vote = np.random.binomial(1, classification_prob_in)
                
                new_index = max(i_item_votes.keys()) + 1
                i_item_votes[new_index] = [vote]
                actual_cost = alg_utils.get_crowd_cost(i_item_votes, cr)

                if((actual_cost) > (1 * expert_cost_increment)):
                    must_continue = False
                    simulated_costs.append(actual_cost)
        #end while      
    #end for

    return (np.mean(simulated_costs),np.std(simulated_costs))

    
'''
    Function to answer: must continue collecting votes over each task?

    Input:
    items - set of items
    votes - set of votes over each item
    classification_threshold - value between 0 and 1 for deciding if prob of data is enough or must continue
    cost_ratio - ratio of crowd to expert cost, [0,1]
    classification_function - function to calculate how likely is to be classified

    Output:
        Dictionary with the decision indexed by item_id
            {
                item_id: bool
                ...
                item_n: ...
            }
        Where False = Stop and True=Continue collecting votes
'''
def decision_function_mv(items, votes, ct, cr, cf):       
    results = {i:(((1 - ct) <= cf(alg_utils.input_adapter_single(i_votes)) <= ct)) for i, i_votes in votes.items()}

    ids_items_unclassified = [i for i, d in results.items() if d == True]

    for item_id in ids_items_unclassified:
        item_votes = votes[item_id].copy()
        if (len(item_votes) == 0):
            results[item_id] = True
        else:
            cost_mean, cost_std = cost_estimator(item_votes, ct, cf, cr)

            if(cost_mean > (1 * expert_cost_increment)):
                results[item_id] = False
        
    
    return results

def decision_function_mv_base(items, votes, ct, cr, cf):       
    results = {i:(((1 - ct) <= cf(alg_utils.input_adapter_single(i_votes)) <= ct)) for i, i_votes in votes.items()}

    return results

def cost_estimator_em(v, ct, cf, cr, acc):
    simulated_costs = []

    for _ in range(drawing_simulations_amount):
        must_continue = True
        i_item_votes = v.copy()
        while (must_continue):
            classification_prob_in = cf(alg_utils.input_adapter_single(i_item_votes))
            classification_prob_out = 1 - classification_prob_in
            if ((classification_prob_in > ct) or (classification_prob_out > ct)):
                must_continue = False            
                simulated_costs.append(alg_utils.get_crowd_cost(i_item_votes, cr))
            else:
                if(classification_prob_in >= classification_prob_out):
                    vote = np.random.binomial(1, acc) #inclusion vote
                else:
                    vote = np.random.binomial(1, 1 - acc) #exclusion vote
                    
                new_index = max(i_item_votes.keys()) + 1
                i_item_votes[new_index] = [vote]
                actual_cost = alg_utils.get_crowd_cost(i_item_votes, cr)

                if((actual_cost) > (1 * expert_cost_increment)):
                    must_continue = False
                    simulated_costs.append(actual_cost)
        #end while      
    #end for

    return (np.mean(simulated_costs),np.std(simulated_costs))

#For using EM all items must have the same number of votes
def decision_function_em(items, votes, ct, cr, cf):       
    results = {i:(((1 - ct) <= cf(alg_utils.input_adapter_single(i_votes)) <= ct)) for i, i_votes in votes.items()}

    ids_items_unclassified = [i for i, d in results.items() if d == True]
    
    accs, p = expectation_maximization(len(next(iter(votes.values()))), items, alg_utils.input_adapter(votes))
    acc_est = np.mean(accs)
    
    for item_id in ids_items_unclassified:
        item_votes = votes[item_id].copy()
        if (len(item_votes) == 0):
            results[item_id] = True
        else:
            cost_mean, cost_std = cost_estimator_em(item_votes, ct, cf, cr, acc_est)

            if(cost_mean > (1 * expert_cost_increment)):
                results[item_id] = False
        
    
    return results

def cost_estimator_bayes(v, ct, cf, cr, acc):
    simulated_costs = []

    for _ in range(drawing_simulations_amount):
        must_continue = True
        i_item_votes = v.copy()
        while (must_continue):
            classification_prob_in = bayes_prob_in(i_item_votes, acc)
            classification_prob_out = 1 - classification_prob_in
            if ((classification_prob_in > ct) or (classification_prob_out > ct)):
                must_continue = False            
                simulated_costs.append(alg_utils.get_crowd_cost(i_item_votes, cr))
            else:
                if(classification_prob_in >= classification_prob_out):
                    vote = np.random.binomial(1, acc) #inclusion vote
                else:
                    vote = np.random.binomial(1, 1 - acc) #exclusion vote
                    
                new_index = max(i_item_votes.keys()) + 1
                i_item_votes[new_index] = [vote]
                actual_cost = alg_utils.get_crowd_cost(i_item_votes, cr)

                if((actual_cost) > (1 * expert_cost_increment)):
                    must_continue = False
                    simulated_costs.append(actual_cost)
        #end while      
    #end for

    return (np.mean(simulated_costs),np.std(simulated_costs))

#For using EM all items must have the same number of votes
def decision_function_bayes(items, votes, ct, cr, cf): 
    accs, p = expectation_maximization(len(next(iter(votes.values()))), items, alg_utils.input_adapter(votes))
    acc_est = np.mean(accs)
    
    results = {i:(((1 - ct) <= bayes_prob_in(i_votes, acc_est) <= ct)) for i, i_votes in votes.items()}

    ids_items_unclassified = [i for i, d in results.items() if d == True]
    
    for item_id in ids_items_unclassified:
        item_votes = votes[item_id].copy()
        if (len(item_votes) == 0):
            results[item_id] = True
        else:
            cost_mean, cost_std = cost_estimator_bayes(item_votes, ct, cf, cr, acc_est)

            if(cost_mean > (1 * expert_cost_increment)):
                results[item_id] = False
        
    
    return results

def bayes_prob_in(i_item_votes, acc):
    pos_v = sum([x[0] for k,x in i_item_votes.items()])
    neg_v = len(i_item_votes) - pos_v
    like_in = binom.pmf(pos_v, pos_v+neg_v, acc)
    like_out = binom.pmf(neg_v, pos_v+neg_v, acc)

    return like_in / (like_in  + like_out)