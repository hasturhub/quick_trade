import mmap
import itertools
import asyncio
import math
import signal
import time
from datetime import datetime, timezone, timedelta
import os
import random
from ib_async import *
from var_dump import var_dump
#import praw
import sys

# handle ctr + c
def signal_handler(sig, frame):
    print("sys.exit")
    ib.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

shm = mmap.mmap(0, 64 * 64, 'AHK')

# tws api init
ib = IB()
try:
    ib.connect('127.0.0.1', 7497, clientId=0, readonly=True)
except Exception:
    print('TWS connect failed!')
    exit()

ib.RaiseRequestErrors = False
# handle some tws errors
def ib_error(ReqId:int, ErrorCode:int, ErrorString:str, Contract):
    if ErrorCode == 200: return # no sec def error is always verbose
    print('Caught error (' + str(ErrorCode) + ')') 

def ib_pos(p):
    # update positions
    for s in syml_dict.values():
        if s.shadow: continue
        if s.ct_id == p.contract.conId:
            s.pos = p.position
            s.pos_avg_cost = p.avgCost
            if s.ct_type == 'O': # tws sends 60 cents as 60.0 for options
                s.pos_avg_cost = p.avgCost / 100

            if s.target == s:
                s.ladder_widget.update()
            return

ib.errorEvent    += ib_error
ib.positionEvent += ib_pos

import win32gui, win32api
import win32con

from PyQt6.QtCore import QT_VERSION_STR
from PyQt6.QtCore import PYQT_VERSION_STR

print(QT_VERSION_STR)
print(PYQT_VERSION_STR)

from PyQt6.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QLineEdit, QListWidget, QListWidgetItem
from PyQt6.QtGui import QFont, QPainter, QColor, QStaticText, QFontMetrics, QTransform, QPixmap, QPainterPath, QImage, QRegularExpressionValidator, QPen, QIcon, QRadialGradient, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QBasicTimer, pyqtSignal, QSize, QThread, QPoint, QPointF, pyqtSignal, pyqtSlot, QRect, QRegularExpression, QTimer, QDateTime, QEvent

# globals

syml_dict = { } # tws_Symbol quick lookup of all instruments, keys are ct_str
month_array = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
today = datetime.now(timezone.utc)

# panels for option switcher, advanced controls, fill details
class floating_panel:

    ladder_widget = None

    def prepare(self, *args):
        P = self
        L = self.ladder_widget
        
        if P.name == 'opt_switcher':

            pm = P.graphics['back'][0]
            pm.fill(QColor(39, 40, 34, 255))
            P.colrects = { 'back': P.colrects['back'] }
            
            T = tws_Symbol.target
            if not T:
                P.colrects['back'] = back 
                return

            if T.ct_type == 'O':
                T = T.parent

            qp = QPainter()
            qp.begin(pm)
            tl = T.opt_list
            
            _month_array = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUNE', 'JULY', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']
            font   = QFont("Consolas", 11)
            font_b = QFont("Consolas", 11, QFont.Weight.DemiBold)
            font.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)
            font_b.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)

            qp.setFont(font_b)
            br_year  = qp.boundingRect(L.blank_r, 0, '\'99')
            br_month = qp.boundingRect(L.blank_r, 0, 'JUNE')
            br_day   = qp.boundingRect(L.blank_r, 0, '31')
            br_type  = qp.boundingRect(L.blank_r, 0, 'C')

            if P.offset < 0: 
                P.offset = 0

            y = 0 - P.offset
            y_off = 0
            
            for i, o in enumerate(tl):
                qp.setPen(QColor(240, 240, 240))
                if not i % 2:
                    qp.fillRect(0, y, P.w, P.row_h, QColor(50, 50, 50))
                    
                y_off = y + br_year.height() + 4
                splt = o.ct_str.split(',')
                year  = '\'' + splt[2] 
                month = _month_array[int(splt[3]) - 1]
                day   = splt[4]
                pc    = splt[5]
                price = splt[6]

                qp.setPen(QColor(240, 240, 240))
                qp.setFont(font)
                x_off = 4                      ; qp.drawText(x_off, y_off - 2, year)
                x_off += br_year.width()  + 4  ; qp.drawText(x_off, y_off - 2, day)
                x_off += br_day.width()   + 4  ; qp.drawText(x_off, y_off - 2, month)
                qp.setFont(font_b)
                x_off += br_month.width() + 6  ; qp.drawText(x_off, y_off - 2, price)
                x_off = P.w - br_type.width() - 16 ; qp.drawText(x_off, y_off - 2, pc)
                if o.starred:
                    qp.setPen(QColor(239,175,212))
                    qp.drawText(P.w - 12, y_off - 4, '*')
                if o.shadow: qp.setPen(QColor(255,155,255,40)) ; qp.drawText(P.w - 12, y_off + 10, '\"')

                top_y = P.y + y
                bot_y = P.y + y + P.row_h

                if bot_y <= P.y or top_y >= P.y + P.h: # fully out of bounds
                    pass
                elif top_y >= P.y and bot_y <= P.y + P.h: # fully in bounds
                    P.colrects[o.ct_str] = [ P.x, top_y, P.w, P.row_h ] 
                else:
                    if top_y < P.y: # top above bounds, else bottom below bounds
                        dif = P.y - top_y
                        P.colrects[o.ct_str] = [ P.x, P.y, P.w, P.row_h - dif ] 
                    else:
                        P.colrects[o.ct_str] = [ P.x, top_y, P.w, P.y + P.h - top_y ] 

                y += P.row_h
                if i + 1 == len(tl) and i % 2:
                    qp.fillRect(0, y, P.w, P.row_h, QColor(50, 50, 50))
                
                if y > P.y + P.h: break
                
            qp.end()

        if P.name == 'fill_display':
            tl = []
            if not len(args): # use last trade list to update display
                if not len(P._trade_list): return
                tl = P._trade_list
            else:
                P._trade_list = args[0]
                tl = args[0]
                        
            P.colrects = { 'back' : P.colrects['back'] } # reset col rects

            pm = P.graphics['back'][0]
            pm.fill(QColor(40, 40, 40, 255))

            qp = QPainter()
            qp.begin(pm)
            f = QFont("Consolas", 11)
            f_small = QFont("Arial", 8)
            f_bold = QFont("Consolas", 12, QFont.Weight.DemiBold)
            f.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)
            f_small.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)
            f_bold.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)

            if P.offset < 0: 
                P.offset = 0

            y = 0 - P.offset
            y_off = 0
            for i, t in enumerate(tl):
                qp.setPen(QColor(240, 240, 240))
                y_off = y + 12
                if not i % 2:
                    qp.fillRect(0, y_off - 12, P.w, 16, QColor(50, 50, 50))
                spc = ''
                if t.spc != 'none':
                    spc = t.spc[0].upper()
                short = t.dir[0].upper() + spc 
                qp.setFont(f)
                qp.drawText(QPoint(2, y_off), short)
                fill_str = str(t.size) + '\\' + str(t.filled)
                qp.drawText(QPoint(26, y_off), fill_str)
                br = qp.boundingRect(L.blank_r, 0, fill_str)
                price_str = str(t.price)

                if t.size - t.filled == 0 or t.stts == 'ended':
                    price_str = '@ ' + str(t.avg_price)

                qp.setFont(f_small)
                br = qp.boundingRect(L.blank_r, 0, price_str)
                qp.drawText(QPoint(P.w - br.width() - 4, y_off), price_str)

                y += P.row_h
                if i + 1 == len(tl) and i % 2:
                    qp.fillRect(0, y, P.w, 16, QColor(50, 50, 50))
                    
            qp.end()
        
        if P.name == 'pos_display':
            tl = P.pos 

            pm = P.graphics['back'][0]
            pm.fill(QColor(40, 40, 40, 255))

            qp = QPainter()
            qp.begin(pm)
            f = QFont("Consolas", 11)
            f_small = QFont("Arial", 8)
            f_bold = QFont("Consolas", 12, QFont.Weight.DemiBold)

            if P.offset < 0: 
                P.offset = 0

            y = 0 - P.offset
            y_off = 0
            for i, p in enumerate(tl):
                #var_dump(p)
                qp.setPen(QColor(240, 240, 240))
                y_off = y + 14 
                if not i % 2:
                    qp.fillRect(0, y, P.w, P.row_h, QColor(50, 50, 50))

                if p.position > 0:
                    qp.fillRect(0, y, 14, P.row_h, QColor(116, 170, 4))
                else:
                    qp.fillRect(0, y, 14, P.row_h, QColor(167, 3, 52))
                
                qp.setFont(f)
                qp.drawText(QPoint(16, y_off), p.contract.localSymbol)

                if False:
                    spc = ''
                    if t.spc != 'none':
                        spc = t.spc[0].upper()
                    short = t.dir[0].upper() + spc 
                    qp.setFont(f)
                    qp.drawText(QPoint(2, y_off), short)
                    fill_str = str(t.size) + '\\' + str(t.filled)
                    qp.drawText(QPoint(26, y_off), fill_str)
                    br = qp.boundingRect(L.blank_r, 0, fill_str)
                    price_str = str(t.price)

                    if t.size - t.filled == 0 or t.stts == 'ended':
                        price_str = '@ ' + str(t.avg_price)

                    qp.setFont(f_small)
                    br = qp.boundingRect(L.blank_r, 0, price_str)
                    qp.drawText(QPoint(P.w - br.width() - 4, y_off), price_str)

                y += P.row_h
                if i + 1 == len(tl) and i % 2:
                    qp.fillRect(0, y, P.w, 16, QColor(50, 50, 50))
                    
            qp.end()

    def collision(self, n, E, enum = None):
        P = self
        L = self.ladder_widget

        if P.name == 'fill_display' or P.name == 'pos_display':
            if 'key' in E:
                if enum == Qt.Key.Key_Escape: n = 'out_of_bounds'
                elif enum == Qt.Key.Key_P and P.name == 'pos_display': n = 'out_of_bounds'

            # close the display
            if n == 'out_of_bounds':
                L.activated_floating_panel = None
                L.update() ; return

            if 'scroll' in E and n != 'out_of_bounds':
                if 'up' in E:
                    P.offset -= 12 # px
                else:
                    P.offset += 12
                P.prepare()
                L.update() ; return
        
        if P.name == 'opt_switcher':
            if 'key' in E:
                if enum == Qt.Key.Key_Escape: n = 'out_of_bounds'
                elif enum == Qt.Key.Key_O: n = 'out_of_bounds'

                if P.offset == 0: # 1-4 fake left click on option
                    l  = list(P.colrects)
                    if enum == Qt.Key.Key_1 and len(l) > 1:
                        n = l[1] ; E = 'click' ; enum = Qt.MouseButton.LeftButton
                    elif enum == Qt.Key.Key_2 and len(l) > 2:
                        n = l[2] ; E = 'click' ; enum = Qt.MouseButton.LeftButton
                    elif enum == Qt.Key.Key_3 and len(l) > 3:
                        n = l[3] ; E = 'click' ; enum = Qt.MouseButton.LeftButton
                    elif enum == Qt.Key.Key_4 and len(l) > 4:
                        n = l[4] ; E = 'click' ; enum = Qt.MouseButton.LeftButton

            # close the display
            if n == 'out_of_bounds':
                L.activated_floating_panel = None
                L.update() ; return

            if 'scroll' in E and n != 'out_of_bounds':
                if 'up' in E:
                    P.offset -= 18 # px
                else:
                    P.offset += 18
                P.prepare()
                L.update() ; return
            
            if E == 'click':
                if n == 'back':
                    return
                if enum == Qt.MouseButton.RightButton:
                    for _, s in syml_dict.items():
                        if s.ct_str == n:
                            s.starred ^= True
                            self.prepare()
                            L.update()
                            return
                if enum == Qt.MouseButton.LeftButton:
                    s = tws_Symbol(n, False)
                    s = s.setup()
                    if s:
                        s.snap_offset_mid()
                        tws_Symbol.target = s
                        L.ctrl_form['order_size'].setText(str(s.order_size))
                        
                        L.activated_floating_panel = None
                        L.update()
                    return

    def __init__(self, _n, _x, _y, _w, _h):
        P = self

        # init vars
        P.name = _n

        P.x = _x
        P.y = _y
        P.w = _w
        P.h = _h

        P.colrects = { } # name : rect
        P.graphics  = { } # name : [pm, x, y]

        # setup panel based on name
        if P.name == 'fill_display':
            P.rows = 4
            P.row_h = 16
            P.h = P.row_h * P.rows + int(P.row_h * 0.33)
            pm = QPixmap(QSize(P.w, P.h))
            pm.fill(QColor(40, 40, 40, 255))

            P.colrects['back'] = [ P.x, P.y, P.w, P.h ] 
            P.graphics['back'] = [ pm, P.x, P.y ]
            P._trade_list = []
            P.offset = 0

        if P.name == 'opt_switcher':
            P.rows = 4
            P.row_h = 30
            P.h = P.row_h * P.rows + int(P.row_h * 0.33)
            pm = QPixmap(QSize(P.w, P.h))
            P.offset = 0
            
            P.ls = [] #unused?

            P.colrects['back'] = [ P.x, P.y, P.w, P.h ] 
            P.graphics['back'] = [ pm, P.x, P.y ]
        
        if P.name == 'pos_display':
            P.row_h = 18
            pm = QPixmap(QSize(P.w, P.h))
            pm.fill(QColor(40, 40, 40, 255))

            P.colrects['back'] = [ P.x, P.y, P.w, P.h ] 
            P.graphics['back'] = [ pm, P.x, P.y ]
            P.offset = 0
            P.pos = ib.positions()

