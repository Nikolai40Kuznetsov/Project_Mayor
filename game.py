import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSizePolicy, QMenu, QAction
)
from PyQt5.QtGui import QPainter, QPen, QFont, QColor, QPainterPath, QPolygonF
from PyQt5.QtCore import Qt, QRect, QPointF, QPoint

CELL_SIZE = 180
COLS = 10
ROWS = 5
FIELD_W = CELL_SIZE * COLS   
FIELD_H = CELL_SIZE * ROWS   
MENU_H = 75


class Tile:
    """Модель клетки."""
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.building = None        
        self.turns_left = 0         
        self.residents = 0          
        self.is_river = False       
        self.is_blocked = False     


class GridWidget(QWidget):
    """Игровое поле с сеткой и логикой."""
    def __init__(self, game_window):
        super().__init__()
        self.game_window = game_window
        self.setFixedSize(FIELD_W, FIELD_H)
        
        self.tiles = [[Tile(c, r) for c in range(COLS)] for r in range(ROWS)]
        self.generate_river()
        self.update_blocked_state()

    def generate_river(self):
        if random.random() < 0.5:
            r = random.randint(1, ROWS - 2)
            c = 0
            while c < COLS:
                self.tiles[r][c].is_river = True
                if random.random() < 0.3 and c < COLS - 1:
                    dr = random.choice([-1, 1])
                    if 0 < r + dr < ROWS - 1:
                        r += dr
                c += 1
        else:
            c = random.randint(1, COLS - 2)
            r = 0
            while r < ROWS:
                self.tiles[r][c].is_river = True
                if random.random() < 0.3 and r < ROWS - 1:
                    dc = random.choice([-1, 1])
                    if 0 < c + dc < COLS - 1:
                        c += dc
                r += 1

    def update_blocked_state(self):
        for r in range(ROWS):
            for c in range(COLS):
                self.tiles[r][c].is_blocked = False
                
        river_cells = [(c, r) for r in range(ROWS) for c in range(COLS) if self.tiles[r][c].is_river]
        if not river_cells:
            return
            
        has_bridge = any(
            self.tiles[r][c].building == "bridge" 
            for r in range(ROWS) for c in range(COLS)
        )
        if has_bridge:
            return 
            
        reachable = [[False for _ in range(COLS)] for _ in range(ROWS)]
        queue = [(0, 0)]
        reachable[0][0] = True
        
        while queue:
            c, r = queue.pop(0)
            for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nc, nr = c + dc, r + dr
                if 0 <= nc < COLS and 0 <= nr < ROWS:
                    if not reachable[nr][nc]:
                        tile = self.tiles[nr][nc]
                        if tile.is_river and tile.building != "bridge":
                            continue
                        reachable[nr][nc] = True
                        queue.append((nc, nr))
                        
        for r in range(ROWS):
            for c in range(COLS):
                if not reachable[r][c] and not self.tiles[r][c].is_river:
                    self.tiles[r][c].is_blocked = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for r in range(ROWS):
            for c in range(COLS):
                tile = self.tiles[r][c]
                rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if tile.is_river:
                    painter.setBrush(QColor(100, 150, 255))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(rect)
                elif tile.is_blocked:
                    painter.setBrush(QColor(255, 0, 0, 40))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(rect)
                    
                    painter.setPen(QPen(QColor(255, 0, 0, 100), 2))
                    for i in range(-CELL_SIZE, CELL_SIZE, 20):
                        painter.drawLine(rect.left() + i, rect.bottom(), rect.left() + i + CELL_SIZE, rect.top())

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)

        x = 0
        while x <= self.width():
            painter.drawLine(x, 0, x, self.height())
            x += CELL_SIZE

        y = 0
        while y <= self.height():
            painter.drawLine(0, y, self.width(), y)
            y += CELL_SIZE

        for row in range(ROWS):
            for col in range(COLS):
                tile = self.tiles[row][col]
                if tile.building:
                    self.draw_building(painter, tile)

    def draw_building(self, painter, tile):
        cx = tile.col * CELL_SIZE + CELL_SIZE // 2
        cy = tile.row * CELL_SIZE + CELL_SIZE // 2

        if tile.building == "bridge":
            painter.setPen(QPen(QColor(100, 60, 20), 3))
            painter.setBrush(QColor(160, 100, 40))
            painter.drawRect(cx - 70, cy - 15, 140, 30)
            painter.setPen(QPen(QColor(120, 80, 30), 2))
            for i in range(-60, 70, 15):
                painter.drawLine(cx + i, cy - 15, cx + i, cy + 15)
            painter.setPen(QPen(QColor(80, 40, 10), 4))
            painter.drawLine(cx - 70, cy - 25, cx + 70, cy - 25)
            painter.drawLine(cx - 70, cy + 25, cx + 70, cy + 25)
            for i in range(-70, 80, 30):
                painter.drawLine(cx + i, cy - 25, cx + i, cy - 15)
                painter.drawLine(cx + i, cy + 25, cx + i, cy + 15)

        elif tile.building == "house":
            capacity = 10
            if tile.turns_left > 0:
                painter.setPen(QPen(QColor(150, 150, 150), 4, Qt.DashLine))
                painter.setBrush(QColor(200, 200, 200, 100))
                painter.drawRect(cx - 40, cy - 20, 80, 60)
                roof = QPolygonF([
                    QPointF(cx - 50, cy - 20),
                    QPointF(cx, cy - 60),
                    QPointF(cx + 50, cy - 20)
                ])
                painter.drawPolygon(roof)
                painter.setPen(QPen(QColor(100, 100, 100)))
                font = QFont("Arial", 10, QFont.Bold)
                painter.setFont(font)
                painter.drawText(QRect(cx - 45, cy - 10, 90, 30), Qt.AlignCenter, f"Стройка\n({tile.turns_left})")
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 50))
                painter.drawRect(cx - 35, cy - 15, 70, 55)
                painter.setPen(QPen(QColor(60, 30, 10), 2))
                painter.setBrush(QColor(210, 180, 140)) 
                painter.drawRect(cx - 40, cy - 20, 80, 60)
                painter.setBrush(QColor(178, 34, 34)) 
                roof = QPolygonF([
                    QPointF(cx - 50, cy - 20),
                    QPointF(cx, cy - 70),
                    QPointF(cx + 50, cy - 20)
                ])
                painter.drawPolygon(roof)
                painter.setPen(QPen(QColor(50, 20, 0), 2))
                painter.setBrush(QColor(101, 67, 33))
                painter.drawRect(cx - 10, cy + 10, 20, 30)
                painter.setBrush(QColor(135, 206, 250)) 
                painter.drawRect(cx + 15, cy - 5, 15, 15)
                self.draw_residents(painter, tile, cx, cy, capacity)

        elif tile.building == "panel":
            capacity = 100
            if tile.turns_left > 0:
                painter.setPen(QPen(QColor(120, 120, 120), 3, Qt.DashLine))
                painter.setBrush(QColor(180, 180, 180, 100))
                painter.drawRect(cx - 35, cy - 60, 70, 110)
                painter.setPen(QPen(QColor(100, 100, 100), 2))
                painter.drawLine(cx - 45, cy + 40, cx - 45, cy - 70) 
                painter.drawLine(cx + 45, cy + 40, cx + 45, cy - 70) 
                painter.drawLine(cx - 45, cy - 40, cx + 45, cy - 40) 
                painter.drawLine(cx - 45, cy - 10, cx + 45, cy - 10) 
                painter.drawLine(cx - 45, cy + 20, cx + 45, cy + 20) 
                painter.drawLine(cx, cy - 80, cx, cy - 60)
                painter.drawLine(cx - 20, cy - 80, cx + 20, cy - 80)
                painter.setPen(QPen(QColor(80, 80, 80)))
                font = QFont("Arial", 10, QFont.Bold)
                painter.setFont(font)
                painter.drawText(QRect(cx - 45, cy + 50, 90, 30), Qt.AlignCenter, f"Стройка\n({tile.turns_left})")
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 50))
                painter.drawRect(cx - 30, cy - 55, 60, 115)
                painter.setPen(QPen(QColor(80, 80, 80), 2))
                painter.setBrush(QColor(160, 170, 180)) 
                painter.drawRect(cx - 35, cy - 60, 70, 110)
                painter.setPen(QPen(QColor(120, 130, 140), 1))
                painter.drawLine(cx - 15, cy - 60, cx - 15, cy + 50)
                painter.drawLine(cx + 15, cy - 60, cx + 15, cy + 50)
                painter.drawLine(cx - 35, cy - 20, cx + 35, cy - 20)
                painter.drawLine(cx - 35, cy + 10, cx + 35, cy + 10)
                painter.setPen(QPen(QColor(50, 50, 50), 1))
                painter.setBrush(QColor(135, 206, 250))
                painter.drawRect(cx - 30, cy - 50, 15, 15)
                painter.drawRect(cx + 5, cy - 50, 15, 15)
                painter.drawRect(cx - 30, cy - 25, 15, 15)
                painter.drawRect(cx + 5, cy - 25, 15, 15)
                painter.drawRect(cx - 30, cy + 0, 15, 15)
                painter.drawRect(cx + 5, cy + 0, 15, 15)
                painter.setBrush(QColor(60, 60, 60))
                painter.drawRect(cx - 10, cy + 25, 20, 25)
                self.draw_residents(painter, tile, cx, cy, capacity)

    def draw_residents(self, painter, tile, cx, cy, capacity):
        if tile.residents > 0:
            painter.setBrush(QColor(0, 200, 0))
            painter.setPen(Qt.NoPen)
            if tile.building == "house":
                painter.drawEllipse(cx - 45, cy - 45, 12, 12)
            else:
                painter.drawEllipse(cx - 45, cy - 70, 12, 12)
        
        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        text = f"{tile.residents}/{capacity}"
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.setPen(Qt.NoPen)
        text_rect = QRect(cx - 25, cy + 45, 50, 16)
        painter.drawRect(text_rect)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(text_rect, Qt.AlignCenter, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            col = event.x() // CELL_SIZE
            row = event.y() // CELL_SIZE
            
            if 0 <= col < COLS and 0 <= row < ROWS:
                tile = self.tiles[row][col]
                
                if tile.is_river:
                    if not tile.building:
                        self.show_bridge_menu(event.pos(), col, row)
                    return
                
                if tile.is_blocked:
                    print(f"Клетка {col},{row} заблокирована рекой (нет моста)")
                    return

                if not tile.building:
                    self.show_build_menu(event.pos(), col, row)
                elif tile.turns_left == 0:
                    self.show_action_menu(event.pos(), col, row)
                else:
                    print(f"Клетка {col},{row} ещё строится")

    def show_bridge_menu(self, pos, col, row):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #222; color: white; padding: 5px; } "
                           "QMenu::item { padding: 5px 20px; } "
                           "QMenu::item:selected { background-color: #444; } "
                           "QMenu::item:disabled { color: #888; }")
        
        action_bridge = QAction("Построить: Мост (2 дер)", self)
        action_bridge.triggered.connect(lambda: self.start_building(col, row, "bridge"))
        
        if not self.game_window.tech_page.card_bridge.is_researched:
            action_bridge.setEnabled(False)
            action_bridge.setText("Мост (требуется технология)")
            
        menu.addAction(action_bridge)
        menu.exec_(self.mapToGlobal(pos))

    def show_build_menu(self, pos, col, row):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #222; color: white; padding: 5px; } "
                           "QMenu::item { padding: 5px 20px; } "
                           "QMenu::item:selected { background-color: #444; } "
                           "QMenu::item:disabled { color: #888; }")
        
        action_house = QAction("Построить: Обычный дом (1 дер, 1 кирп)", self)
        action_house.triggered.connect(lambda: self.start_building(col, row, "house"))
        menu.addAction(action_house)
        
        action_panel = QAction("Построить: Панельный дом (5 кирп, 1 мет, 1 мед)", self)
        action_panel.triggered.connect(lambda: self.start_building(col, row, "panel"))
        
        if not self.game_window.tech_page.card_panel.is_researched:
            action_panel.setEnabled(False)
            action_panel.setText("Панельный дом (требуется технология)")
            
        menu.addAction(action_panel)
        menu.exec_(self.mapToGlobal(pos))

    def show_action_menu(self, pos, col, row):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #222; color: white; padding: 5px; } "
                           "QMenu::item { padding: 5px 20px; } "
                           "QMenu::item:selected { background-color: #444; } "
                           "QMenu::item:disabled { color: #888; }")
        
        tile = self.tiles[row][col]
        
        if tile.building == "bridge":
            action_demolish = QAction("Снести мост (нужна 1 взрывчатка)", self)
            action_demolish.triggered.connect(lambda: self.demolish_building(col, row))
            has_explosive = any(chip.resource_type == "explosive" for chip in self.game_window.resources_page.chips)
            if not has_explosive:
                action_demolish.setEnabled(False)
                action_demolish.setText("Снести (нет взрывчатки)")
            menu.addAction(action_demolish)
            menu.exec_(self.mapToGlobal(pos))
            return

        capacity = 10 if tile.building == "house" else 100
        
        free_spots = capacity - tile.residents
        if free_spots > 0:
            action_settle = QAction(f"Заселить (свободно {free_spots} мест)", self)
            action_settle.triggered.connect(lambda: self.settle_house(col, row))
            menu.addAction(action_settle)
        else:
            action_settle = QAction("Заселить (дом полон)", self)
            action_settle.setEnabled(False)
            menu.addAction(action_settle)
            
        action_demolish = QAction("Снести (нужна 1 взрывчатка)", self)
        action_demolish.triggered.connect(lambda: self.demolish_building(col, row))
        
        has_explosive = any(chip.resource_type == "explosive" for chip in self.game_window.resources_page.chips)
        if not has_explosive:
            action_demolish.setEnabled(False)
            action_demolish.setText("Снести (нет взрывчатки)")
            
        menu.addAction(action_demolish)
        menu.exec_(self.mapToGlobal(pos))

    def start_building(self, col, row, building_type):
        tile = self.tiles[row][col]
        
        if building_type == "house":
            cost = {"wood": 1, "brick": 1}
            turns = 1
        elif building_type == "panel":
            if not self.game_window.tech_page.card_panel.is_researched:
                return
            cost = {"brick": 5, "metal": 1, "copper": 1}
            turns = 2
        elif building_type == "bridge":
            if not self.game_window.tech_page.card_bridge.is_researched:
                return
            cost = {"wood": 2}
            turns = 1
        else:
            return

        if self.game_window.resources_page.consume_resources(cost):
            tile.building = building_type
            tile.turns_left = turns
            tile.residents = 0
            self.update_blocked_state()
            self.update()

    def settle_house(self, col, row):
        tile = self.tiles[row][col]
        capacity = 10 if tile.building == "house" else 100
        free_spots = capacity - tile.residents
        
        if tile.building and free_spots > 0:
            to_settle = min(free_spots, capacity) 
            tile.residents += to_settle
            self.game_window.population += to_settle
            self.game_window.update_population_label()
            self.update()

    def demolish_building(self, col, row):
        tile = self.tiles[row][col]
        
        if not self.game_window.resources_page.consume_resources({"explosive": 1}):
            return
            
        # Запоминаем, сколько людей осталось без дома
        homeless = tile.residents
        
        # Уничтожаем здание
        tile.building = None
        tile.turns_left = 0
        tile.residents = 0
        
        if homeless > 0:
            # Собираем все свободные места в других домах
            available_spots = []
            for r in range(ROWS):
                for c in range(COLS):
                    t = self.tiles[r][c]
                    if t.building and t.turns_left == 0 and not (r == row and c == col):
                        capacity = 10 if t.building == "house" else 100
                        free = capacity - t.residents
                        if free > 0:
                            available_spots.append((t, free))
            
            # Сортируем по убыванию свободных мест
            available_spots.sort(key=lambda x: x[1], reverse=True)
            
            # Рассаживаем
            for t, free in available_spots:
                if homeless <= 0:
                    break
                take = min(homeless, free)
                t.residents += take
                homeless -= take
                # Возвращаем в общий счётчик тех, кто переселился (они остались в городе)
                # (поскольку они уже были учтены ранее, мы просто не вычитаем их)
            
            # ВАЖНО: вычитаем из населения только тех, кто ушёл из города (homeless)
            if homeless > 0:
                self.game_window.population -= homeless
                if self.game_window.population < 0:
                    self.game_window.population = 0
                    
            self.game_window.update_population_label()

        self.update_blocked_state()
        self.update()

    def process_turn(self):
        need_update = False
        for row in range(ROWS):
            for col in range(COLS):
                tile = self.tiles[row][col]
                if tile.building and tile.turns_left > 0:
                    tile.turns_left -= 1
                    need_update = True
        if need_update:
            self.update()
            self.update_blocked_state()


