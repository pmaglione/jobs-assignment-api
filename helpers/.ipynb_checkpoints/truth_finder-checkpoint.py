import numpy as np
import math
from collections import defaultdict
from .algorithms_utils import invert
from .mv import majority_voting


def expectation_maximization(N, M, Psi):
    """
    The expectation maximization method (EM) from Dong et al., 2013. It iteratively estimates the probs of objects, then
    the accuracies of sources until a convergence is reached.

    :param N: number of sources
    :param M: number of items
    :param Psi: observations
    :return:
    """
    inv_Psi = invert(N, M, Psi)
    # convergence eps
    eps = 0.001
    it_max = 50

    # init iteration
    p = majority_voting(Psi)
    A = [np.average([p[obj][val] for obj, val in x]) for x in inv_Psi]

    it = 2
    while True:
        # E-step
        p = []
        for obj in range(M):
            # a pass to detect all values of an object
            C = defaultdict(float)
            for s, val in Psi[obj]:
                C[val] = 0.0
            # total number of values
            V = len(C)
            if V == 1:
                C[val] = 1.
                p.append(C)
                continue

            # a pass to compute value confidences
            for s, val in Psi[obj]:
                for v in C.keys():
                    if v == val:
                        if A[s] == 0.:
                            A[s] = 0.01
                            C[v] += math.log(A[s])

                    else:
                        if A[s] == 1.:
                            A[s] = 0.99
                        C[v] += math.log((1-A[s])/(V-1))

            # compute probs
            # normalize
            norm = 0.0
            for val in C.keys():
                norm += math.exp(C[val])
            for val in C.keys():
                C[val] = math.exp(C[val])/norm
            p.append(C)

        # M-step
        A_new = [np.average([p[obj][val] for obj, val in x]) for x in inv_Psi]

        # convergence check
        if sum(abs(np.subtract(A, A_new)))/len(A) < eps:
            A = A_new
            break
        else:
            A = A_new

        it += 1
        if it >= it_max:
            return A, p

    return A, p
