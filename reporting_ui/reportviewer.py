# -*- coding: utf-8 -*-
"""

"""

from externals.formlayout.formlayout import QDialog, QWebView, QUrl, QVBoxLayout, QDialogButtonBox


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
        
