from tkinter import *
from tkinter import ttk

class Table:
    def __init__(self, ws):
        frame = Frame(ws)
        frame.pack()

        #self.scrollbar
        self.scroll = Scrollbar(frame)
        self.scroll.pack(side=RIGHT, fill=Y)

        self.scroll = Scrollbar(frame,orient='horizontal')
        self.scroll.pack(side= BOTTOM,fill=X)

        self.tv = ttk.Treeview(frame,yscrollcommand=self.scroll.set, xscrollcommand = self.scroll.set)

    def update(self, lst, header):
        for item in self.tv.get_children():
            self.tv.delete(item)

        self.tv.pack()

        self.scroll.config(command=self.tv.yview)
        self.scroll.config(command=self.tv.xview)

        #define our column
        self.tv['columns'] = header

        # format our column
        self.tv.column("#0", width=0,  stretch=NO) 
        self.tv.heading("#0",text="",anchor=CENTER)
        for element in header:
            self.tv.column(element, anchor=CENTER, width=80)
            self.tv.heading(element,text=element,anchor=CENTER)

        i = 0
        for row in lst:
            self.tv.insert(parent='',index='end',iid=i,text='', values = row)
            i += 1
        self.tv.pack()