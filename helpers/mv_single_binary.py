from .mv import majority_voting as majority_voting_multiple

def majority_voting(Psi):
    """
    For a single item and binary classification returns the probability of IN
    
    Majority voting fusing: a true value is the one which got most votes.
    :param Psi: observations (a list of object votes)
    :return: for each object we return a dict in a list. Each key in the dict is an object value, the dict values are
    probs.
    """
    #res = majority_voting_multiple(Psi)
    
    #return res[0][1]

    if (len(Psi[0]) == 0):
        return .5
    else:
        return sum([x[1] for x in Psi[0]]) / len(Psi[0])