import collections

import pymel.core as pymel
from omtk.core.classCtrl import BaseCtrl
from omtk.libs import libCtrlShapes
from omtk.libs import libRigging
from omtk.modules_broken import rigFK

from omtk import constants


class CtrlFkAdd(BaseCtrl):
    def __createNode__(self, size=None, refs=None, *args, **kwargs):
        # Resolve size automatically if refs are provided.
        ref = next(iter(refs), None) if isinstance(refs, collections.Iterable) else refs
        if size is None and ref is not None:
            size = libRigging.get_recommended_ctrl_size(ref)
        else:
            size = 1.0

        node = libCtrlShapes.create_shape_needle(size=size, *args, **kwargs)

        return node


class AdditiveFK(rigFK.FK):
    """
    An AdditiveFK chain is a standard FK chain that have one or many additional controllers to rotate the entire chain.
    """
    _CLASS_CTRL_IK = CtrlFkAdd

    def __init__(self, *args, **kwargs):
        super(AdditiveFK, self).__init__(*args, **kwargs)
        self.num_ctrls = 1
        self.additive_ctrls = []

    def build(self, *args, **kwargs):
        super(AdditiveFK, self).build(*args, **kwargs)

        nomenclature_anm = self.get_nomenclature_anm()

        # Ensure to create the finger ctrl in the good orientation
        if nomenclature_anm.side == self.rig.nomenclature.SIDE_L:
            normal_data = {constants.Axis.x: (1, 0, 0), constants.Axis.y: (0, 1, 0), constants.Axis.z: (0, 0, 1)}
        else:
            normal_data = {constants.Axis.x: (-1, 0, 0), constants.Axis.y: (0, -1, 0), constants.Axis.z: (0, 0, -1)}

        self.additive_ctrls = filter(None, self.additive_ctrls)
        if not self.additive_ctrls:
            ctrl_add = CtrlFkAdd()
            self.additive_ctrls.append(ctrl_add)

        # HACK - Temp since we don't support multiple ctrl for the moment
        ctrl_add = self.additive_ctrls[0]
        for i, ctrl in enumerate(self.additive_ctrls):
            # Resolve ctrl name
            nomenclature = nomenclature_anm + self.rig.nomenclature(self.jnt.stripNamespace().nodeName())
            if self._NAME_CTRL_MERGE and len(self.additive_ctrls) == 1:
                name = nomenclature.resolve("addFk", "{0:02d}".format(i))
            else:
                name = nomenclature.resolve("addFk")

            ctrl.build(name=name, refs=self.chain.start, normal=normal_data[self.rig.DEFAULT_UPP_AXIS])
            ctrl.offset.setMatrix(self.chain.start.getMatrix(worldSpace=True))
            ctrl.setParent(self.grp_anm)

        for i, ctrl in enumerate(self.ctrls):
            # HACK Add a new layer if this is the first ctrl to prevent Gimbal lock problems
            if i == 0:
                ctrl.offset = ctrl.append_layer("gimbal")
            attr_rotate_x = libRigging.create_utility_node('addDoubleLinear',
                                                           input1=ctrl.offset.rotateX.get(),
                                                           input2=ctrl_add.rotateX
                                                           ).output
            attr_rotate_y = libRigging.create_utility_node('addDoubleLinear',
                                                           input1=ctrl.offset.rotateY.get(),
                                                           input2=ctrl_add.rotateY
                                                           ).output
            attr_rotate_z = libRigging.create_utility_node('addDoubleLinear',
                                                           input1=ctrl.offset.rotateZ.get(),
                                                           input2=ctrl_add.rotateZ
                                                           ).output
            pymel.connectAttr(attr_rotate_x, ctrl.offset.rotateX)
            pymel.connectAttr(attr_rotate_y, ctrl.offset.rotateY)
            pymel.connectAttr(attr_rotate_z, ctrl.offset.rotateZ)

        # Constraint the fk ctrls in position to the additive fk ctrls
        pymel.pointConstraint(ctrl_add, self.ctrls[0].offset)

    def iter_ctrls(self):
        for ctrl in super(AdditiveFK, self).iter_ctrls():
            yield ctrl
        for ctrl in self.additive_ctrls:
            yield ctrl


def register_plugin():
    return AdditiveFK