import pymel.core as pymel
from omtk.rigging.autorig.classRigNode import RigNode
from omtk.rigging.autorig.classRigPart import RigPart

'''
A follice is constrained to the surface of a nurbsSurface. (see NurbsPlane class)
'''
class Follicle(RigNode):
    def __init__(self, _parent, *args, **kwargs):
        super(Follicle, self).__init__(*args, **kwargs)

        pymel.connectAttr(_parent.worldSpace, self.node.inputSurface)

    def __createNode__(self, *args, **kwargs):
        joint = pymel.createNode('joint')
        follicle = pymel.createNode('follicle')
        follicleTransform = follicle.getParent()
        follicle.setParent(joint, relative=True, shape=True)
        pymel.connectAttr(follicle.outTranslate, joint.t)
        pymel.connectAttr(follicle.outRotate, joint.r)
        pymel.delete(follicleTransform)
        return joint

def _createNurbsSurfaceFromNurbsCurve(_curve, _width=0.1):
    nurbsMin = pymel.duplicate(_curve)[0]
    nurbsMax = pymel.duplicate(_curve)[0]
    nurbsMin.tz.set(nurbsMin.tz.get() - _width)
    nurbsMax.tz.set(nurbsMin.tz.get() + _width)

    loft = pymel.createNode('loft')
    pymel.connectAttr(nurbsMin.worldSpace, loft.inputCurve[0])
    pymel.connectAttr(nurbsMax.worldSpace, loft.inputCurve[1])

    surface = pymel.createNode('nurbsSurface')
    pymel.connectAttr(loft.outputSurface, surface.create)

    pymel.disconnectAttr(loft.outputSurface, surface.create)
    pymel.delete(loft)
    pymel.delete(nurbsMin)
    pymel.delete(nurbsMax)

def _createSurfaceJnts(_surface, _numJnts=19):
    #minU, maxU = _surface.getMinMaxU()
    #minV, maxV = _surface.getMinMaxV()
    aReturn = []
    print _numJnts
    for i in range(_numJnts):
        follicle = Follicle(_surface, _create=True)
        follicle.parameterV.set(i / float(_numJnts-1))
        follicle.parameterU.set(0.5)
        aReturn.append(follicle)
    return aReturn

class CurveDeformer(RigPart):
    kType_NurbsCurve = 0
    kType_NurbsSurface = 1

    def __init__(self, _line, _numJnts=19, *args, **kwargs):
        super(CurveDeformer, self).__init__(*args, **kwargs)

        self.aInput = [_line]
        self.type = self.kType_NurbsSurface
        self.numJnts = _numJnts

    def Build(self):
        super(CurveDeformer, self).Build()

        oCurve = next((o for o in self.aInput if any (s for s in o.getShapes() if isinstance(s, pymel.nodetypes.NurbsCurve))), None)
        oSurface = next((o for o in self.aInput if any (s for s in o.getShapes() if isinstance(s, pymel.nodetypes.NurbsSurface))), None)

        if self.type == self.kType_NurbsSurface:
            oSurface = _createNurbsSurfaceFromNurbsCurve(oCurve)
            oSurface.rename(self._pNameMapRig.Serialize()+'_nurbsSurface')
            oSurface.setParent(self.oGrpRig)

            for i in range(oSurface.numKnotsInV()-1):
                cluster, clusterHandle = pymel.cluster(oSurface.cv[0:3][i])
                cluster.rename(self._pNameMapRig.Serialize('cluster', _iIter=i))
                clusterHandle.rename(self._pNameMapRig.Serialize('clusterHandle', _iIter=i))
                clusterHandle.setParent(self.oGrpRig)

                uRef = pymel.createNode('transform')
                uRef.rename(self._pNameMapRig.Serialize('cvRef', _iIter=i))
                uRef.setParent(self.oGrpRig)
                pymel.connectAttr(oCurve.controlPoints[i], uRef.t)
                #pymel.connectAttr(libRigging.CreateUtilityNode('pointOnCurveInfo', inputCurve=oCurve.worldSpace, parameter=((float(i)/(oSurface.numKnotsInV()-3)))).position, uRef.t)
                #pymel.tangentConstraint(oCurve, uRef)

                clusterHandle.setParent(uRef)

        assert(isinstance(oSurface, pymel.PyNode))
        self.aJnts = _createSurfaceJnts(oSurface, self.numJnts)
        for i, jnt in enumerate(self.aJnts):
            jnt.rename(self._pNameMapRig.Serialize(_iIter=i))
            jnt.setParent(self.oGrpRig)
