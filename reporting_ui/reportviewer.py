# -*- coding: utf-8 -*-
"""

"""

from externals.formlayout.formlayout import (QDialog, QWebView, QUrl, QVBoxLayout,
                                             QDialogButtonBox, QTextEdit, QFont, Qt, Signal)

class ReportViewer(QDialog):
    def __init__(self, url, parent=None):
        super(ReportViewer, self).__init__(parent)
        l = QVBoxLayout(self)
        w = QWebView()
        l.addWidget(w)
        w.load(QUrl(url))

        bb = QDialogButtonBox(QDialogButtonBox.Close)
        l.addWidget(bb)

        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)
        

class ComputationProgressViewer(QDialog):
    append = Signal(str)
    def __init__(self, parent=None):
        super(ComputationProgressViewer, self).__init__(parent)
        l = QVBoxLayout(self)
        self.tv = QTextEdit(readOnly=True)
        
        font = QFont("Courier New")
        font.setFixedPitch(True)
        self.tv.setFont(font)
        
        self.resize(800,600)
        l.addWidget(self.tv)

        bb = QDialogButtonBox(QDialogButtonBox.Close)
        l.addWidget(bb)
        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)

        # we use a queued connection since a write may come from another thread
        self.append.connect(self.tv.append, type=Qt.QueuedConnection)

    def write(self, value):
        self.append.emit(value)

    
