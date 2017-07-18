import logging
from maya import cmds
import pymel.core as pymel
from omtk.core.classComponent import Component
from omtk.core.classComponentDefinition import ComponentDefinition
from omtk.libs import libComponents
from omtk.qt_widgets.ui import widget_component_list
from omtk.vendor.Qt import QtWidgets, QtCore

log = logging.getLogger('omtk')


class MayaNodeDefinition(ComponentDefinition):
    type = 'Maya Node'

    def __init__(self, cls_name):
        self._cls_name = cls_name
        self.name = cls_name

    def instanciate(self, parent, name='unamed'):
        return pymel.createNode(self._cls_name, name=name)


class ComponentDefinitionTableModel(QtCore.QAbstractTableModel):
    _HEADERS = (
        'Name', 'Type', 'Description'
    )

    def __init__(self, entries):
        super(ComponentDefinitionTableModel, self).__init__()
        self.__entries = entries

    def load_maya_nodes(self):
        for node_type in cmds.allNodeTypes():
            inst = MayaNodeDefinition(node_type)
            self.__entries.append(inst)
        self.__entries = sorted(self.__entries)

    # --- QtCore.QAbstractTableModel ---

    def rowCount(self, index):
        return len(self.__entries)

    def columnCount(self, index):
        return len(self._HEADERS)

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return
        return self._HEADERS[section]

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            entry = self.__entries[row]
            if col == 0:
                return entry.name
            if col == 1:
                return entry.type if hasattr(entry, 'type') else 'unknown'
            # if col == 1:
            #     return entry.version
            # if col == 2:
            #     return entry.author
            # if col == 3:
            #     return entry.uid

    # --- Custom methods ---

    def get_entry(self, index):
        # type: (int) -> ComponentDefinition
        return self.__entries[index]


class WidgetComponentList(QtWidgets.QWidget):
    signalComponentCreated = QtCore.Signal(Component)

    def __init__(self, parent):
        super(WidgetComponentList, self).__init__(parent)
        self.ui = widget_component_list.Ui_Form()
        self.ui.setupUi(self)

        view = self.ui.tableView

        # Configure headers
        horizontal_header = view.horizontalHeader()
        horizontal_header.setSectionResizeMode(horizontal_header.Stretch)
        view.verticalHeader().hide()

        defs = list(libComponents.walk_available_component_definitions())
        self.model = ComponentDefinitionTableModel(defs)
        self.model.load_maya_nodes()
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        view.setModel(self.proxy_model)
        # view.resizeColumnsToContents()

        self._manager = None

        self._ctrl = None

        # Connect events
        self.ui.lineEdit_search.textChanged.connect(self.on_user_changed_query)

        self._set_selected_row_index(0)

    def on_user_changed_query(self, query):
        self.proxy_model.setFilterRegExp('.*{0}.*'.format(query.replace('*', '.*')))
        self._set_selected_row_index(0)

    def set_ctrl(self, ctrl):
        """
        Define the link with the main logic controller.
        :param ctrl:
        :return:
        """
        self._ctrl = ctrl

    def set_manager(self, parent):
        self._manager = parent

    def _get_selected_entries(self):
        # type: () -> List[ComponentDefinition]
        selected_row_indexes = self._get_selected_row_indexes()
        return [self.model.get_entry(i) for i in selected_row_indexes]

    def _get_selected_row_indexes(self):
        selection_model = self.ui.tableView.selectionModel()
        return [self.proxy_model.mapToSource(index).row() for index in selection_model.selectedRows()]

    def _set_selected_row_index(self, row):
        selection_model = self.ui.tableView.selectionModel()
        model = selection_model.model()
        num_rows = model.rowCount()
        num_cols = model.columnCount()

        # Prevent out of bound.
        if row < 0:
            return
        if row > (num_rows - 1):
            return

        sel = QtCore.QItemSelection(
            model.sourceModel().createIndex(row, 0),
            model.sourceModel().createIndex(row, num_cols - 1)
        )
        selection_model.select(sel, selection_model.ClearAndSelect)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Enter or key == QtCore.Qt.Key_Return:
            self.action_submit()
            return

        if key == QtCore.Qt.Key_Escape:
            self.close()
            return

        if key == QtCore.Qt.Key_Up:
            row = next(iter(self._get_selected_row_indexes()), None)
            self._set_selected_row_index(row - 1)
            return

        if key == QtCore.Qt.Key_Down:
            row = next(iter(self._get_selected_row_indexes()), None)
            self._set_selected_row_index(row + 1)
            return

    def action_submit(self):
        entries = self._get_selected_entries()
        for entry in entries:
            # Create the component in memory
            try:
                component = entry.instanciate(self._manager)
            except Exception, e:
                log.exception(e)
                raise e

            # Export the component metadata
            if isinstance(component, ComponentDefinition):
                from omtk.vendor import libSerialization
                libSerialization.export_network(component, cache=self._manager._serialization_cache)  ## error ehere

            self.signalComponentCreated.emit(component)
        self.close()
