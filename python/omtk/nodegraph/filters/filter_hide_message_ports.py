import pymel.core as pymel
from omtk.nodegraph import nodegraph_filter
from omtk.factories import factory_datatypes

if False:
    from omtk.nodegraph.models import NodeModel, PortModel, ConnectionModel


class NodeGraphMetadataFilter(nodegraph_filter.NodeGraphFilter):
    """
    Simple filter than let only connection between message attribute pass.
    """
    def can_show_port(self, port):
        # type: (PortModel) -> bool
        port_type = port.get_metatype()
        if port_type != factory_datatypes.AttributeType.AttributeMessage:
            return False

        return super(NodeGraphMetadataFilter, self).can_show_port(port)

    # def can_show_connection(self, connection):
    #     # type: (ConnectionModel) -> bool
    #     port_src = connection.get_source()
    #     port_src_type = port_src.get_metatype()
    #     if port_src_type != factory_datatypes.AttributeType.AttributeMessage:
    #         return False
    #
    #     port_dst = connection.get_destination()
    #     port_dst_type = port_dst.get_metatype()
    #     if port_dst_type != factory_datatypes.AttributeType.AttributeMessage:
    #         return False
    #
    #     return super(NodeGraphMetadataFilter, self).can_show_connection(connection)