class TechCard(QWidget):
    def __init__(self, title, cost, is_researched=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.cost = cost
        self.is_researched = is_researched
        self.setFixedSize(600, 100)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_researched(self, status):
        self.is_researched = status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.is_researched:
            border_color = QColor(60, 180, 60)
            text_color = QColor(100, 220, 100)
            bg_color = QColor(20, 40, 20, 200)
        else:
            border_color = QColor(180, 40, 40)
            text_color = QColor(220, 80, 80)
            bg_color = QColor(40, 10, 10, 200)

        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())

        pen = QPen(border_color)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(2, 2, self.width() - 4, self.height() - 4)

        font = QFont("Arial", 18, QFont.Bold)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(QRect(20, 15, 450, 50), Qt.AlignLeft | Qt.AlignVCenter, self.title)

        font_cost = QFont("Arial", 18)
        painter.setFont(font_cost)
        painter.drawText(QRect(470, 15, 110, 50), Qt.AlignRight | Qt.AlignVCenter, str(self.cost))


class TechTreeWidget(QWidget):
    def __init__(self, game_window):
        super().__init__()
        self.game_window = game_window
        self.setFixedSize(FIELD_W, FIELD_H)
        self.setStyleSheet("background-color: #111111;")

        self.card_house = TechCard("Строительство", 0, is_researched=True, parent=self)
        self.card_house.move(100, 150)

        self.card_panel = TechCard("Панельные дома", 5, is_researched=False, parent=self)
        self.card_panel.move(800, 150)

        self.card_bridge = TechCard("Строительство мостов", 3, is_researched=False, parent=self)
        self.card_bridge.move(800, 350)

        self.btn_debug = QPushButton("DEBUG: Исследовать всё", self)
        self.btn_debug.setGeometry(100, 500, 400, 50)
        self.btn_debug.clicked.connect(self.debug_research)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        start_x = self.card_house.x() + self.card_house.width()
        start_y = self.card_house.y() + self.card_house.height() // 2
        end_x = self.card_panel.x()
        end_y = self.card_panel.y() + self.card_panel.height() // 2

        line_color = QColor(60, 180, 60) if self.card_house.is_researched else QColor(180, 40, 40)
        pen = QPen(line_color)
        pen.setWidth(4)
        painter.setPen(pen)

        path = QPainterPath()
        path.moveTo(start_x, start_y)
        mid_x = start_x + 50
        path.lineTo(mid_x, start_y)
        path.lineTo(mid_x, end_y)
        path.lineTo(end_x, end_y)
        painter.drawPath(path)

        end_x2 = self.card_bridge.x()
        end_y2 = self.card_bridge.y() + self.card_bridge.height() // 2

        path2 = QPainterPath()
        path2.moveTo(start_x, start_y)
        path2.lineTo(mid_x, start_y)
        path2.lineTo(mid_x, end_y2)
        path2.lineTo(end_x2, end_y2)
        painter.drawPath(path2)

        super().paintEvent(event)

    def debug_research(self):
        self.card_panel.set_researched(True)
        self.card_bridge.set_researched(True)
        self.update()

    def check_turn_unlocks(self, turn):
        if turn >= 5 and not self.card_panel.is_researched:
            self.card_panel.set_researched(True)
            self.update()
        if turn >= 3 and not self.card_bridge.is_researched:
            self.card_bridge.set_researched(True)
            self.update()