class ahkmemWorker(QThread):
    def run(p):
        while True:
            # bytes [0] and [1] are contract flag and order size flag
            shm.seek(0) 
            ct_flag = shm.read(1)
            sz_flag = shm.read(1)
            if ct_flag != b'\x00':
                shm.seek(2) 
                l = shm.find(b'\x00')
                ct_str = shm.read(l - 2).decode('UTF-8')
                
                p.ladder_widget.load_signal.emit(ct_str)
                
                shm.seek(0) 
                shm.write(b'\x00')
            
            if sz_flag != b'\x00':
                shm.seek(2) 
                sz = int.from_bytes(shm.read(8), byteorder='little')

                p.ladder_widget.size_signal.emit(sz)
                
                shm.seek(1) 
                shm.write(b'\x00')

            p.usleep(100) # microseconds
    
    def start_thread(self, w):
        self.name = 'ahk shared memory'
        t = ahkmemWorker(self)
        t.finished.connect(t.deleteLater)
        t.ladder_widget = w
        t.start()
        
        self.thread = t

class ladderWorker(QThread):
    # creates price ladders in background... maybe more later

    def run(p):
        t = p.target
        L = t.ladder_widget

        delay = 100
        start_time = time.time()

        while True: 
            if t.ask != 0 and t.bid != 0:

                mid = ( t.ask + t.bid ) // 2
                print(t.name, '@', t.ask, t.bid)

                li = []

                if mid < 2*100:     # 2
                    li       = [ 1, 2, 5, 10 ]
                elif mid < 20*100:  # 20
                    li       = [ 1, 2, 5, 10, 20 ]
                elif mid < 100*100: # 100
                    li       = [ 1, 2, 5, 10, 20 ]
                elif mid < 200*100: # 200
                    li       = [ 1, 2, 5, 10, 20, 50 ]
                elif mid < 400*100: # 400
                    li       = [ 2, 5, 10, 20, 50, 100 ]
                else:
                    li       = [ 5, 10, 20, 50, 100, 200 ]

                t.ladder_inc = li
                t.ladder_focus_inc = t.ladder_inc[0]

                mid = mid - (mid % t.ladder_focus_inc)
                t.mpl_offset = 999999 - mid - ((L.ladder_rows // 2) * t.ladder_focus_inc)
                t.correct_oob() # TODO: this should run before mpl_offset is set

                if t is tws_Symbol.target:
                    L.update() # NOTE: can't use multiple updates in row

                break

            # after 5 seconds, switch to a 1 second delay
            if delay == 100 and time.time() - start_time > 5:
                delay = 10**6

            p.usleep(delay) # microseconds
    
    def setup(self, s):
        self.name = s.name + ' setup'
        self.target = s
        self.thread = None

    def start_thread(self, task):
        t = ladderWorker(self)
        t.finished.connect(t.deleteLater)

        t.task = task 
        t.target = self.target 
        t.start()

        self.thread = t

class tws_Trade:
    # global bools, algo speed values are 0 -> no algo, 1 -> slow, 2 -> fast
    # TODO: adaptive algo
    glb = { 'algo_speed' : 0, 'all_or_none' : False, 'outside_rth' : True  }

    def status_change(self, t):
        s = self.sym
        L = s.ladder_widget
        if t.orderStatus.status != self.status:
            self.status = t.orderStatus.status

            ts = t.orderStatus.status
            
            # stts stores either 'live', 'ended', or 'working'
            # colors:            blue   red     not disp    gray
            if ts == 'Submitted':
                self.stts = 'live'
            elif ts == 'Cancelled' or ts == 'Filled' or ts == 'ApiCancelled':
                self.stts = 'ended'

                if self.filled == 0:
                    s.trades.remove(self)
                else:
                    sw = s.trades.pop(s.trades.index(self))
                    s.trades_fin.append(sw)
            else:
                self.stts = 'working'

            if s == s.target:
                L.update()

    def fill_event(self, t, f):
        L = self.sym.ladder_widget
        print('fill', f.execution.cumQty)

        self.filled = int(f.execution.cumQty)
        self.avg_price = f.execution.avgPrice
        
        if L.activated_floating_panel and L.activated_floating_panel.name == 'fill_display':
            L.activated_floating_panel.prepare() # update fills

    def __eq__(self, other):
        return self.trade.order == other.trade.order

    def __init__(self, s, o, base_trade, spc):
        L = s.ladder_widget
        self.offset = o

        self.price = L.mpl[o][1]

        # validate order size
        size = L.ctrl_form['order_size'].text()
        if not len(size):  
            return
        elif int(size) <= 0:
            return
        self.size = int(size)

        self.sym = s

        self.filled = 0
        self.avg_price = '0.00'
        
        self.stts = 'working'
        self.dir  = base_trade 
        self.spc  = spc

        order = None
        if spc == 'none':
            if base_trade == 'buy':
                order = LimitOrder('BUY', self.size, float(L.mpl[o][0]))
            elif base_trade == 'sell':
                order = LimitOrder('SELL', self.size, float(L.mpl[o][0]))
        elif spc == 'stp':
            if base_trade == 'buy':
                order = StopOrder('BUY', self.size, float(L.mpl[o][0]))
            elif base_trade == 'sell':
                order = StopOrder('SELL', self.size, float(L.mpl[o][0]))

        if not order:
            return

        if self.glb['all_or_none']:
            order.allOrNone  = True
        if self.glb['outside_rth'] and self.sym.ct_type == 'S':
            order.outsideRth = True

        #order.transmit = False
        
        self.price = order.lmtPrice
        self.aux_price = order.auxPrice
        if self.spc == 'stp':
            self.price = self.aux_price
        self.trade = ib.placeOrder(s.ct, order)
        self.trade.statusEvent += self.status_change
        self.trade.fillEvent += self.fill_event
        
        self.status = self.trade.orderStatus.status
        self.time_created = time.time()
        
        s.trades.append(self)
        L.update()

class tws_Symbol:

    target   = None
    workers  = [] # throw threads in here
    ladder_widget = None
    
    def snap_offset_mid(self):
        t = self
        L = t.ladder_widget
        if t.mpl_offset is not None:
            mid = ( t.ask + t.bid ) // 2
            mid = mid - (mid % t.ladder_focus_inc)
            t.mpl_offset = 999999 - mid - ((L.ladder_rows // 2) * t.ladder_focus_inc)

            t.correct_oob()
    
    def correct_oob(self):
        L = self.ladder_widget
        t = self

        if t.mpl_offset + t.ladder_focus_inc * L.ladder_rows > 999999:
            t.mpl_offset = 999999 - (L.ladder_rows - 1) * t.ladder_focus_inc
        if t.mpl_offset < 0:
            t.mpl_offset = 0

    def update(self, ticker):
        L = self.ladder_widget
        if math.isnan(ticker.ask) or math.isnan(ticker.bid):
            return

        self.ask = int(ticker.ask * 100)
        self.bid = int(ticker.bid * 100)

        if self.ask < 1: # if market closed, tws will send -100
            self.ask = 0 
        if self.bid < 1:
            self.bid = 0 

        if False:
            if not math.isnan(ticker.shortableShares):
                self.shortable_shares = ticker.shortableShares
            else:
                self.shortable_shares = 0
        
        for t in ticker.ticks:
            if t.tickType == 46:
                n = int(t.price)
                if n > 2.5:
                    self.short_fact = 'S'
                elif n > 1.5:
                    self.short_fact = 'H'
                else:
                    self.short_fact = 'N'
            elif t.tickType == 65: # 10 minute vol
                self.volume = t.size
            elif t.tickType == 9: # last close
                self.close = t.price
        # diag
        #self.ask = 4041
        #self.bid = 4001
        self.bid_str = str(self.bid)
        self.ask_str = str(self.ask)
        if not math.isnan(ticker.last):
            self.last = ticker.last

        if self.ask != self.ask_old or self.bid != self.bid_old:
            self.ask_old = self.ask
            self.bid_old = self.bid
            if self.target is self and self.mpl_offset:
                L.update()

    def __init__(self, ct_str, shadow = False, starred = False):
        self.shadow = shadow
        self.ct_str = ct_str
        self.starred = starred # save record to file
        self.pos = 0.0

    def setup(self):
        L = self.ladder_widget
        t = tws_Symbol.target
        ct_str = self.ct_str
        replace_shadow = False
        if ct_str in syml_dict:
            if not syml_dict[ct_str].shadow or self.shadow:
                return syml_dict[ct_str]
            else:
                replace_shadow = True

        ct_pts = ct_str.split(',')

        if ct_pts[1] == 'EQ':
            self.ct_type = 'S'
        elif ct_pts[1] == 'OPT':
            self.ct_type = 'O'
        else:
            return None

        if self.shadow:
            if self.ct_type == 'S':
                self.opt_list = []
            elif self.ct_type == 'O':
                p_str = ct_pts[0] + ',EQ'
                if p_str in syml_dict:
                    self.parent = syml_dict[p_str]
                else:
                    p = tws_Symbol(p_str, True)
                    p = p.setup()
                    self.parent = p

                self.parent.opt_list.append(self)

            syml_dict[ct_str] = self
            return self

        S  = self
        ct = None
        if S.ct_type == 'S':
            ct = Stock(ct_pts[0], 'SMART', 'USD')
            self.name = ct_pts[0]
        elif S.ct_type == 'O':
            p = ct_pts
            ct = Option(p[0], '20'+p[2]+p[3]+p[4], p[6], p[5], exchange='SMART')
            self.name = p[0] + ' ' + p[6] + p[5]  
            self.exp_str = '20' + p[2] + ' ' + month_array[int(p[3]) - 1] + ' ' + p[4]

        if not ct: return None
        qc = ib.qualifyContracts(ct)
        if not len(qc):
            return None
            
        self.ct = ct
        self.ct_id = ct.conId
        
        self.ask = 0
        self.bid = 0

        self.show_last = True

        self.ask_old = -1
        self.bid_old = -1

        self.ladder_inc = []
        self.ladder_focus_inc = None

        self.mpl_offset = None

        self.shortable_shares = 0
        self.short_fact = None
        self.last = 0

        self.opt_list = []
        if self.ct_type == 'S':
            self.order_size = 100 # used to remember order size on switch, never to place!
        else:
            self.order_size = 5

        self.trades = []
        self.trades_fin = []

        self.pos_avg_cost = '0.00'
        
        ib.reqMarketDataType(1)
        if self.ct_type == 'S': # get short avail with 236
            self.ibticker = ib.reqMktData(ct, genericTickList='236,595')
        else:
            self.ibticker = ib.reqMktData(ct)
        self.ibticker.updateEvent += self.update
        
        pos = ib.positions()
        for p in pos:
            if p.contract.conId == self.ct_id:
                self.pos = p.position
                self.pos_avg_cost = p.avgCost
                if self.ct_type == 'O':
                    self.pos_avg_cost = p.avgCost / 100
                break

        th = ladderWorker()
        th.setup(self)
        th.start_thread('default')
        self.workers.append(th)

        self.close = 0
        self.volume = 0

        if self.ct_type == 'S' and replace_shadow: # copy over shadow values
            self.opt_list = syml_dict[ct_str].opt_list 
            self.starred  = syml_dict[ct_str].starred

        if self.ct_type == 'O': # setup parent values, create a shadow parent if needed
            p_str = ct_pts[0] + ',EQ'
            if p_str in syml_dict:
                self.parent = syml_dict[p_str]
            else:
                p = tws_Symbol(p_str, True)
                p = p.setup()
                self.parent = p
                
            if replace_shadow:
                self.starred = syml_dict[ct_str].starred
                l = self.parent.opt_list
                for i in range(len(l)):
                    if l[i].ct_str == ct_str:
                        self.starred = l[i].starred
                        l[i] = self ; break
            else:
                self.parent.opt_list.append(self)
                
        
        self.last_touched  = time.time()
        syml_dict[ct_str]  = self
        return self

class widgetLadder(QWidget):
    
    # globals
    mpl = [] # master price ladder
    mtl = [] # master trade list
    ctrl_form = {}
    
    win_id = 0
    wheel_focus_click = False

    diag_bid_ask = False

    load_signal = pyqtSignal(str)
    size_signal = pyqtSignal(int)

    price_font   = None
    price_font_b = None

    ladder_row_spacing  = 18
    ladder_height       = ladder_row_spacing * 29
    ladder_width        = 200 
    ladder_ctrl_height  = 60 # ladder begins on px 61
    ladder_bot_pane_h   = 20
    ladder_win_height   = ladder_height + ladder_ctrl_height + ladder_bot_pane_h
    ladder_win_width    = 200
    ladder_rows         = 29

    filled_pane_width = 26

    # repaint will set these, used for main thread inputs mostly
    last_ask_pos         = 0
    last_bid_pos         = 0 
    last_price_box_x     = 0
    last_price_box_width = 0
    buy_bxs  = []
    sell_bxs = []
    fill_bxs = []

    @pyqtSlot(int)
    def load_size_slot(self, n):
        if tws_Symbol.target:
            t = tws_Symbol.target
            t.order_size = n
            self.ctrl_form['order_size'].setText(str(n))

    @pyqtSlot(str)
    def load_slot(self, ct_str):
        L = self
        t = tws_Symbol.target
            
        # LOAD
        s = tws_Symbol(ct_str, False)
        s = s.setup()
        if s:
            s.snap_offset_mid()
            tws_Symbol.target = s
            L.ctrl_form['order_size'].setText(str(s.order_size))
            L.update()

    def size_ctrl_submit(self):
        L = self
        t = tws_Symbol.target
        size = L.ctrl_form['order_size'].text()
        
        if t:
            t.order_size = int(size)

        L.ctrl_form['order_size'].clearFocus()

    def trade_check_tick(self):
        #print(random.randrange(1,1000), 'tick')
        L = self
        T = tws_Symbol.target

        ib_trades = ib.openTrades()
        for b in ib_trades:
            for s in syml_dict.values():
                if s.shadow: continue
                for t in s.trades:
                    if b.order.orderId == t.trade.order.orderId:
                        if t.spc == 'stp' and b.order.auxPrice != t.aux_price:
                            t.aux_price = b.order.auxPrice
                            t.price = t.aux_price
                            p = str(t.price)
                            p = p.split('.')
                            if len(p[1]) < 2:
                                p[1] = p[1] + '0'
                            n = int(p[0]) * 100 + int(p[1])
                            t.offset = 999999 - n
                            L.update()
                        elif t.spc != 'stp' and t.price != b.order.lmtPrice:
                            t.price = b.order.lmtPrice
                            p = str(t.price)
                            p = p.split('.')
                            if len(p[1]) < 2:
                                p[1] = p[1] + '0'
                            n = int(p[0]) * 100 + int(p[1])
                            t.offset = 999999 - n
                            L.update()

                        if t.size != b.order.totalQuantity:
                            t.size = int(b.order.totalQuantity)
        
    def __init__(self):
        super().__init__()
        L = self
        
        L.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent) # must do fills

        tws_Symbol.ladder_widget = self
        self.win_id = int(self.winId())

        self.load_signal.connect(self.load_slot)
        self.size_signal.connect(self.load_size_slot)

        self.setGeometry(self.ladder_win_height, 200, 200, self.ladder_win_height)
        self.move(1000, 200)
        self.setWindowTitle('Quick Trader')
        self.show()

        self.timer = QBasicTimer()
        self.timer.start(100, self)
        
        self.trade_check = QTimer(self)
        self.trade_check.timeout.connect(self.trade_check_tick)

        # create master price ladder
        # TODO: low to high instead of high to low
        n_max = int('9999' + '99')
        mpl = [None] * (n_max + 1)

        for i, j in enumerate(mpl):
            nh = n_max // 100
            nl = n_max - nh * 100

            if nl < 10:
                z = '0'
            else:
                z = ''

            mpl[i] = [ str(nh) + '.' + z + str(nl), n_max, nh, nl ]
            
            n_max -= 1
        
        self.mpl = mpl
        
        # font sizes
        L.price_font   = QFont("Arial", 9)
        L.price_font_b = QFont("Arial", 9, QFont.Weight.DemiBold)
        L.ctrl_panel_font = QFont("Consolas", 11)
        L.ctrl_panel_font.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)
        #L.price_font.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)
        #L.price_font_b.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)

        L.bid_hl  = QColor(255,243,133)
        L.ask_hl  = QColor(129,210,125)
        L.last_hl = QColor(255,204,0)

        # pxmaps
        blank_canvas = QPixmap(QSize(9999, 9999))
        L.blank   = blank_canvas
        L.blank_r = blank_canvas.rect()

        self.bt_decor = QPixmap(QSize(L.ladder_width, L.ladder_height))
        self.bt_decor.fill(QColor(240, 240, 240, 255))
        
        self.p_decor = QPixmap(QSize(L.ladder_width, L.ladder_height))
        self.p_decor.fill(QColor(240, 240, 240, 255))

        self.bid_arrow = QPixmap(QSize(16, 16))
        self.bid_arrow.fill(QColor(0, 0, 0, 0))
        self.ask_arrow = QPixmap(QSize(16, 16))
        self.ask_arrow.fill(QColor(0, 0, 0, 0))
        
        self.bot_pane = QPixmap(QSize(L.ladder_win_width, L.ladder_bot_pane_h))
        self.bot_pane.fill(QColor(180, 210, 210, 255))
        
        L.ctrl_panel = QPixmap(QSize(L.ladder_win_width, L.ladder_ctrl_height))
        L.ctrl_panel.fill(QColor(180, 210, 210, 255))
        
        L.mult_trades = QPixmap(QSize(12, 12))
        L.mult_trades.fill(QColor(0, 0, 0, 0))
        L.stop_hex = QPixmap(QSize(L.ladder_row_spacing - 1, L.ladder_row_spacing - 1))
        L.stop_hex.fill(QColor(255, 255, 255, 0))
        
        L.hint_up = QPixmap(QSize(12, 9))
        L.hint_up.fill(QColor(255, 255, 255, 0))
        L.hint_dn = L.hint_up.copy() 
        
        fm = QFontMetrics(L.ctrl_panel_font)
        L.parent_arrow_w = 30
        L.parent_arrow_h = fm.ascent()
        L.parent_arrow = QPixmap(QSize(L.parent_arrow_w, L.parent_arrow_h))
        L.parent_arrow.fill(QColor(0, 0, 0, 0))
        L.last_parent_arrow_w = 0
        
        # order size editor
        ql = QLineEdit(self)
        ql.setFont(QFont("Arial", 10))
        ql.setPlaceholderText('Size')
        ql.setMaxLength(4)
        ql.setMaximumSize(60, 30)
        ql.move(L.ladder_win_width - 64, 4)
        
        rx = QRegularExpression(R'\d+')
        ql.setValidator(QRegularExpressionValidator(rx))
        ql.editingFinished.connect(self.size_ctrl_submit)
        ql.show()
        
        L.ctrl_form['order_size'] = ql
        
        # paint graphics 
        paint = QPainter()
        
        step = L.ladder_row_spacing 
        decor_line_color = QColor(210, 210, 210)
        paint.begin(self.bt_decor)
        if True: # alt styling
            for i in range(L.ladder_rows):
                if i % 2:
                    paint.fillRect(0, i * step, L.ladder_width, step, QColor('#BABABA'))
                else:
                    paint.fillRect(0, i * step, L.ladder_width, step, QColor('#C0C0C0'))
        if False:
            paint.setPen(decor_line_color)
            for i in range(L.ladder_rows):
                paint.drawLine(0, i * step, L.ladder_width, i * step)
        paint.end()
        
        paint.begin(self.p_decor)
        for i in range(L.ladder_rows):
            if i % 2:
                paint.fillRect(0, i * step, L.ladder_width, step, QColor('#D4D5C2'))
            else:
                paint.fillRect(0, i * step, L.ladder_width, step, QColor('#DBDCC8'))
        paint.end()
        
        dark = QColor(220, 220, 230)
        light = QColor(240, 240, 240)
        dark = QColor(100, 100, 140, 70)
        light = QColor(200, 200, 220, 40)
        grad_w = 18
        linearGrad = QLinearGradient(QPointF(0, 0), QPointF(grad_w, 0))
        linearGrad.setColorAt(1, light)
        linearGrad.setColorAt(0, dark)
        
        self.bt_decor_nt = QPixmap(self.bt_decor)
        
        paint.begin(self.bt_decor_nt)
        paint.fillRect(0, 0, grad_w, L.ladder_height, QBrush(linearGrad))
        linearGrad = QLinearGradient(QPointF(L.ladder_width - grad_w, 0), QPointF(L.ladder_width, 0))
        linearGrad.setColorAt(0, light)
        linearGrad.setColorAt(1, dark)
        paint.fillRect(L.ladder_width - grad_w, 0, grad_w, L.ladder_height, QBrush(linearGrad))
        if False:
            paint.setPen(decor_line_color)
            for i in range(L.ladder_rows):
                paint.drawLine(0, i * step, L.ladder_width, i * step)
        paint.end()

        paint.begin(self.bid_arrow)
        #paint.setRenderHint(QPainter.RenderHint.Antialiasing)
        #paint.setPen(Qt.PenStyle.NoPen)
        paint.setBrush(QColor(166, 214, 9, 255))
        paint.setBrush(L.bid_hl)
        #paint.setBrush(QColor(25, 165, 55, 255))
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(12, 8)
        path.lineTo(0, 16)
        path.lineTo(0, 0)
        paint.drawPath(path)
        paint.end()
        
        paint.begin(self.ask_arrow)
        paint.setBrush(QColor(226, 238, 139, 255))
        paint.setBrush(L.ask_hl)
        #paint.setBrush(QColor(255, 210, 80, 255))
        #paint.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(12, 0)
        path.lineTo(0, 8)
        path.lineTo(12, 16)
        path.lineTo(12, 0)
        paint.drawPath(path)
        paint.end()
        
        paint.begin(L.parent_arrow)
        paint.setPen(Qt.PenStyle.NoPen)
        paint.setBrush(QColor(180 - 40, 210 - 40, 210 - 40, 255))
        path = QPainterPath()
        path.moveTo(0, L.parent_arrow_h / 2)
        path.lineTo(8, L.parent_arrow_h)
        path.lineTo(L.parent_arrow_w, L.parent_arrow_h)
        path.lineTo(L.parent_arrow_w, 0)
        path.lineTo(8, 0)
        path.moveTo(0, L.parent_arrow_h / 2)
        paint.drawPath(path)
        paint.end()
        
        paint.begin(L.mult_trades)
        #paint.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint.setFont(QFont("Helvetica", 14, QFont.Weight.Bold))
        paint.setPen(QColor(230, 230, 230))
        paint.drawText(0, 16, '*')
        paint.end()
        
        paint.begin(L.stop_hex)
        d = L.ladder_row_spacing - 1
        L.stop_hex_mid = d // 2
        paint.setPen(Qt.PenStyle.NoPen)
        paint.setBrush(QColor(40, 40, 40, 255))
        
        path = QPainterPath()
        path.moveTo(4, 0)
        path.lineTo(d - 5, 0)
        
        path.lineTo(d, 5)
        path.lineTo(d, d - 4)

        path.lineTo(d, 4)
        path.lineTo(d, d - 5)
        
        path.lineTo(d - 4, d)
        path.lineTo(4, d)
        
        path.lineTo(0, d - 4)
        path.lineTo(0, 4)

        paint.drawPath(path)

        paint.end()
        
        paint.begin(L.hint_up)
        paint.setBrush(QColor(167, 3, 52))
        paint.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(6, 0)
        path.lineTo(0, 9)
        path.lineTo(12, 9)
        path.lineTo(6, 0)
        paint.drawPath(path)
        paint.end()
        
        paint.begin(L.hint_dn)
        paint.setBrush(QColor(167, 3, 52))
        paint.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(6, 9)
        path.lineTo(0, 0)
        path.lineTo(12, 0)
        path.lineTo(6, 9)
        paint.drawPath(path)
        paint.end()

        # init switch buttons in control panel
        L.sbutton_wh = 24
        
        L.sbutton_opt_x = L.ladder_win_width - L.sbutton_wh - 4
        L.sbutton_opt_y = L.ladder_ctrl_height - L.sbutton_wh  - 4
        L.sbutton_opt_pm = QPixmap(QSize(L.sbutton_wh, L.sbutton_wh))
        L.sbutton_opt_pm.fill(QColor(0, 0, 0, 0))
        
        paint.begin(L.sbutton_opt_pm)
        paint.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        paint.setPen(QColor(210,221,146)) ; paint.drawText(1, 20, 'O')

        paint.setFont(QFont("Helvetica", 11, QFont.Weight.Bold))
        paint.setPen(QColor(30,30,30)) ; paint.drawText(6, 22, 'P')

        paint.setFont(QFont("Helvetica", 11, QFont.Weight.Bold))
        paint.setPen(QColor(60,60,60)) ; paint.drawText(15, 16, 'T')
        paint.end()
        
        if False:
            paint.begin(L.sbutton_ctrl_pm)
            paint.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
            paint.setPen(QColor(210,221,146)) ; paint.drawText(1, 20, 'E')

            paint.setFont(QFont("Helvetica", 13, QFont.Weight.Bold))
            paint.setPen(QColor(30,30,30)) ; paint.drawText(11, 20, 'Q')
            paint.end()
        
        L.star = QPixmap.fromImage(QImage('star.png'))
        L.up_arrow = QPixmap.fromImage(QImage('up.png'))
        L.dn_arrow = QPixmap.fromImage(QImage('down.png'))
        
        paint.begin(self.ctrl_panel)
        paint.fillRect(L.sbutton_opt_x, L.sbutton_opt_y, L.sbutton_wh, L.sbutton_wh, QColor(180 - 44, 210 - 44, 210 - 44, 255))
        #paint.fillRect(L.sbutton_ctrl_x, L.sbutton_ctrl_y, L.sbutton_wh, L.sbutton_wh, QColor(180 - 44, 210 - 44, 210 - 44, 255))
        paint.end()
        
        # load save file items
        s = None
        save_file = open('quick_change_helper.save', 'r')
        sf_lines = save_file.readlines()
        for l in sf_lines:
            splt = l.rstrip('\n').split(':')
            key = splt[0]
            val = splt[1]
            if key == 'LAST':
                s = tws_Symbol(val, False)
                s = s.setup()
            elif key == 'OPTH': # option list head
                t = tws_Symbol(val, True)
                t.setup()
            else: # option 
                t = tws_Symbol(val, True, True)
                t.setup()

        if s:
            s.snap_offset_mid()
            tws_Symbol.target = s
            L.ctrl_form['order_size'].setText(str(s.order_size))
        
        th = ahkmemWorker()
        th.start_thread(self)
        tws_Symbol.workers.append(th)

        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus) # needed to grab focus from input box
        
        # floating panels init
        L.activated_floating_panel = None
        floating_panel.ladder_widget = L

        L.fp_width = int(L.ladder_width * 0.9)
        
    def closeEvent(self, event):
        for w in tws_Symbol.workers:
            try:
                w.thread.terminate()
            except:
                pass

        print('exiting')
        # save last open symbol ct_str, save starred options 
        save_str = ''

        for k, s in syml_dict.items():
            if s.ct_type == 'S' and len(s.opt_list):
                save_str += 'OPTH:' + s.ct_str + '\n'
                for o in s.opt_list:
                    if o.starred:
                        save_str += '-:' + o.ct_str + '\n'
        
        if tws_Symbol.target:
            save_str += 'LAST:' + tws_Symbol.target.ct_str + '\n' 

        save_file = open('quick_change_helper.save', 'w')
        save_file.write(save_str)

        time.sleep(0.05) # a bit of time for threads to exit
        event.accept()

    def wheelEvent(self, e):
        t = tws_Symbol.target
        L = self 
        pos = e.position()
        if win32gui.GetForegroundWindow() != self.win_id:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            L.wheel_focus_click = True

        if L.activated_floating_panel:
            P = L.activated_floating_panel
            for n, r in P.colrects.items():
                if pos.x() > r[0] and pos.x() < r[0] + r[2] and pos.y() > r[1] and pos.y() < r[1] + r[3]:
                    if e.angleDelta().y() > 0:
                        P.collision(n, 'scroll_up'); return
                    P.collision(n, 'scroll_down'); return

        if not t or t.mpl_offset is None:
            return

        if pos.y() < L.ladder_ctrl_height or pos.y() > L.ladder_win_height - L.ladder_bot_pane_h:
            return

        # scroll ladder if in proper bounds
        if pos.x() < L.last_price_box_x or pos.x() > L.last_price_box_width + L.last_price_box_x:
            if e.angleDelta().y() > 0:
                t.mpl_offset -= 4 * t.ladder_focus_inc

            elif e.angleDelta().y() < 0:
                t.mpl_offset += 4 * t.ladder_focus_inc

            t.correct_oob()
            self.update()
            return

        # zoom ladder
        i = t.ladder_inc.index(t.ladder_focus_inc)

        if e.angleDelta().y() < 0: # zoom out
            i = t.ladder_inc.index(t.ladder_focus_inc)
            if i + 1 >= len(t.ladder_inc):
                return

            row = int((pos.y() - L.ladder_ctrl_height) / L.ladder_row_spacing)

            new_inc = t.ladder_inc[i+1]
            j = t.mpl_offset + row * t.ladder_focus_inc
            
            modu = L.mpl[j][1] % new_inc
            n = L.mpl[j][1] - modu

            t.ladder_focus_inc = new_inc
            t.mpl_offset = 999999 - n - row * t.ladder_focus_inc

        else: # zoom in
            i = t.ladder_inc.index(t.ladder_focus_inc)
            if i - 1 < 0:
                return

            row = int((pos.y() - L.ladder_ctrl_height) / L.ladder_row_spacing)

            new_inc = t.ladder_inc[i-1]
            j = t.mpl_offset + row * t.ladder_focus_inc

            n = L.mpl[j][1]

            t.mpl_offset = 999999 - ( n - n % new_inc) - row * new_inc 

            t.ladder_focus_inc = new_inc

        t.correct_oob()
        self.update()

    def mouseMoveEvent(self, e):
        pass

    def mousePressEvent(self, e):
        # CLICK
        # TODO: sometimes clicks don't register after focus is lost?
        if self.wheel_focus_click:
            self.wheel_focus_click = False
            return
        
        pos = e.position()
        t = tws_Symbol.target
        L = self

        # check if clicked on a floating panel
        if L.activated_floating_panel:
            P = L.activated_floating_panel
            for n, r in reversed(P.colrects.items()):
                if pos.x() > r[0] and pos.x() < r[0] + r[2] and pos.y() > r[1] and pos.y() < r[1] + r[3]:
                    P.collision(n, 'click', e.button())
                    return

            # clicked outside of floating panel
            P.collision('out_of_bounds', 'click', e.button())
            return
        
        # clicked in top ctrl panel or bottom pane
        if pos.y() < L.ladder_ctrl_height + 1 or pos.y() > L.ladder_win_height - L.ladder_bot_pane_h:
            if t and t.ct_type == 'O':
                if pos.y() > 4 and pos.y() < L.parent_arrow_h + 4 and pos.x() < L.last_parent_arrow_w:
                    # LOAD
                    s = tws_Symbol(t.parent.ct_str, False)
                    s = s.setup()
                    if s:
                        s.snap_offset_mid()
                        tws_Symbol.target = s
                        L.ctrl_form['order_size'].setText(str(s.order_size))

                    L.update() ; return

            if pos.y() > L.sbutton_opt_y and pos.y() < L.sbutton_opt_y + L.sbutton_wh and pos.x() > L.sbutton_opt_x and pos.x() < L.sbutton_opt_x + L.sbutton_wh:
                L.activated_floating_panel = floating_panel('opt_switcher', int(L.ladder_width / 2 - L.fp_width / 2), L.ladder_ctrl_height + 12, L.fp_width, 28 * 5 - 1)
                L.activated_floating_panel.prepare()
                L.update()
            
            return

        # click was in ladder
        if not t or t.mpl_offset is None:
            return

        row = int((pos.y() - L.ladder_ctrl_height) / L.ladder_row_spacing)

        # check if clicked on a fill box
        if e.button() == Qt.MouseButton.LeftButton and pos.x() > L.ladder_win_width - L.filled_pane_width:
            for b in L.fill_bxs:
                if b[4] == row:
                    # create a floating panel with fill data sorted by time created
                    b[1].sort(key=lambda x: x.time_created, reverse=True) 
                    fp_width = L.ladder_win_width - 6 
                    L.activated_floating_panel = floating_panel('fill_display', int(L.ladder_width / 2 - fp_width / 2), L.ladder_ctrl_height + int(L.ladder_height / 2 - 50), fp_width, 100)
                    L.activated_floating_panel.prepare(b[1])
                    L.update()
                    return
        
        # get the order type
        md = app.keyboardModifiers()
        found_trades_to_cancel = False
        on  = 'none'
        spc = 'none'
        if pos.x() < L.last_price_box_x:
            if e.button() == Qt.MouseButton.LeftButton and md == Qt.KeyboardModifier.NoModifier:
                on = 'buy'
                # check for orders to cancel with left click
                for b in L.buy_bxs:
                    if b[4] == row:
                        for r in b[2]:
                            if not r.stts == 'ended':
                                found_trades_to_cancel = True
                                ib.cancelOrder(r.trade.order)
            elif e.button() == Qt.MouseButton.LeftButton and md == Qt.KeyboardModifier.ControlModifier:
                on  = 'buy'
                spc = 'stp'

        elif pos.x() > L.last_price_box_x + L.last_price_box_width and pos.x() < L.ladder_width - L.filled_pane_width:
            if e.button() == Qt.MouseButton.RightButton and md == Qt.KeyboardModifier.NoModifier:
                on = 'sell'
            elif e.button() == Qt.MouseButton.LeftButton and md == Qt.KeyboardModifier.ControlModifier:
                on  = 'sell'
                spc = 'stp'
            elif e.button() == Qt.MouseButton.LeftButton and md == Qt.KeyboardModifier.NoModifier:
                # check for orders to cancel with left click
                for b in L.sell_bxs:
                    if b[4] == row:
                        for r in b[2]:
                            if not r.stts == 'ended':
                                found_trades_to_cancel = True
                                ib.cancelOrder(r.trade.order)

        if on == 'none' or found_trades_to_cancel: 
            return

        # submit the trade
        o = t.mpl_offset + row * t.ladder_focus_inc 

        trade = tws_Trade(t, o, on, spc)
        L.update()

    def keyPressEvent(self, e):
        key = e.key()
        t = tws_Symbol.target
        L = self

        if t is None:
            return

        # send keys to floating panel first
        P = L.activated_floating_panel
        if L.activated_floating_panel:
            P.collision('back', 'key', key) ; return
        
        if key == Qt.Key.Key_O.value: #O
            h = 28 * 5 - 1
            L.activated_floating_panel = floating_panel('opt_switcher', int(L.ladder_width / 2 - L.fp_width / 2), L.ladder_ctrl_height + int(L.ladder_height / 2 - h / 2), L.fp_width, h)
            L.activated_floating_panel.prepare()
            L.update() ; return
        elif key == Qt.Key.Key_B.value: #B
            if t.ct_type == 'O':
                # LOAD
                s = tws_Symbol(t.parent.ct_str, False)
                s = s.setup()
                if s:
                    s.snap_offset_mid()
                    tws_Symbol.target = s
                    L.ctrl_form['order_size'].setText(str(s.order_size))
                L.update() ; return
        elif key == Qt.Key.Key_P.value: #P, simple display of open positions colored to show long vs short
            pdh = int(L.ladder_height * 0.33)
            L.activated_floating_panel = floating_panel('pos_display', 0, L.ladder_win_height - pdh, L.ladder_win_width, pdh)
            L.activated_floating_panel.prepare()
            L.update() ; return

        # handle keys for ladder manipulation
        if not t or t.mpl_offset is None:
            return

        if key == Qt.Key.Key_K.value:   #K
            t.mpl_offset -= 6 * t.ladder_focus_inc

        elif key == Qt.Key.Key_J.value: #J
            t.mpl_offset += 6 * t.ladder_focus_inc

        elif key == Qt.Key.Key_M.value: #M
            mid = ( t.ask + t.bid ) // 2
            mid = mid - (mid % t.ladder_focus_inc)
            t.mpl_offset = 999999 - mid - ((L.ladder_rows // 2) * t.ladder_focus_inc)
        
        elif key == Qt.Key.Key_F.value: #F
            t.ladder_focus_inc = t.ladder_inc[0]
            mid = ( t.ask + t.bid ) // 2
            mid = mid - (mid % t.ladder_focus_inc)
            t.mpl_offset = 999999 - mid - ((L.ladder_rows // 2) * t.ladder_focus_inc)
        
        elif key == Qt.Key.Key_L.value: #L
            if t:
                t.show_last ^= True
                print(t.show_last)
        
        elif key == Qt.Key.Key_D.value: #D Diag
            L.diag_bid_ask ^= True
            print('syml_dict:')
            for n, k in syml_dict.items():
                print(n, k.shadow)
            
        t.correct_oob()
        self.update()

    def focusOutEvent(self, e):
        # start timer to check for trade changes in TWS
        self.trade_check.start(500) # ms
    def focusInEvent(self, e):
        self.trade_check.stop()

    def paintEvent(self, e):
        qp = QPainter()
        L = self
        t = tws_Symbol.target

        if e.region().boundingRect().width() < L.ladder_win_width:
            # ctrl panel buttons trigger this on hover, etc
            return

        # TODO: a L.ctrl_frame and t.ctrl_frame which must match

        qp.begin(self)
        
        # draw ctrl panel and bottom 'price box' panel
        qp.drawPixmap(0, 0, L.ctrl_panel)
        qp.drawPixmap(0, L.ladder_win_height - L.ladder_bot_pane_h, L.bot_pane)

        if not t:
            qp.drawPixmap(0, L.ladder_ctrl_height, L.bt_decor)
            qp.end()
            return

        qp.drawPixmap(L.sbutton_opt_x, L.sbutton_opt_y, L.sbutton_opt_pm)
        
        font = L.ctrl_panel_font
        qp.setFont(L.ctrl_panel_font)

        if t.ct_type == 'O':
            name_br = qp.boundingRect(L.blank_r, 0, t.name)
            
            fill = QColor(180 - 20, 210 - 20, 210 - 20, 255)
            qp.fillRect(0, 4, name_br.width()  + 20, L.parent_arrow_h, fill)
            qp.drawPixmap(int(name_br.width()) + 10, 4, L.parent_arrow)

            L.last_parent_arrow_w = name_br.width() + 6 + L.parent_arrow_w

        qp.drawText(4, 4 + 12, t.name)

        avg = math.ceil(float(t.pos_avg_cost) * 100) / 100

        qp.drawText(4, L.ladder_ctrl_height - 4, str(int(t.pos)) + ' ' + str(avg))

        if t.ct_type == 'O':
            qp.setFont(QFont("Consolas", 9))
            qp.drawText(4, 4 + 24, t.exp_str)
        
        # there is a target with an mpl_offset, draw the ladder or end here
        if t.mpl_offset is None:
            qp.drawPixmap(0, L.ladder_ctrl_height, L.bt_decor)
            # draw floating panel if there is one
            if L.activated_floating_panel:
                P = L.activated_floating_panel
                for n, g in P.graphics.items():
                    qp.drawPixmap(g[1], g[2], g[0])
            qp.end()
            return

        # print shortable status, % change since last day close, 10 minute volume
        bot_pane_off = 16
        if t.short_fact is not None:
            if t.short_fact == 'S':
                qp.fillRect(0, L.ladder_win_height - L.ladder_bot_pane_h, bot_pane_off, L.ladder_bot_pane_h, QColor('#5CED73'))
            elif t.short_fact == 'H':
                qp.fillRect(0, L.ladder_win_height - L.ladder_bot_pane_h, bot_pane_off, L.ladder_bot_pane_h, QColor('#008631'))
            else:
                qp.fillRect(0, L.ladder_win_height - L.ladder_bot_pane_h, bot_pane_off, L.ladder_bot_pane_h, QColor(100,100,100))

        qp.setFont(L.ctrl_panel_font)
        qp.setPen(QColor(250, 250, 250))

        if t.close > 0:
            diff = (t.last / t.close - 1) * 100 
            diff_str = str(format(abs(diff), '.2f')) + '%'
            
            diff_br = qp.boundingRect(L.blank_r, 0, diff_str)
            if diff < 0:
                diff *= -1
                qp.fillRect(bot_pane_off, L.ladder_win_height - L.ladder_bot_pane_h, diff_br.width() + 4, L.ladder_bot_pane_h, QColor(147, 28, 29))
            else:
                qp.fillRect(bot_pane_off, L.ladder_win_height - L.ladder_bot_pane_h, diff_br.width() + 4, L.ladder_bot_pane_h, QColor(40, 40, 40))
            bot_pane_off += 2
            qp.drawText(bot_pane_off, L.ladder_win_height - 2, diff_str)
            bot_pane_off += diff_br.width() + 2
        
        if t.volume >= 1000:
            vol_str = str(int(t.volume / 1000)) + 'K'
            vol_br = qp.boundingRect(L.blank_r, 0, vol_str)
            qp.fillRect(bot_pane_off, L.ladder_win_height - L.ladder_bot_pane_h, vol_br.width() + 4, L.ladder_bot_pane_h, QColor('#660033'))
            bot_pane_off += 2
            qp.drawText(bot_pane_off, L.ladder_win_height - 2, vol_str)
            
        qp.setFont(QFont("Arial", 12, QFont.Weight.DemiBold))
        qp.setPen(QColor(0, 0, 0))

        if t.ladder_focus_inc > t.ladder_inc[0]:
            if False: # distracting?
                qp.drawPixmap(0, L.ladder_ctrl_height, L.bt_decor_nt)
            else:
                qp.drawPixmap(0, L.ladder_ctrl_height, L.bt_decor)
            br = qp.boundingRect(L.blank_r, 0, '± ' + str(t.ladder_focus_inc))
            qp.drawText(L.ladder_win_width - br.width() - 2, L.ladder_win_height - 2, '± ' + str(t.ladder_focus_inc))
        else:
            qp.drawPixmap(0, L.ladder_ctrl_height, L.bt_decor)
            
        font      = L.price_font 
        font_bold = L.price_font_b 

        o = t.mpl_offset
        m = L.ladder_row_spacing

        # calculate price box width, price box x based on largest number
        qp.setFont(font_bold)
        r = qp.boundingRect(L.blank_r, 0, L.mpl[0][0])
        x_off = int(L.ladder_win_width / 2 - r.width() / 2) - 8
        
        r = qp.boundingRect(L.blank_r, 0, L.mpl[o][0])
        pb_width = int(r.width()) + 8

        fm = QFontMetrics(font_bold)

        y_off = m / 2 - fm.ascent() / 2 - L.ladder_ctrl_height
        
        # alt styling 
        qp.drawPixmap(x_off, L.ladder_ctrl_height, L.p_decor, 0, 0, pb_width, L.ladder_height)
        
        # calculate bid and ask pos
        nrm_ask = t.ask % t.ladder_focus_inc
        if nrm_ask == 0:
            nrm_ask = t.ladder_focus_inc

        nrm_bid = t.bid % t.ladder_focus_inc

        na = 999999 - (t.ask + (t.ladder_focus_inc - nrm_ask)) # ciel
        nb = 999999 - (t.bid - nrm_bid) # floor

        last = int(t.last * 100)
        nrm_last = last % t.ladder_focus_inc
        nl = 999999 - (last - nrm_last) # floor
        
        # update what is on ladder after last draw
        L.last_price_box_width = pb_width
        L.last_price_box_x     = x_off

        L.last_ask = t.ask
        L.last_bid = t.bid
        L.last_ask_pos = -2
        L.last_bid_pos = -2

        nb_hit = -1
        na_hit = -1
        na_mod = 0
        nb_mod = 0
    
        bold_inc = t.ladder_focus_inc * 5
        for i in range(L.ladder_rows):
            p = QPointF(x_off + 4, (i + 1) * m - y_off)
            
            if na == o:
                qp.fillRect(x_off, i * m + L.ladder_ctrl_height, pb_width, L.ladder_row_spacing, L.ask_hl)
                L.last_ask_pos = i
                na_hit = i
            if nb == o:
                qp.fillRect(x_off, i * m + L.ladder_ctrl_height, pb_width, L.ladder_row_spacing, L.bid_hl)
                L.last_bid_pos = i
                nb_hit = i
            if nl == o and t.show_last:
                qp.fillRect(x_off + 3, i * m + L.ladder_ctrl_height, pb_width - 6, L.ladder_row_spacing, L.last_hl)


            qp.setFont(font)
            if L.mpl[o][1] % bold_inc == 0:
                qp.setFont(font_bold)

            qp.drawText(p, L.mpl[o][0])

            o += t.ladder_focus_inc

        # adjust bid/ask arrows if outside of ladder
        if nb >= o:
            nb = L.ladder_rows
            nb_mod = L.ladder_row_spacing // 2 
        elif nb < t.mpl_offset:
            nb = 0
            nb_mod = L.ladder_row_spacing // 2 
        else:
            nb = nb_hit
        
        if na >= o:
            na = L.ladder_rows
            na_mod = L.ladder_row_spacing // 2 
        elif na < t.mpl_offset:
            na = 0
            na_mod = L.ladder_row_spacing // 2 
        else:
            na = na_hit

        # populate trade and fill lists
        L.buy_bxs  = []
        L.sell_bxs = []
        L.fill_bxs = []
        for r in itertools.chain(t.trades, t.trades_fin):
            row = 0
            if r.dir == 'buy':
                row = math.ceil((r.offset - t.mpl_offset) / t.ladder_focus_inc)
            else:
                row = math.floor((r.offset - t.mpl_offset) / t.ladder_focus_inc)
            if row < 0 or row >= L.ladder_rows:
                continue

            y = L.ladder_row_spacing * row + L.ladder_ctrl_height

            # add fills
            found = False
            live_fill = False
            partial_fill = False
            if r.stts == 'live':
                live_fill = True
                if r.filled and r.size - r.filled != 0:
                    partial_fill = True

            for b in L.fill_bxs:
                if b[0] == y:
                    found = True
                    b[1].append(r)
                    if not b[2]:
                        b[2] = live_fill
                    if not b[3]:
                        b[3] = partial_fill
            
            if not found:
                L.fill_bxs.append([y, [r], live_fill, partial_fill, row])

            if r.stts == 'ended':
                continue

            if r.dir == 'buy':
                found = False
                for b in L.buy_bxs:
                    if b[0] == y:
                        found = True
                        if r.stts == 'live':
                            b[1] = r.stts
                            b[3] = r.spc

                        b[2].append(r)
    
                if not found:
                    L.buy_bxs.append([y, r.stts, [r], r.spc, row])

            elif r.dir == 'sell':
                found = False
                for b in L.sell_bxs:
                    if b[0] == y:
                        found = True
                        if r.stts == 'live':
                            b[1] = r.stts
                            b[3] = r.spc

                        b[2].append(r)
    
                if not found:
                    L.sell_bxs.append([y, r.stts, [r], r.spc, row])

        # draw orders
        for b in L.buy_bxs:
            color = QColor(150, 150, 150)
            if b[1] == 'live':
                color = QColor(100, 100, 250)

            qp.fillRect(0, b[0] + 1, L.last_price_box_x, L.ladder_row_spacing - 1, color)
            if b[3] == 'stp': # draw stop sign !
                qp.drawPixmap(L.last_price_box_x // 2 - L.stop_hex_mid, b[0] + 1, L.stop_hex)
            if len(b[2]) > 1:
                qp.drawPixmap(1, b[0], L.mult_trades)
        
        for b in L.sell_bxs:
            color = QColor(150, 150, 150)
            if b[1] == 'live':
                color = QColor(250, 100, 100)

            l = L.ladder_width - L.last_price_box_x - L.last_price_box_width - L.filled_pane_width
            qp.fillRect(L.last_price_box_x + L.last_price_box_width, b[0] + 1, l, L.ladder_row_spacing - 1, color)
            if b[3] == 'stp': # draw stop sign !
                qp.drawPixmap(L.last_price_box_x + L.last_price_box_width + l // 2 - L.stop_hex_mid, b[0] + 1, L.stop_hex)
            if len(b[2]) > 1:
                qp.drawPixmap(L.last_price_box_x + L.last_price_box_width + l - 12, b[0], L.mult_trades)

        # draw fill boxes
        for b in L.fill_bxs:
            w = L.filled_pane_width
            x = L.ladder_width - w

            color = QColor(140, 140, 140)
            
            if b[2]: # live bool
                color = QColor(60, 60, 60)
            if b[3]: # partial bool
                color = QColor(141, 208, 6)

            qp.fillRect(x, b[0] + 1, w, L.ladder_row_spacing - 1, color)
        
        # draw bid/ask arrows
        qp.drawPixmap(x_off + pb_width, na * m + L.ladder_ctrl_height - na_mod, L.ask_arrow)
        qp.drawPixmap(x_off - 12, nb * m + L.ladder_ctrl_height - nb_mod, L.bid_arrow)

        if L.diag_bid_ask:
            br = qp.boundingRect(L.blank_r, 0, t.bid_str)
            qp.fillRect(x_off - 60, nb * m + L.ladder_ctrl_height, br.width() + 4, L.ladder_bot_pane_h, QColor(255, 203, 164))
            qp.drawText(x_off - 60, nb * m + L.ladder_ctrl_height + 10, t.bid_str)
            
            br = qp.boundingRect(L.blank_r, 0, t.ask_str)
            qp.fillRect(x_off + pb_width + 20, na * m + L.ladder_ctrl_height, br.width() + 4, L.ladder_bot_pane_h, QColor(255, 203, 164))
            qp.drawText(x_off + pb_width + 20, na * m + L.ladder_ctrl_height + 10, t.ask_str)
            
            br = qp.boundingRect(L.blank_r, 0, str(t.last))
            qp.fillRect(x_off + pb_width + 20, (na-2) * m + L.ladder_ctrl_height, br.width() + 4, L.ladder_bot_pane_h, L.last_hl)
            qp.drawText(x_off + pb_width + 20, (na-2) * m + L.ladder_ctrl_height + 10, str(t.last))
        
        # draw floating panel if there is one
        if L.activated_floating_panel:
            P = L.activated_floating_panel
            for n, g in P.graphics.items():
                qp.drawPixmap(g[1], g[2], g[0])
        
        qp.end()

    def timerEvent(self, event):
        #ib.waitOnUpdate(0.001)
        ib.sleep(0) # is this faster?

app = QApplication(sys.argv)
ex = widgetLadder()
sys.exit(app.exec())
