#!/usr/bin/env python

import Tkinter as tk, tkFont, tkFileDialog
import sys, os, time
import onionshare
from Queue import Queue, Empty
from threading import Thread

class OnionShareGUI(object):
    def __init__(self):
        self.root = tk.Tk()

        # prepare GUI
        self.root.title('OnionShare')
        self.root.resizable(0, 0)
        self.create_widgets()
        self.root.grid()

        # select file
        if len(sys.argv) >= 2:
            self.filename = sys.argv[1]
        else:
            self.filename = tkFileDialog.askopenfilename(title="Choose a file to share", parent=self.root)
        self.basename = os.path.basename(self.filename)
        self.root.title('OnionShare - {0}'.format(self.basename))

        # todo: start onionshare here, and display web server logs in update() method
        # this might be helpful: https://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python

        # update regularly
        self.update()

    def create_widgets(self):
        self.pad = 10
        sys12 = tkFont.Font(family="system", size=12)
        sys20 = tkFont.Font(family="system", size=20, weight="bold")

        # url
        self.url_labelframe = tk.LabelFrame(text="Send this URL to your friend")
        self.url_labelframe.pack()
        self.url_text = tk.Text(self.url_labelframe, width=31, height=2, font=sys20)
        self.url_text.config(state=tk.DISABLED)
        self.url_text.pack(padx=self.pad, pady=self.pad)
        self.url_labelframe.grid(padx=self.pad, pady=self.pad)

        # logs
        self.logs_labelframe = tk.LabelFrame(text="Server logs")
        self.logs_labelframe.pack()
        self.logs_text = tk.Text(self.logs_labelframe, width=70, height=10, font=sys12)
        self.logs_text.insert(tk.INSERT, "")
        self.logs_text.config(state=tk.DISABLED)
        self.logs_text.pack(padx=self.pad, pady=self.pad)
        self.logs_labelframe.grid(padx=self.pad, pady=self.pad)

        # quit button
        self.quit_button = tk.Button(self.root, text='Quit', command=self.root.quit)
        self.quit_button.grid(padx=self.pad, pady=self.pad)

    def update(self):
        self.root.after(500, self.update)

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

def main():
    app = OnionShareGUI()
    app.root.mainloop()

if __name__ == '__main__':
    main()
