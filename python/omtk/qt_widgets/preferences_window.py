from omtk.core import plugin_manager
from omtk.core import preferences
from omtk.qt_widgets.ui import preferences_window
from omtk.vendor.Qt import QtCore, QtWidgets


class PreferencesWindow(QtWidgets.QDialog):
    searchQueryChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(PreferencesWindow, self).__init__(parent=parent)

        self._prefs = preferences.get_preferences()

        # Initialize GUI
        self.ui = preferences_window.Ui_Dialog()
        self.ui.setupUi(self)

        # Fill the QComboBox
        self.rig_plugins = sorted(plugin_manager.plugin_manager.get_loaded_plugins_by_type('rigs'))
        rig_plugins_names = [plugin.cls.__name__ for plugin in self.rig_plugins if plugin]
        labels = ['Default'] + rig_plugins_names

        self.ui.comboBox.addItems(labels)

        default_rig_type_name = self._prefs.get_default_rig_class().__name__
        if default_rig_type_name in rig_plugins_names:
            self.ui.comboBox.setCurrentIndex(rig_plugins_names.index(default_rig_type_name) + 1)

        self.ui.checkBox.setChecked(self._prefs.hide_welcome_screen)

        # Connect events
        self.ui.comboBox.currentIndexChanged.connect(self.on_default_rig_changed)
        self.ui.checkBox.stateChanged.connect(self.on_hide_welcome_screen_changed)

    def on_default_rig_changed(self, index):
        if index == 0:
            self._prefs.default_rig = None
        else:
            self._prefs.default_rig = self.rig_plugins[index - 1].cls.__name__

        self._prefs.save()

    def on_hide_welcome_screen_changed(self, state):
        self._prefs.hide_welcome_screen = self.ui.checkBox.isChecked()
        self._prefs.save()


gui = PreferencesWindow()


def show():
    global gui
    gui.show()
