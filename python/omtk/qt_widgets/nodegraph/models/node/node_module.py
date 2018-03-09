from . import node_entity


class NodeGraphModuleModel(node_entity.NodeGraphEntityModel):
    def get_children(self):
        result = set()
        for sub_component in self._entity.iter_sub_components():
            child = self._registry.get_node_from_value(sub_component)
            result.add(child)
        return result
