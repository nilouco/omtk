"""
The NodeGraphWidget use PyFlowgraph to display node, attribute and connections.
It use a NodeGraphModel generaly used as a singleton to store scene informations.
Multiple NodeGraphController bound to this model can interact with multiples NodeGraphView.

Usage example 1, handling MVC ourself
from omtk.qt_widgets import nodegraph_widget
from omtk.vendor.Qt import QtCore, QtGui, QtWidgets

win = QtWidgets.QMainWindow()
view = nodegraph_widget.NodeGraphView()
model = nodegraph_widget.NodeGraphModel()
ctrl = nodegraph_widget.NodeGraphController(model, view)
win.setCentralWidget(view)
win.show()

Usage example 1, using prefab Widget
from omtk.qt_widgets import nodegraph_widget
from omtk.vendor.Qt import QtCore, QtGui, QtWidgets

win = QtWidgets.QMainWindow()
widget = nodegraph_widget.NodeGraphWidget()
win.setCentralWidget(widget)
win.show()
"""
from omtk.libs import libPyflowgraph
from omtk.libs import libPython
from omtk.qt_widgets.nodegraph_widget.ui import nodegraph_widget
from omtk.vendor.Qt import QtWidgets


@libPython.memoized
def _get_singleton_model():
    from .nodegraph_model import NodeGraphModel

    return NodeGraphModel()


class NodeGraphWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        from .nodegraph_controller import NodeGraphController

        super(NodeGraphWidget, self).__init__(parent)
        self.ui = nodegraph_widget.Ui_Form()
        self.ui.setupUi(self)

        # Configure NodeGraphView
        self._nodegraph_view = self.ui.widget_view
        self._nodegraph_model = _get_singleton_model()
        self._nodegraph_ctrl = NodeGraphController(self._nodegraph_model)
        self._nodegraph_ctrl.set_view(self._nodegraph_view)

        # Hack: Connect controller events to our widget
        # print self._nodegraph_ctrl.onLevelChanged
        # self._nodegraph_ctrl.onLevelChanged.connect(self.on_level_changed)

        self._nodegraph_view.set_model(self._nodegraph_ctrl)

        # Connect events
        self.ui.pushButton_add.pressed.connect(self.on_add)
        self.ui.pushButton_del.pressed.connect(self.on_del)
        self.ui.pushButton_expand.pressed.connect(self.on_expand)
        self.ui.pushButton_collapse.pressed.connect(self.on_colapse)
        self.ui.pushButton_down.pressed.connect(self.on_navigate_down)
        self.ui.pushButton_up.pressed.connect(self.on_navigate_up)
        self.ui.pushButton_arrange_upstream.pressed.connect(self.on_arrange_upstream)
        self.ui.pushButton_arrange_downstream.pressed.connect(self.on_arrange_downstream)

        self.ui.widget_view.endSelectionMoved.connect(self.on_selected_nodes_moved)

        # Connect events (breadcrumb)
        self.ui.widget_breadcrumb.path_changed.connect(self.on_level_changed)

    def on_selected_nodes_moved(self):
        for node in self.ui.widget_view.getSelectedNodes():
            if node._meta_data:
                new_pos = node.pos()  # for x reason, .getGraphPos don't work here
                new_pos = (new_pos.x(), new_pos.y())
                libPyflowgraph.save_node_position(node, new_pos)

    def on_add(self):
        raise NotImplementedError

    def on_del(self):
        graph = self.ui.widget_view
        graph.deleteSelectedNodes()

    def on_expand(self):
        self._nodegraph_ctrl.expand_selected_nodes()

    def on_colapse(self):
        return self._nodegraph_ctrl.colapse_selected_nodes()

    def on_navigate_down(self):
        self._nodegraph_ctrl.navigate_down()

    def on_navigate_up(self):
        self._nodegraph_ctrl.navigate_up()

    def _get_active_node(self):
        return next(iter(self._nodegraph_view.getSelectedNodes()), None)

    def on_arrange_upstream(self):
        node = self._get_active_node()
        if not node:
            return
        libPyflowgraph.arrange_upstream(node)

    def on_arrange_downstream(self):
        node = self._get_active_node()
        if not node:
            return
        libPyflowgraph.arrange_downstream(node)

    def on_level_changed(self, model):
        """Called when the current level is changed using the breadcrumb widget."""
        # self.ui.widget_breadcrumb.set_path(model)
        self._nodegraph_ctrl.set_level(model)


# from pyflowgraph.graph_view import GraphView as NodeGraphWidget