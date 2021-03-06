# import numpy as np 
import CTL.funcs.xplib as xplib

def solveEnv(aMat, chi, threshold = 1e-10):
    """
    Generate a projector matrix from a environment matrix, usually the product of two projectors we want.

    Parameters
    ----------
    aMat : 2-D ndarray of float
        The environment matrix to be decomposed.
    chi : int
        The maximum nunber of eigenvalues to be kept. Help decide the second dimension of the result.
    threshold : float, default 1e-10
        The threshold below which we will consider a float number as zero. 
    """
    eigenValuesEnv, eigenVectorsEnv = xplib.xp.linalg.eigh(aMat)
    eigenExist = sum(eigenValuesEnv > threshold)
    # print(eigenValuesEnv)
    if (chi > eigenExist):
        error = 0.0
    else:
        error = 1.0 - xplib.xp.sum(eigenValuesEnv[-chi:]) / xplib.xp.sum(eigenValuesEnv)
    
    chi = min(chi, eigenExist)
    # if (chi > eigenVectorsEnv.shape[1]):
    #     return eigenVectorsEnv, 0.0
    # else:
    return xplib.xp.flip(eigenVectorsEnv[:, -chi:], axis = 1), error
    # return eigenVectorsEnv[:, -chi:]