'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8' 888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b d88' 88b 888""8P
  .88ooo8888.   888ooo888  888     888   888  888     888  888ooo888  888   888   888 888ooo888  888
 .8'     888.  888    .o  888     888   888  888     888  888    .o  888   888   888 888    .o  888
o.oooooo..o88.oooooo..oPoooo88b    Yo8od8P' o888o   o888o Y8bod8P' o888o  888bod8P' Y8bod8P' d888b
d8P'    Y8 d8P'    Y8 888         "'                                    888
Y88bo.      Y88bo.       888  oooo  oooo  oo.ooooo.  oooo d8b              o888o
 "Y8888o.   "Y8888o.   888 .8P'   888   888' 88b 888""8P
     "Y88b      "Y88b  888888.     888   888   888  888
oo     .d8P oo     .d8P  888 `88b.   888   888   888  888
8""88888P'  8""88888P'  o888o o888o o888o  888bod8P' d888b
                                           888
                                          o888o

https://aeronautica-helper.vercel.app
https://github.com/SSkipr/AeronauticaHelper
Version 4.1.6 Beta
'''

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QFrame,
    QWidget,
)

from AeroHelper.automation.routes_catalog import (
    custom_routes,
    fetch_remote_routes,
    local_official_version,
    official_routes,
    parse_remote_routes_payload,
    routes_dev_mode,
    save_custom_routes,
    save_official_routes,
    set_routes_dev_mode,
)
from AeroHelper.ui.app_icon import load_app_icon
from AeroHelper.utils.version import is_version_outdated

DEV_NOTICE = (
    'Dev mode is on. Spell every airport and destination exactly as Aeronautica shows it. '
    'Dock and exit are bearings, or none. Cycles is how many undocking cycles to run. '
    'These are your routes, not the official list, and they may not work.'
)
OFFICIAL_NOTICE = (
    'These are the official AutoPilot routes saved on this computer. '
    'Fetch latest to load the current list from the AeroHelper server and fill this window.'
)
ROUTES_BUTTON_TOOLTIP = (
    'Beta. Opens the official AutoPilot routes list, and Dev mode for editing your own routes. '
    'The official list has its own version and can change without a new AeroHelper release.'
)


def _ui():
    try:
        from AeroHelper.ui import main_window_theme as theme
    except ImportError:
        from AeroHelper.ui import main_window as theme
    return theme


def _routes_as_list(routes):
    items = []
    for key, meta in (routes or {}).items():
        destinations = [
            {'key': dest_key, 'name': dest_name}
            for dest_key, dest_name in (meta.get('destinations') or {}).items()
        ]
        items.append({
            'key': key,
            'full_name': meta.get('full_name') or '',
            'destinations': destinations or [{'key': '', 'name': ''}],
            'dock': meta.get('dock') or 'none',
            'exit': meta.get('exit') or 'none',
            'cycles': meta.get('cycles') or 0,
        })
    return items


def _blank_airport():
    return {
        'key': '',
        'full_name': '',
        'destinations': [{'key': '', 'name': ''}],
        'dock': 'none',
        'exit': 'none',
        'cycles': 0,
    }


def handle_startup_routes_payload(window, payload):
    parsed = parse_remote_routes_payload(payload)
    if not parsed:
        return
    version, routes = parsed
    window._pending_official_version = version
    window._pending_official_routes = routes
    if not is_version_outdated(local_official_version(), version):
        return
    app_remote = getattr(window, 'global_version', None)
    app_local = getattr(window, 'version', None)
    if app_remote and is_version_outdated(app_local, app_remote):
        return
    QTimer.singleShot(700, lambda: _prompt_outdated_routes(window, version))


def _prompt_outdated_routes(window, version):
    if getattr(window, '_routes_prompt_shown', False):
        return
    if not is_version_outdated(local_official_version(), version):
        return
    if getattr(window, '_pending_official_version', None) != version:
        return
    window._routes_prompt_shown = True
    pull = _show_outdated_dialog(window, local_official_version() or 'not downloaded', version)
    if pull:
        try:
            save_official_routes(version, getattr(window, '_pending_official_routes', None))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(window, 'Routes', f'Could not save the newest official routes.\n\n{exc}')
    open_routes_window(window)


def _show_outdated_dialog(parent, local_version, remote_version):
    ui = _ui()
    dialog = QDialog(parent)
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    dialog.setWindowTitle('AeroHelper - Routes List')
    dialog.setModal(True)
    icon = load_app_icon()
    if not icon.isNull():
        dialog.setWindowIcon(icon)
    dialog.resize(520, 280)
    dialog.setStyleSheet(
        f'''
        QDialog {{ background-color: {ui.BG_WINDOW}; }}
        QLabel {{ color: {ui.TEXT_PRIMARY}; background: transparent; }}
        QPushButton#pullRoutes {{
            background-color: {ui.ACCENT_WARM};
            color: {ui.BG_WINDOW};
            border: none;
            border-radius: 10px;
            padding: 10px 18px;
            font-weight: 700;
        }}
        QPushButton#ignoreRoutes {{
            background: rgba(255, 255, 255, 0.065);
            color: {ui.TEXT_PRIMARY};
            border: 1px solid {ui.BORDER_SOFT};
            border-radius: 10px;
            padding: 10px 18px;
            font-weight: 650;
        }}
        '''
    )
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(28, 24, 28, 20)
    layout.setSpacing(12)
    title = QLabel('Your official routes list is out of date')
    title.setFont(QFont(ui.APP_FONT_FAMILY, 14, QFont.Bold))
    title.setStyleSheet(f'color: {ui.ERROR_TEXT};')
    title.setWordWrap(True)
    layout.addWidget(title)
    detail = QLabel(
        f'Your routes list: {local_version}\n'
        f'Latest routes list: {remote_version}\n\n'
        'This is the official routes list, not the AeroHelper app version. '
        'Nothing is downloaded until you choose Pull newest.'
    )
    detail.setFont(QFont(ui.APP_FONT_FAMILY, 10))
    detail.setWordWrap(True)
    layout.addWidget(detail)
    layout.addStretch()
    choice = {'pull': False}

    def _ignore():
        choice['pull'] = False
        dialog.accept()

    def _pull():
        choice['pull'] = True
        dialog.accept()

    ignore_btn = QPushButton('Ignore')
    ignore_btn.setObjectName('ignoreRoutes')
    ignore_btn.setMinimumHeight(44)
    ignore_btn.setCursor(Qt.PointingHandCursor)
    ignore_btn.clicked.connect(_ignore)
    pull_btn = QPushButton('Pull newest')
    pull_btn.setObjectName('pullRoutes')
    pull_btn.setMinimumHeight(44)
    pull_btn.setCursor(Qt.PointingHandCursor)
    pull_btn.clicked.connect(_pull)
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(ignore_btn)
    row.addWidget(pull_btn)
    layout.addLayout(row)
    dialog.exec_()
    return choice['pull']


def open_routes_window(parent):
    existing = getattr(parent, '_routes_dialog', None)
    if existing is not None:
        existing.raise_()
        existing.activateWindow()
        return
    dialog = RoutesDialog(parent)
    parent._routes_dialog = dialog
    dialog.finished.connect(lambda: setattr(parent, '_routes_dialog', None))
    dialog.exec_()


class RoutesDialog(QDialog):
    fetch_finished = pyqtSignal(object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = _ui()
        self._dev_mode = routes_dev_mode()
        saved_custom = custom_routes()
        self._custom_draft = _routes_as_list(saved_custom if saved_custom else official_routes())
        self._cards = []
        self._fetching = False
        self.fetch_finished.connect(self._on_fetch_finished)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle('Route customization')
        self.setModal(True)
        icon = load_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self._apply_size()
        self._build()
        self._render()

    def _apply_size(self):
        ui = self._ui
        width = ui.scale_px(980)
        height = ui.scale_px(900)
        screen = QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            width = min(width, max(ui.scale_px(420), avail.width() - 24))
            height = min(height, max(ui.scale_px(520), avail.height() - 32))
        self.resize(width, height)
        self.setMinimumSize(min(ui.scale_px(420), width), min(ui.scale_px(480), height))

    def _build(self):
        ui = self._ui
        self.setStyleSheet(
            f'''
            QDialog {{ background-color: {ui.BG_WINDOW}; }}
            QLabel {{ color: {ui.TEXT_PRIMARY}; background: transparent; }}
            QCheckBox {{ color: {ui.TEXT_PRIMARY}; background: transparent; spacing: 8px; }}
            QLineEdit {{
                color: {ui.TEXT_PRIMARY};
                background: {ui.BG_INPUT};
                border: 1px solid {ui.BORDER_SOFT};
                border-radius: 8px;
                padding: 6px 8px;
            }}
            QScrollArea {{ background: transparent; border: none; }}
            QFrame#routeCard {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid {ui.BORDER_SOFT};
                border-radius: 12px;
            }}
            QPushButton#saveRoutes {{
                background-color: {ui.ACCENT_WARM};
                color: {ui.BG_WINDOW};
                border-radius: 10px;
                padding: 8px 18px;
                font-weight: 700;
            }}
            QPushButton#pullRoutes {{
                background-color: {ui.ACCENT_WARM};
                color: {ui.BG_WINDOW};
                border-radius: 10px;
                padding: 8px 18px;
                font-weight: 700;
            }}
            '''
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel('Route customization')
        title.setFont(QFont(ui.APP_FONT_FAMILY, 14, QFont.Bold))
        header.addWidget(title)
        beta = QLabel('BETA')
        beta.setFont(QFont(ui.APP_FONT_FAMILY, 8, QFont.Bold))
        beta.setStyleSheet(
            f'color: {ui.WARNING_TEXT}; background: {ui.WARNING_BG}; '
            f'border: 1px solid {ui.WARNING_BORDER}; border-radius: 8px; padding: 2px 8px;'
        )
        header.addWidget(beta)
        header.addStretch()
        root.addLayout(header)
        self._version_label = QLabel()
        self._version_label.setFont(QFont(ui.APP_FONT_FAMILY, 9))
        self._version_label.setStyleSheet(f'color: {ui.TEXT_MUTED};')
        self._version_label.setWordWrap(True)
        root.addWidget(self._version_label)
        dev_row = QHBoxLayout()
        self._dev_box = QCheckBox('Dev mode')
        self._dev_box.setFont(QFont(ui.APP_FONT_FAMILY, 10, QFont.Bold))
        self._dev_box.setChecked(self._dev_mode)
        self._dev_box.stateChanged.connect(self._on_dev_toggled)
        dev_row.addWidget(self._dev_box)
        dev_row.addStretch()
        root.addLayout(dev_row)
        self._notice = QLabel()
        self._notice.setWordWrap(True)
        self._notice.setFont(QFont(ui.APP_FONT_FAMILY, 9))
        root.addWidget(self._notice)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 8, 0)
        self._body_layout.setSpacing(12)
        self._scroll.setWidget(self._body)
        root.addWidget(self._scroll, 1)
        buttons = QHBoxLayout()
        self._add_btn = QPushButton('Add airport')
        self._add_btn.setStyleSheet(ui.SECONDARY_BUTTON_STYLE)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.clicked.connect(self._add_airport)
        buttons.addWidget(self._add_btn)
        self._pull_btn = QPushButton('Fetch latest')
        self._pull_btn.setObjectName('pullRoutes')
        self._pull_btn.setCursor(Qt.PointingHandCursor)
        self._pull_btn.clicked.connect(self._fetch_latest)
        buttons.addWidget(self._pull_btn)
        buttons.addStretch()
        close_btn = QPushButton('Close')
        close_btn.setStyleSheet(ui.SECONDARY_BUTTON_STYLE)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        self._save_btn = QPushButton('Save')
        self._save_btn.setObjectName('saveRoutes')
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self._save)
        buttons.addWidget(self._save_btn)
        root.addLayout(buttons)

    def _pending_update(self):
        parent = self.parent()
        remote_version = getattr(parent, '_pending_official_version', None)
        remote_routes = getattr(parent, '_pending_official_routes', None)
        if not remote_version or not isinstance(remote_routes, dict):
            return None
        if is_version_outdated(local_official_version(), remote_version):
            return (remote_version, remote_routes)
        return None

    def _refresh_header(self):
        ui = self._ui
        local_version = local_official_version() or 'not downloaded'
        pending = self._pending_update()
        if pending:
            text = f'Official routes list version: {local_version}    Latest: {pending[0]}'
        else:
            text = f'Official routes list version: {local_version}'
        if self._dev_mode:
            text += '\nDev mode uses your saved routes. Unsaved edits apply after you click Save.'
        self._version_label.setText(text)
        self._notice.setText(DEV_NOTICE if self._dev_mode else OFFICIAL_NOTICE)
        self._notice.setStyleSheet(f'color: {ui.WARNING_TEXT if self._dev_mode else ui.TEXT_MUTED};')
        self._dev_box.blockSignals(True)
        self._dev_box.setChecked(self._dev_mode)
        self._dev_box.blockSignals(False)
        editing = self._dev_mode
        self._add_btn.setVisible(editing)
        self._save_btn.setVisible(editing)
        if not self._fetching:
            self._pull_btn.setEnabled(True)
            self._pull_btn.setText('Fetch latest')

    def _clear_body(self):
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._cards = []

    def _render(self):
        self._refresh_header()
        self._clear_body()
        routes = self._custom_draft if self._dev_mode else _routes_as_list(official_routes())
        if not routes:
            empty = QLabel('No routes yet. Fetch latest to load the official list.')
            empty.setWordWrap(True)
            self._body_layout.addWidget(empty)
        for item in routes:
            self._body_layout.addWidget(self._airport_card(item, self._dev_mode))
        self._body_layout.addStretch(1)

    def _airport_card(self, item, editable):
        ui = self._ui
        card = QFrame()
        card.setObjectName('routeCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        key = item.get('key') or ''
        meta_name = item.get('full_name') or ''
        destinations = item.get('destinations') or []
        record = {
            'dock': item.get('dock') or 'none',
            'exit': item.get('exit') or 'none',
            'cycles': item.get('cycles') or 0,
            'key': None,
            'name': None,
            'dest_rows': [],
            'dest_layout': None,
        }
        if editable:
            key_row = QHBoxLayout()
            key_edit = QLineEdit(key)
            key_edit.setPlaceholderText('Airport key, spelled exactly')
            name_edit = QLineEdit(meta_name)
            name_edit.setPlaceholderText('Full name, spelled exactly')
            record['key'] = key_edit
            record['name'] = name_edit
            key_row.addWidget(key_edit, 1)
            key_row.addWidget(name_edit, 2)
            remove = QPushButton('Remove')
            remove.setStyleSheet(ui.SECONDARY_BUTTON_STYLE)
            remove.setCursor(Qt.PointingHandCursor)
            remove.clicked.connect(lambda _checked=False, target=card: self._remove_airport(target))
            key_row.addWidget(remove)
            layout.addLayout(key_row)
        else:
            title = QLabel(key)
            title.setFont(QFont(ui.APP_FONT_FAMILY, 10, QFont.Bold))
            full = QLabel(meta_name)
            full.setStyleSheet(f'color: {ui.TEXT_MUTED};')
            full.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(full)
            dock_line = QLabel(
                f"Dock {record['dock']}    Exit {record['exit']}    Cycles {record['cycles']}"
            )
            dock_line.setStyleSheet(f'color: {ui.TEXT_MUTED};')
            dock_line.setWordWrap(True)
            layout.addWidget(dock_line)
        if editable:
            layout.addLayout(self._dock_row(record))
        dest_host = QVBoxLayout()
        record['dest_layout'] = dest_host
        if editable:
            for dest in destinations:
                dest_host.addLayout(self._dest_row(record, dest.get('key') or '', dest.get('name') or ''))
            add_dest = QPushButton('Add destination')
            add_dest.setStyleSheet(ui.SECONDARY_BUTTON_STYLE)
            add_dest.setCursor(Qt.PointingHandCursor)
            add_dest.clicked.connect(lambda _checked=False, target=record: self._add_destination(target))
            layout.addLayout(dest_host)
            layout.addWidget(add_dest, 0, Qt.AlignLeft)
        else:
            for dest in destinations:
                line = QLabel(f"{dest.get('key') or ''}  →  {dest.get('name') or ''}")
                line.setWordWrap(True)
                line.setFont(QFont(ui.APP_FONT_FAMILY, 9))
                layout.addWidget(line)
        record['card'] = card
        self._cards.append(record)
        return card

    def _dock_row(self, record):
        ui = self._ui
        row = QHBoxLayout()
        dock_edit = QLineEdit(str(record.get('dock') or 'none'))
        exit_edit = QLineEdit(str(record.get('exit') or 'none'))
        cycles_edit = QLineEdit(str(record.get('cycles') if record.get('cycles') is not None else 0))
        dock_edit.setPlaceholderText('none')
        exit_edit.setPlaceholderText('none')
        cycles_edit.setPlaceholderText('0')
        record['dock_edit'] = dock_edit
        record['exit_edit'] = exit_edit
        record['cycles_edit'] = cycles_edit
        for label, edit in (('Dock', dock_edit), ('Exit', exit_edit), ('Cycles', cycles_edit)):
            caption = QLabel(label)
            caption.setFont(QFont(ui.APP_FONT_FAMILY, 8, QFont.Bold))
            caption.setStyleSheet(f'color: {ui.TEXT_MUTED};')
            row.addWidget(caption)
            row.addWidget(edit, 1)
        return row

    def _dock_values(self, record):
        dock_edit = record.get('dock_edit')
        exit_edit = record.get('exit_edit')
        cycles_edit = record.get('cycles_edit')
        dock = dock_edit.text().strip() if dock_edit is not None else str(record.get('dock') or 'none')
        exit_bearing = exit_edit.text().strip() if exit_edit is not None else str(record.get('exit') or 'none')
        if cycles_edit is not None:
            raw_cycles = cycles_edit.text().strip()
        else:
            raw_cycles = str(record.get('cycles') if record.get('cycles') is not None else 0)
        if raw_cycles == '':
            cycles = 0
        else:
            try:
                cycles = int(raw_cycles)
            except ValueError:
                return None
            if cycles < 0:
                return None
        return {
            'dock': dock or 'none',
            'exit': exit_bearing or 'none',
            'cycles': cycles,
        }

    def _dest_row(self, record, dest_key, dest_name):
        ui = self._ui
        row = QHBoxLayout()
        key_edit = QLineEdit(dest_key)
        key_edit.setPlaceholderText('Destination key')
        name_edit = QLineEdit(dest_name)
        name_edit.setPlaceholderText('Destination full name')
        entry = {'key': key_edit, 'name': name_edit, 'row': row}
        record['dest_rows'].append(entry)
        row.addWidget(key_edit, 1)
        row.addWidget(name_edit, 2)
        remove = QPushButton('✕')
        remove.setStyleSheet(ui.SECONDARY_BUTTON_STYLE)
        remove.setCursor(Qt.PointingHandCursor)
        remove.setFixedWidth(ui.scale_px(36))
        remove.clicked.connect(lambda _checked=False, target=record, item=entry: self._remove_destination(target, item))
        row.addWidget(remove)
        return row

    def _capture_draft(self):
        if not self._dev_mode:
            return
        draft = []
        for record in self._cards:
            if record['key'] is None:
                continue
            destinations = [
                {'key': dest['key'].text(), 'name': dest['name'].text()}
                for dest in record['dest_rows']
            ]
            dock_values = self._dock_values(record) or {
                'dock': record['dock_edit'].text() if record.get('dock_edit') is not None else record.get('dock') or 'none',
                'exit': record['exit_edit'].text() if record.get('exit_edit') is not None else record.get('exit') or 'none',
                'cycles': record['cycles_edit'].text() if record.get('cycles_edit') is not None else record.get('cycles') or 0,
            }
            draft.append({
                'key': record['key'].text(),
                'full_name': record['name'].text(),
                'destinations': destinations or [{'key': '', 'name': ''}],
                'dock': dock_values['dock'],
                'exit': dock_values['exit'],
                'cycles': dock_values['cycles'],
            })
        self._custom_draft = draft

    def _on_dev_toggled(self, state):
        enabled = state == Qt.Checked
        if self._dev_mode and not enabled:
            self._capture_draft()
        self._dev_mode = enabled
        try:
            set_routes_dev_mode(enabled)
        except OSError as exc:
            QMessageBox.warning(self, 'Routes', f'Could not save Dev mode.\n\n{exc}')
        if enabled and not self._custom_draft:
            self._custom_draft = _routes_as_list(official_routes())
        self._render()

    def _add_airport(self):
        self._capture_draft()
        self._custom_draft.append(_blank_airport())
        self._render()

    def _remove_airport(self, card):
        self._capture_draft()
        kept = []
        for record, item in zip(self._cards, self._custom_draft):
            if record.get('card') is card:
                continue
            kept.append(item)
        self._custom_draft = kept
        self._render()

    def _add_destination(self, record):
        record['dest_layout'].addLayout(self._dest_row(record, '', ''))

    def _remove_destination(self, record, entry):
        record['dest_rows'] = [item for item in record['dest_rows'] if item is not entry]
        row = entry['row']
        while row.count():
            item = row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        record['dest_layout'].removeItem(row)

    def _draft_from_cards(self, allow_incomplete):
        draft = {}
        seen = set()
        for record in self._cards:
            if record['key'] is None:
                continue
            key = record['key'].text().strip()
            name = record['name'].text().strip()
            destinations = {}
            incomplete = False
            for dest in record['dest_rows']:
                dest_key = dest['key'].text().strip()
                dest_name = dest['name'].text().strip()
                if not dest_key and not dest_name:
                    continue
                if not dest_key or not dest_name:
                    incomplete = True
                destinations[dest_key] = dest_name
            if not key and not name and not destinations:
                continue
            if not allow_incomplete and (not key or not name or not destinations or incomplete):
                return None
            if key in seen:
                return None
            dock_values = self._dock_values(record)
            if dock_values is None:
                return None
            if key:
                seen.add(key)
            draft[key] = {
                'full_name': name,
                'destinations': destinations,
                'dock': dock_values['dock'],
                'exit': dock_values['exit'],
                'cycles': dock_values['cycles'],
            }
        return draft

    def _save(self):
        draft = self._draft_from_cards(allow_incomplete=False)
        if not draft:
            QMessageBox.warning(
                self,
                'Routes',
                'Every airport needs a unique key, a full name, and at least one destination.\n'
                'Cycles must be a whole number, 0 or higher. Dock and exit are bearings, or none.\n\n'
                'Spell names exactly as Aeronautica shows them. Routes that are spelled wrong may not work.',
            )
            return
        try:
            save_custom_routes(draft)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Routes', f'Could not save your routes.\n\n{exc}')
            return
        self._dev_mode = True
        self._custom_draft = _routes_as_list(custom_routes())
        self._render()

    def _fetch_latest(self):
        if self._fetching:
            return
        self._fetching = True
        self._pull_btn.setEnabled(False)
        self._pull_btn.setText('Fetching...')

        def work():
            try:
                parsed = fetch_remote_routes()
                self.fetch_finished.emit(parsed, '')
            except Exception as exc:
                self.fetch_finished.emit(None, str(exc))

        import threading
        threading.Thread(target=work, daemon=True).start()

    def _on_fetch_finished(self, parsed, error):
        self._fetching = False
        if error or not isinstance(parsed, tuple):
            self._pull_btn.setEnabled(True)
            self._pull_btn.setText('Fetch latest')
            QMessageBox.warning(self, 'Routes', f'Could not fetch the latest routes.\n\n{error or "The server list was empty."}')
            return
        version, routes = parsed
        try:
            save_official_routes(version, routes)
        except (OSError, ValueError) as exc:
            self._pull_btn.setEnabled(True)
            self._pull_btn.setText('Fetch latest')
            QMessageBox.warning(self, 'Routes', f'Could not save the latest routes.\n\n{exc}')
            return
        parent = self.parent()
        if parent is not None:
            parent._pending_official_version = version
            parent._pending_official_routes = routes
        self._custom_draft = _routes_as_list(routes)
        self._render()
