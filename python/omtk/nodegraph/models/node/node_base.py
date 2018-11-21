import logging

from omtk import decorators
from omtk.vendor.Qt import QtCore
from omtk.nodegraph.signal import Signal

log = logging.getLogger('omtk.nodegraph')


class NodeModel(QtCore.QObject):  # QObject provide signals
    """Define the data model for a Node which can be used by multiple view."""

    # Signal emitted when the node is unexpectedly deleted.
    onDeleted = Signal(object)

    # Signal emitted when the node is renamed.
    onRenamed = Signal(object)

    # Signal emitted when an attribute is unexpectedly added.
    onPortAdded = Signal(object)  # todo: port to QtCore.QObject

    # Signal emitted when an attribute is unexpectedly removed.
    onPortRemoved = Signal(str)

    def __init__(self, registry, name):
        super(NodeModel, self).__init__()  # initialize QObject
        self._name = name
        self._pos = None
        self._registry = registry
        self._child_nodes = set()
        self._cache_ports = set()

        # Add the new instance to the registry
        registry._register_node(self)

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self._name)

    def __hash__(self):
        return hash(self._name)
        # raise NotImplementedError  # this is implemented for PyNode atm

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not (self == other)

    def dump(self):
        """
        Convert a node to a JSON compatible data structure.
        Used for testing.
        :return: A JSON compatible data structure in the following form:
        {
            'node_name_1': ['port1_name', 'port2_name', ...],
            'node_name_2': ['port1_name', 'port2_name', ...],
            ...
        }
        :rtype: dict
        """
        ports = [str(port.get_name()) for port in self.iter_ports()]
        return {
            'ports': ports,
        }

    def get_name(self):
        return self._name

    def rename(self, new_name):
        self._name = new_name
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    @decorators.memoized_instancemethod
    def get_metadata(self):
        return None

    @decorators.memoized_instancemethod
    def get_metatype(self):
        from omtk.factories import factory_datatypes
        return factory_datatypes.get_datatype(self.get_metadata())

    def get_nodes(self):
        """
        Used for selection purpose. Return what should be selected if the node is selected.
        :return: A list of objects to select.
        """
        return None

    def get_parent(self):
        # type: () -> NodeModel
        """
        Provide access to the upper node level.
        This allow compound nesting.
        :return: A NodeModel instance.
        """
        return None

    def get_children(self):
        # type: () -> List[NodeModel]
        return self._child_nodes

    def get_position(self):
        return self._pos

    def set_position(self, pos):
        self._pos = pos

    def get_ports_metadata(self):
        # Used to invalidate cache
        return set()

    def _register_port(self, port):
        self._cache_ports.add(port)

    def _unregister_port(self, port):
        self._cache_ports.discard(port)

    def iter_ports(self):
        """
        Iterate through all the node ports.
        :return: A port generator
        :rtype: Generator[omtk.nodegraph.PortModel]
        """
        i = self.get_ports()
        for port in i:
            yield port

    def get_ports(self):
        """
        Query all the node ports.
        :return: The node ports.
        :rtype: List[PortModel]
        """
        if not self._cache_ports:
            for port in self.scan_ports():
                self._register_port(port)
        return self._cache_ports

    def get_port_by_name(self, name):
        """
        Find a port with a specific name.
        :param name: The port name we are searching for.
        :return: A port or None if nothing is found.
        :rtype omtk.nodegraph.PortModel or None
        """
        for port in self.iter_ports():
            if port.get_name() == name:
                return port

    def scan_ports(self):
        # type: () -> Generator[PortModel]
        return
        yield

    @decorators.memoized_instancemethod
    def get_input_ports(self):
        # type: () -> list[PortModel]
        return [attr for attr in self.get_ports() if attr.is_writable()]

    @decorators.memoized_instancemethod
    def get_connected_input_ports(self):
        # type: () -> list[PortModel]
        return [attr for attr in self.get_input_ports() if attr.get_input_connections()]

    @decorators.memoized_instancemethod
    def get_output_ports(self):
        # type: () -> list[PortModel]
        return [attr for attr in self.get_ports() if attr.is_readable()]

    @decorators.memoized_instancemethod
    def get_input_connections(self):
        # type: () -> list(PortModel)
        result = []
        for attr in self.get_input_ports():
            result.extend(attr.get_input_connections())
        return result

    @decorators.memoized_instancemethod
    def get_output_connections(self):
        result = []
        for attr in self.get_output_ports():
            result.extend(attr.get_output_connections())
        return result

    @decorators.memoized_instancemethod
    def get_connected_output_ports(self):
        return [attr for attr in self.get_output_ports() if attr.get_output_connections()]

    # --- View related methods

    def _get_widget_label(self):
        """
        Return the name that should be displayed in the Widget label.
        """
        return self._name

    def _get_widget_cls(self):
        """
        Return the desired Widget class.
        """
        from omtk.nodegraph.widgets import node_widget
        return pyflowgraph_node_widget.OmtkNodeGraphNodeWidget

    def get_widget(self, graph, ctrl):
        # type: (PyFlowgraphView, NodeGraphController) -> OmtkNodeGraphNodeWidget
        node_name = self._get_widget_label()
        cls = self._get_widget_cls()
        inst = cls(graph, node_name, self, ctrl)
        return inst

    def on_added_to_scene(self):
        """
        Called when the node is added to a view (scene).
        """
        pass

    def on_removed_from_scene(self):
        """
        Called when the node is removed from the view (scene).
        """
        pass


