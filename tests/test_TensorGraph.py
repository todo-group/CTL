from tests.packedTest import PackedTest
from CTL.tensor.contract.tensorGraph import TensorGraph
from CTL.tensor.tensor import Tensor
from CTL.tensor.contract.link import makeLink
from CTL.tensor.contract.optimalContract import makeTensorGraph, contractWithSequence
import CTL.funcs.funcs as funcs
import numpy as np

class TestTensorGraph(PackedTest):

    def __init__(self, methodName = 'runTest'):
        super().__init__(methodName = methodName, name = 'TensorGraph')

    def test_TensorGraph(self):
        shapeA = (300, 4, 5)
        shapeB = (300, 6)
        shapeC = (4, 6, 5)
        a = Tensor(shape = shapeA, labels = ['a300', 'b4', 'c5'], data = np.ones(shapeA))
        b = Tensor(shape = shapeB, labels = ['a300', 'd6'], data = np.ones(shapeB))
        c = Tensor(shape = shapeC, labels = ['b4', 'd6', 'c5'], data = np.ones(shapeC))

        makeLink(a.getLeg('a300'), b.getLeg('a300'))
        makeLink(a.getLeg('b4'), c.getLeg('b4'))
        makeLink(a.getLeg('c5'), c.getLeg('c5'))
        makeLink(b.getLeg('d6'), c.getLeg('d6'))

        tensorList = [a, b, c]

        tensorGraph = makeTensorGraph(tensorList)

        # if we use typical dim, then contract between 0 and 2 first is preferred
        # and this is not true if we consider the real bond dimension 300

        seq = tensorGraph.optimalContractSequence(typicalDim = None)
        self.assertListEqual(seq, [(0, 1), (2, 0)])
        self.assertEqual(tensorGraph.optimalCostResult(), 36120)

        seq = tensorGraph.optimalContractSequence(typicalDim = None, bf = True)
        self.assertEqual(tensorGraph.optimalCostResult(), 36120)

        # res1 = contractWithSequence(tensorList, seq = seq)

        seq = tensorGraph.optimalContractSequence(typicalDim = 10)
        self.assertListEqual(seq, [(0, 2), (1, 0)])
        self.assertEqual(tensorGraph.optimalCostResult(), 10100)

        seq = tensorGraph.optimalContractSequence(typicalDim = 10, bf = True)
        self.assertEqual(tensorGraph.optimalCostResult(), 10100)

        res2 = contractWithSequence(tensorList, seq = seq)
        self.assertEqual(res2.a ** 2, funcs.tupleProduct(shapeA) * funcs.tupleProduct(shapeB) * funcs.tupleProduct(shapeC))

        # problem: now the tensor network can only be contracted once
        # this can be solved by create another (copyable) FiniteTensorNetwork object
        # which traces all the bonds and legs, and can be easily copied


