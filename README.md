WINDOWS. UNSTABLE, UNTESTED! US STOCKS/OPTIONS


https://github.com/user-attachments/assets/6128df35-f087-4399-917a-620c687cc8bc


### quick_change.py
python 3, pyqt6, ib_async...<br/>
left click on bid side:       LMT BUY<br/>
right click on ask side:      LMT SELL<br/>
shift+left click on bid side: MKT BUY STP<br/>
shift+left click on ask side: MKT SELL STP<br/>
b: go (b)ack to underlying<br/>
j: scroll ladder down<br/>
k: scroll ladder up<br/>
m: snap mid<br/>
f: snap mid at zoom level 1<br/>
l: show/hide (l)ast price<br/>
mouse scroll on prices in ladder: zoom in/out<br/>
mouse scroll on bid or ask cols: scroll up/down<br/>
left click on boxes on right to show fill stats for order<br/>
black = order working, grey = order not transmitted/complete, green = order partially filled<br/>
left click on orders to cancel<br/>
o: (o)ption switcher menu<br/>
right click on option to save it between sessions (a * will appear)<br/>
1-4: when in option switcher menu and not scrolled, select option #<br/>
p: list (p)ositions<br/>
ESC: close menu<br/>
...
### quick_change.ahk
AutoHotkey v2<br/>
hotkeys for tws classic, will require tuning of constants for your tws display settings<br/>
ctrl+s: make a chart group zoomable<br/>
F1-F6: change bar size<br/>
z: zoom in on chart in group<br/>
` key + 1-4: set an order size in quick_change.py<br/>
ctrl+t: send chart contract to quick_change.py<br/>
...
