# import numpy as np 
import CTL.funcs.xplib as xplib
from CTL.tensor.tensor import Tensor
from CTL.tensor.tensorFactory import makeSquareTensor
from CTL.tensor.contract.contractExp import squareHorizontalContractFTN, squareVerticalContractFTN
from CTL.tensor.contract.contractExp import HOTRGHorizontalContractFTN, HOTRGVerticalContractFTN
from CTL.tensor.contract.contractExp import makeSquareTensorDict, squareTrace
import CTL.funcs.funcs as funcs
import CTL.funcs.linalg as linalgFuncs

class HOTRG:

    # square lattice HOTRG
    # start with a single tensor, contract on square lattice
    # each time contract on one direction by two tensors, do HOSVD, then 

    def __init__(self, a, chiH = 16, chiV = None):
        assert (a is not None), "Error: HOTRG must be initialized with at least one tensor."
        self.horizontalIterateFTN = HOTRGHorizontalContractFTN()
        self.verticalIterateFTN = HOTRGVerticalContractFTN()
        self.horizontalProjectFTN = {'l': squareHorizontalContractFTN('l'), 'r': squareHorizontalContractFTN('r')}
        self.verticalProjectFTN = {'u': squareVerticalContractFTN('u'), 'd': squareVerticalContractFTN('d')}
        self.chiH = chiH
        if (chiV is None):
            self.chiV = chiH
        else:
            self.chiV = chiV
        if (isinstance(a, Tensor)):
            self.a = a.copy()
        else:
            self.a = makeSquareTensor(a)

        if (self.a.degreeOfFreedom is None):
            self.a.degreeOfFreedom = 1

        self.aNorms = []
        self.errors = []

        self.aArchive = []
        # self.impurityArchive = []
        self.directChoices = []
        self.projectors = []

        self.appendToArchive()
        # self.iterateChoices = []

        self.impurityParts = 2

    def appendToArchive(self):
        self.normalizeTensors()
        self.aArchive.append(self.a.copy())

    def normalizeTensors(self):
        aNorm = self.a.norm()
        self.a.a /= aNorm 
        self.aNorms.append(aNorm)

    def directedIterateTrial(self, d):
        funcs.assertInSet(d, ['u', 'd', 'l', 'r'], 'direction')
        # make projector, and return the truncation error
        # for l: use M, M', calculate MM', return U_L
        if (d == 'l') or (d == 'r'):
            # horizontal project
            squareTensor = self.horizontalProjectFTN[d].contract(makeSquareTensorDict(self.a))
            # l, r
            # labels = [d, funcs.oppositeDirection(d)]
            # print('a = {}'.format(self.a))
            # print('squareTensor = {}'.format(squareTensor))
            squareMat = squareTensor.toMatrix(rows = [d], cols = [funcs.oppositeDirection(d)])
            # print(squareTensor)
            prjMat, error = linalgFuncs.solveEnv(squareMat, self.chiH)
            # prjTensor = Tensor(data = prjMat, shape = (chiH ** 2, prjMat.shape[1]), labels = ['i', 'o'])
        else:
            squareTensor = self.verticalProjectFTN[d].contract(makeSquareTensorDict(self.a))
            # print('a = {}'.format(self.a))
            # print('squareTensor = {}'.format(squareTensor))
            squareMat = squareTensor.toMatrix(rows = [d], cols = [funcs.oppositeDirection(d)])
            prjMat, error = linalgFuncs.solveEnv(squareMat, self.chiV)
            # prjTensor = Tensor(data = prjMat, shape = (chiV ** 2, prjMat.shape[1]), labels = ['i', 'o'])

        # envTrace = xplib.xp.trace(squareMat)
        # envTraceApprox = xplib.xp.trace(prjMat.T @ squareMat @ prjMat)
        # error = (envTrace - envTraceApprox) / envTrace 
        # deltaTensor = (prjMat.T @ squareMat @ prjMat) - squareMat 
        # error = xplib.xp.linalg.norm(deltaTensor) / xplib.xp.linalg.norm(squareMat)
        return {'error': error, 'projectTensor': prjMat}

    def directedIterate(self, d, prjTensor, inputTensor1 = None, inputTensor2 = None):
        # print(inputTensor1, inputTensor2)
        # print(prjTensor.shape)
        funcs.assertInSet(d, ['u', 'd', 'l', 'r'], 'direction')
        # use the real projector for iteration
        if (inputTensor1 is None):
            inputTensor1 = self.a 
        if (inputTensor2 is None):
            inputTensor2 = self.a
        chiH = inputTensor1.shapeOfLabel('l')
        chiV = inputTensor1.shapeOfLabel('u')
        if (d == 'l') or (d == 'r'):
            # given U_L: 
            # the prjTensor
            lTensor = Tensor(data = prjTensor, shape = (chiH, chiH, prjTensor.shape[1]), labels = ['u', 'd', 'o'])
            rTensor = Tensor(data = funcs.transposeConjugate(prjTensor), shape = (prjTensor.shape[1], chiH, chiH), labels = ['o', 'u', 'd'])
            if (d == 'r'):
                lTensor, rTensor = rTensor, lTensor 
            return self.horizontalIterateFTN.contract({'u': inputTensor1, 'd': inputTensor2, 'l': lTensor, 'r': rTensor})
        else:
            uTensor = Tensor(data = prjTensor, shape = (chiV, chiV, prjTensor.shape[1]), labels = ['l', 'r', 'o'])
            dTensor = Tensor(data = funcs.transposeConjugate(prjTensor), shape = (prjTensor.shape[1], chiV, chiV), labels = ['o', 'l', 'r'])
            if (d == 'd'):
                uTensor, dTensor = dTensor, uTensor
            return self.verticalIterateFTN.contract({'u': uTensor, 'd': dTensor, 'l': inputTensor1, 'r': inputTensor2})
        
    def iterate(self):
        # choose among 4 directions

        dof = self.a.degreeOfFreedom

        directions = ['u', 'd', 'l', 'r']
        minimumError = -1.0
        projectTensor = None 
        bestDirection = None 
        
        for d in directions: 

            projector = self.directedIterateTrial(d)
            # print(d, projector['error'])
            if (minimumError < 0) or (projector['error'] < minimumError):
                minimumError = projector['error']
                bestDirection = d
                projectTensor = projector['projectTensor']
        
        # self.directChoices.append((bestDirection, projectTensor))
        self.a = self.directedIterate(bestDirection, projectTensor)
        self.a.degreeOfFreedom = dof * 2
        self.appendToArchive()
        self.errors.append(minimumError)
        self.directChoices.append(bestDirection)
        self.projectors.append(projectTensor)

    def getNorm(self, idx):
        assert (idx < len(self.aNorms)), "Error: HOTRG.getNorm(idx) get {}, but only {} norms.".format(idx, len(self.aNorms))
        return self.aNorms[idx]

    def impurityIterate(self, tensors, loopIdx):
        assert len(tensors) == self.impurityParts, "Error: HOTRG.impurityIterate requires the length of tensor list to be {}, but {} gotten.".format(self.impurityParts, len(tensors))
        assert loopIdx < len(self.directChoices), "Error: HOTRG.impurityIterate can not accept loopIdx {} not smaller than current iteration number {}.".format(loopIdx, len(self.directChoices))
        res = self.directedIterate(self.directChoices[loopIdx], self.projectors[loopIdx], tensors[0], tensors[1])
        # res.a /= self.aNorms[loopIdx + 1]
        return res

    # def impurityIterate(self, impurities, highestOrder = None):
    #     pass 
    #     # TODO: impurity tensor calculation
    #     # we have the basis tensor, and 1, 2, ... n-th order of the impurity tensor
    #     # to calculate the new tensor of 0, 1, ... n: we need the projectors from the original 
    #     # directChoices and projectors will be used
        
    #     initialOrderN = len(impurities)
    #     # order 0 .. initialOrderN - 1
    #     if (highestOrder is None):
    #         highestOrder = initialOrderN
        
    def tensorTrace(self, x):
        # return x.trace(rows = ['u', 'l'], cols = ['d', 'r'])
        return squareTrace(x)
    def pureTensorTrace(self, idx):
        return squareTrace(self.aArchive[idx])

    def logZDensity(self):
        # only a will be considered
        # for i in range(len(self.aArchive)):
        accumulateLogZ = 0.0
        res = []
        stepN = len(self.aArchive)
        # print(stepN, len(self.aNorms))
        for i in range(stepN):
            dof = self.aArchive[i].degreeOfFreedom
            accumulateLogZ += xplib.xp.log(self.aNorms[i]) / dof
            # TNTrace = triangleTensorTrace(self.aArchive[i], self.bArchive[i])
            # TNTrace = self.aArchive[i].trace(rows = ['u', 'l'], cols = ['d', 'r'])
            TNTrace = squareTrace(self.aArchive[i])
            currLogZ = accumulateLogZ + xplib.xp.log(TNTrace) / dof
            # contraction: 1A + 1B
            res.append(currLogZ)

        return xplib.xp.array(res)