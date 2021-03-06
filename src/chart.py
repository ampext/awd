from PySide import QtGui, QtCore
import db
import defaults

class ChartItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

        self.parent = parent

        self.neutralLineColor = defaults.GetNeutralLineColor()
        self.neutralFillColor = defaults.GetDefaultNeutralFillColor()

        self.upLineColor = defaults.GetUpLineColor()
        self.upFillColor = defaults.GetUpFillColor()

        self.downLineColor = defaults.GetDownLineColor()
        self.downFillColor = defaults.GetDownFillColor()
        
    def paint(self, painter, option, index):
        option_v4 = QtGui.QStyleOptionViewItemV4(option)
        column = self.parent.header().visualIndex(index.column())
        
        if column == 0: option_v4.viewItemPosition = QtGui.QStyleOptionViewItemV4.Beginning	
        elif column == index.model().columnCount() - 1 : option_v4.viewItemPosition = QtGui.QStyleOptionViewItemV4.End
        else: option_v4.viewItemPosition = QtGui.QStyleOptionViewItemV4.Middle

        #QtGui.QStyledItemDelegate.paint(self, painter, option_v4, index)
        self.parent.style().drawControl(QtGui.QStyle.CE_ItemViewItem, option_v4, painter, self.parent)
        
        if not index.isValid() or index.column() != index.model().chartColumn(): return
        
        values = index.model().data(index, QtCore.Qt.DisplayRole)

        if not values or len(values) == 0: return
        
        max_y = max(values)
        min_y = min(values)
        points = []

        color = self.neutralLineColor
        bg_color =self.neutralFillColor

        if len(values) > 1: 
            if values[-1] > values[-2]:
                color = self.upLineColor
                bg_color = self.upFillColor
            else:
                color = self.downLineColor
                bg_color = self.downFillColor

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

    def SetUpLineColor(self, color):
        self.upLineColor = color

    def GetUpLineColor(self):
        return self.upLineColor

    def SetDownLineColor(self, color):
        self.downLineColor = color

    def GetDownLineColor(self):
        return self.downLineColor

    def SetNeutralLineColor(self, color):
        self.neutralLineColor = color

    def GetNeutralLineColor(self):
        return self.neutralLineColor
        
    def SetUpFillColor(self, color):
        self.upFillColor = color

    def GetUpFillColor(self):
        return self.upFillColor

    def SetDownFillColor(self, color):
        self.downFillColor = color

    def GetDownFillColor(self):
        return self.downFillColor

    def SetNeutralFillColor(self, color):
        self.neutralFillColor = color

    def GetNeutralFillColor(self):
        return self.neutralFillColor