class ResourceChip(QWidget):
    def __init__(self, resource_type="electricity", parent=None):
        super().__init__(parent)
        self.resource_type = resource_type
        self.setFixedSize(160, 160)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        colors = {
            "electricity": QColor(255, 215, 0),
            "metal": QColor(150, 150, 150),
            "wood": QColor(139, 69, 19),
            "brick": QColor(205, 92, 92),
            "copper": QColor(184, 115, 51),
            "explosive": QColor(220, 20, 20),
        }
        
        border_color = colors.get(self.resource_type, QColor(0, 0, 0))

        painter.setBrush(QColor(255, 255, 255))
        pen = QPen(border_color)
        pen.setWidth(6)
        painter.setPen(pen)
        painter.drawEllipse(3, 3, 154, 154)

        if self.resource_type == "electricity":
            self.draw_electricity(painter)
        elif self.resource_type == "metal":
            self.draw_metal(painter)
        elif self.resource_type == "wood":
            self.draw_wood(painter)
        elif self.resource_type == "brick":
            self.draw_brick(painter)
        elif self.resource_type == "copper":
            self.draw_copper(painter)
        elif self.resource_type == "explosive":
            self.draw_explosive(painter)

    def draw_electricity(self, painter):
        lightning = QPolygonF([
            QPointF(90, 35), QPointF(60, 85), QPointF(80, 85),
            QPointF(70, 125), QPointF(105, 75), QPointF(85, 75)
        ])
        painter.setBrush(QColor(255, 215, 0))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(lightning)
        
        pen_lightning = QPen(QColor(200, 160, 0))
        pen_lightning.setWidth(2)
        painter.setPen(pen_lightning)
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(lightning)

    def draw_metal(self, painter):
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.setBrush(Qt.NoBrush)

        top_face = QPolygonF([QPointF(40, 70), QPointF(80, 40), QPointF(120, 70), QPointF(80, 100)])
        painter.setBrush(QColor(50, 50, 50))
        painter.drawPolygon(top_face)

        left_face = QPolygonF([QPointF(40, 70), QPointF(80, 100), QPointF(80, 120), QPointF(40, 90)])
        painter.setBrush(QColor(30, 30, 30))
        painter.drawPolygon(left_face)

        right_face = QPolygonF([QPointF(80, 100), QPointF(120, 70), QPointF(120, 90), QPointF(80, 120)])
        painter.setBrush(QColor(70, 70, 70))
        painter.drawPolygon(right_face)

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(50, 75, 70, 90)
        painter.drawLine(55, 70, 75, 85)
        painter.drawLine(90, 85, 110, 70)
        painter.drawLine(95, 90, 115, 75)

    def draw_wood(self, painter):
        painter.setPen(QPen(QColor(80, 40, 10), 3))
        painter.setBrush(QColor(101, 67, 33))
        painter.drawEllipse(40, 40, 80, 80)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(210, 180, 140))
        painter.drawEllipse(46, 46, 68, 68)
        
        painter.setBrush(Qt.NoBrush)
        pen_rings = QPen(QColor(139, 90, 43), 2)
        painter.setPen(pen_rings)
        painter.drawEllipse(55, 55, 50, 50)
        painter.drawEllipse(65, 65, 30, 30)
        painter.drawEllipse(73, 73, 14, 14)

    def draw_brick(self, painter):
        painter.setPen(QPen(QColor(50, 20, 20), 2))
        
        painter.setBrush(QColor(178, 34, 34))
        painter.drawRect(60, 40, 40, 20)
        
        painter.setBrush(QColor(165, 42, 42))
        painter.drawRect(40, 65, 35, 20)
        
        painter.setBrush(QColor(178, 34, 34))
        painter.drawRect(80, 65, 40, 20)
        
        painter.setPen(QPen(QColor(255, 240, 240), 2))
        painter.drawLine(60, 60, 100, 60)
        painter.drawLine(75, 65, 75, 85)
        painter.drawLine(60, 40, 60, 60)
        painter.drawLine(100, 40, 100, 60)

    def draw_copper(self, painter):
        painter.setPen(QPen(QColor(80, 40, 10), 3))
        painter.setBrush(Qt.NoBrush)

        top_face = QPolygonF([QPointF(40, 70), QPointF(80, 40), QPointF(120, 70), QPointF(80, 100)])
        painter.setBrush(QColor(184, 115, 51))
        painter.drawPolygon(top_face)

        left_face = QPolygonF([QPointF(40, 70), QPointF(80, 100), QPointF(80, 120), QPointF(40, 90)])
        painter.setBrush(QColor(150, 80, 30))
        painter.drawPolygon(left_face)

        right_face = QPolygonF([QPointF(80, 100), QPointF(120, 70), QPointF(120, 90), QPointF(80, 120)])
        painter.setBrush(QColor(210, 140, 70))
        painter.drawPolygon(right_face)

        painter.setPen(QPen(QColor(255, 200, 150), 2))
        painter.drawLine(50, 75, 70, 90)
        painter.drawLine(90, 85, 110, 70)

    def draw_explosive(self, painter):
        painter.setPen(QPen(QColor(50, 0, 0), 2))
        painter.setBrush(QColor(200, 30, 30))
        
        painter.drawRect(55, 50, 15, 60)
        painter.drawRect(75, 50, 15, 60)
        painter.drawRect(95, 50, 15, 60)
        
        painter.setBrush(QColor(0, 0, 0))
        painter.drawRect(53, 65, 60, 6)
        painter.drawRect(53, 85, 60, 6)
        
        painter.setPen(QPen(QColor(100, 50, 0), 3))
        path = QPainterPath()
        path.moveTo(95, 50)
        path.quadTo(110, 30, 90, 20)
        painter.drawPath(path)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 165, 0))
        painter.drawEllipse(85, 15, 10, 10)
        painter.setBrush(QColor(255, 255, 0))
        painter.drawEllipse(88, 18, 4, 4)


class ResourceGridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(FIELD_W, FIELD_H)
        
        self.chips = []
        
        resources = [
            ("electricity", 0),
            ("metal", 1),
            ("wood", 2),
            ("brick", 3),
            ("copper", 4),
        ]

        for res_type, row in resources:
            for col in range(7): 
                chip = ResourceChip(res_type, self)
                self.place_chip(chip, col, row)
                self.chips.append(chip)
                
        for col in range(7, 10):
            chip = ResourceChip("explosive", self)
            self.place_chip(chip, col, 4)
            self.chips.append(chip)

    def place_chip(self, chip, col, row):
        x = col * CELL_SIZE + 10
        y = row * CELL_SIZE + 10
        chip.move(x, y)

    def consume_resources(self, cost_dict):
        current = {}
        for chip in self.chips:
            current[chip.resource_type] = current.get(chip.resource_type, 0) + 1
            
        for res, amount in cost_dict.items():
            if current.get(res, 0) < amount:
                return False
                
        to_remove = []
        for res, amount in cost_dict.items():
            removed = 0
            for chip in list(self.chips):
                if chip.resource_type == res and removed < amount:
                    to_remove.append(chip)
                    self.chips.remove(chip)
                    removed += 1
                    
        for chip in to_remove:
            chip.deleteLater()
            
        return True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)

        x = 0
        while x <= self.width():
            painter.drawLine(x, 0, x, self.height())
            x += CELL_SIZE

        y = 0
        while y <= self.height():
            painter.drawLine(0, y, self.width(), y)
            y += CELL_SIZE


class GameWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Градостроительная игра")
        self.setFixedSize(FIELD_W, FIELD_H + MENU_H)

        self.turn = 1
        self.population = 0 

        self.stack = QStackedWidget()

        city_page = QWidget()
        city_layout = QVBoxLayout(city_page)
        city_layout.setContentsMargins(0, 0, 0, 0)
        city_layout.setSpacing(0)
        self.grid = GridWidget(self)
        city_layout.addWidget(self.grid)

        self.resources_page = ResourceGridWidget()
        self.tech_page = TechTreeWidget(self)

        self.stack.addWidget(city_page)        
        self.stack.addWidget(self.resources_page) 
        self.stack.addWidget(self.tech_page)   

        menu = QWidget()
        menu.setFixedSize(FIELD_W, MENU_H)
        menu_layout = QHBoxLayout(menu)
        menu_layout.setContentsMargins(10, 5, 10, 5)
        menu_layout.setSpacing(10)

        self.btn_city = QPushButton("Город")
        self.btn_resources = QPushButton("Ресурсы")
        self.btn_tech = QPushButton("Технологии")
        for b in (self.btn_city, self.btn_resources, self.btn_tech):
            b.setFixedHeight(MENU_H - 20)
            b.setMinimumWidth(160)
            b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            menu_layout.addWidget(b)

        self.btn_city.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_resources.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_tech.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        menu_layout.addStretch(1)

        font = QFont()
        font.setPointSize(14)
        font.setBold(True)

        self.pop_label = QLabel(f"Население: {self.population} чел.")
        self.pop_label.setAlignment(Qt.AlignCenter)
        self.pop_label.setFont(font)
        self.pop_label.setFixedHeight(MENU_H - 20)
        menu_layout.addWidget(self.pop_label)

        self.turn_label = QLabel(f"Ход: {self.turn}")
        self.turn_label.setAlignment(Qt.AlignCenter)
        self.turn_label.setFont(font)
        self.turn_label.setFixedHeight(MENU_H - 20)
        menu_layout.addWidget(self.turn_label)

        menu_layout.addStretch(1)

        self.btn_next_turn = QPushButton("Следующий ход")
        self.btn_next_turn.setFixedHeight(MENU_H - 20)
        self.btn_next_turn.setMinimumWidth(200)
        self.btn_next_turn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_next_turn.clicked.connect(self.next_turn)
        menu_layout.addWidget(self.btn_next_turn)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.stack)
        main_layout.addWidget(menu)

    def update_population_label(self):
        self.pop_label.setText(f"Население: {self.population} чел.")

    def next_turn(self):
        self.turn += 1
        self.turn_label.setText(f"Ход: {self.turn}")
        self.grid.process_turn() 
        self.tech_page.check_turn_unlocks(self.turn)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec_())
    # добавить инфраструктуру (школы, заводы, магазины, рабочие места), добавить возможность сносить мосты, добавить политику, вкладку идеологии и систему денег, 
