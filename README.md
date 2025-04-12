### quick_trade.py ###
python >= 3, pyqt6, ib_async...
left click on bid side:       LMT BUY
right click on ask side:      LMT SELL
shift+left click on bid side: MKT BUY STP
shift+left click on ask side: MKT SELL STP
b: go (b)ack to underlying
j: scroll ladder down
k: scroll ladder up
m: snap mid
f: snap mid at zoom level 1
mouse scroll on prices in ladder: zoom in/out
mouse scroll on bid or ask cols: scroll up/down
left click on boxes on far right to show fill stats for order
left click on orders to cancel
...

o: (o)ption switcher menu
1-4: when in option switcher menu and not scolled, select option #
p: list (p)ositions
ESC: close menu

### quick_trade.ahk ###
AutoHotkey v2
hotkeys for tws classic, will require tuning of constants for your tws display settings
ctrl+s: make a chart group zoomable
z: zoom in on chart in group
` key + 1-4: set an order size in quick_trade
ctrl+t: send us stock/option to quick_trade
... 
