from PySide import QtGui, QtCore
import db_helper

class ChartItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent, provider):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self.series_provider = provider
        self.parent = parent
        
    def paint(self, painter, option, index):
        option_v4 = QtGui.QStyleOptionViewItemV4(option)
        column = self.parent.header().visualIndex(index.column())
        
        if column == 0: option_v4.viewItemPosition = QtGui.QStyleOptionViewItemV4.Beginning	
        elif column == index.model().columnCount() - 1 : option_v4.viewItemPosition = QtGui.QStyleOptionViewItemV4.End
        else: option_v4.viewItemPosition = QtGui.QStyleOptionViewItemV4.Middle

        #QtGui.QStyledItemDelegate.paint(self, painter, option_v4, index)
        self.parent.style().drawControl(QtGui.QStyle.CE_ItemViewItem, option_v4, painter, self.parent)
        
        values = self.series_provider(index.row())

        if len(values) == 0: return
        
        max_y = max(values)
        min_y = min(values)
        points = []

        color = QtGui.QColor("darkGray")
        bg_color = QtGui.QColor("lightGray")

        if len(values) > 1: 
            if values[-1] > values[-2]:
                color = QtGui.QColor("red")
                bg_color = QtGui.QColor("lightPink")
            else:
                color = QtGui.QColor("darkGreen")
                bg_color = QtGui.QColor("lightGreen")

            for i, value in enumerate(values):
                x = i * option.rect.width() / (len(values) - 1)
                y = (value - min_y) * (option.rect.height() - 2) / (max_y - min_y)
                points.append(QtCore.QPoint(x + option.rect.x(), option.rect.y() + option.rect.height() - y - 1))
        else:
            points.append(QtCore.QPoint(option.rect.x(), option.rect.y() + 0.5 * option.rect.height()))
            points.append(QtCore.QPoint(option.rect.x() + option.rect.width(), option.rect.y() + 0.5 * option.rect.height()))

        path = QtGui.QPainterPath()

        path.moveTo(option.rect.x() + option.rect.width(), option.rect.y() + option.rect.height())
        path.lineTo(option.rect.x(), option.rect.y() + option.rect.height())

        for point in points:
            path.lineTo(point)

        path.closeSubpath()

        painter.save()
        painter.setRenderHints(QtGui.QPainter.Antialiasing)
        painter.setClipRect(option.rect)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(bg_color))
        painter.drawPath(path)

        painter.setPen(color)
        painter.drawPolyline(points)
        painter.restore()
        
        
class ChartDataProvider(): 
    def __init__(self):
        self.series = {}
        self.row2asin = {}

    def SetRow2Asin(self, row, asin):
        self.row2asin[row] = asin

    def Update(self):
        self.series = {}
        items = db_helper.GetAllItems()

        for item in items:
            self.series[item[1]] = db_helper.GetNLastPriceChanges(item[1], 5)

    def GetData(self, row_index):
        return self.series[self.row2asin[row_index]]

    def __call__(self, row_index):
        return self.GetData(row_index)