#! /usr/bin/env python3.2
#
# Andrew L Janke <a.janke@gmail.com>
#
# A PySide GUI app for N3


import signal
import sys

import os

from PySide.QtCore import *
from PySide.QtGui import *

from subprocess import call, Popen, PIPE

proc_dir = "minc_proc"
stage_dir = "03-nuc"

# catch Ctrl-C and die
signal.signal(signal.SIGINT, signal.SIG_DFL)

# signal Class
class CmdSignal(QObject):
   sig = Signal(str)

# QThread Class for running commands
class CmdThread(QThread):
   def __init__(self, parent = None):
      QThread.__init__(self, parent)
      self.exiting = False
      self.complete = CmdSignal()
      self.update_o = CmdSignal()
      self.update_e = CmdSignal()
      self.cmd = []

   # run the command
   def run(self):
      pipe = Popen(self.cmd, stdout=PIPE, stderr=PIPE)
      while True:
         stdout_t = pipe.stdout.readline().decode("utf-8").rstrip()
         stderr_t = pipe.stderr.readline().decode("utf-8").rstrip()
   
         if not stdout_t and not stderr_t:
            break
   
         print("[PO]" + stdout_t, "")
         print("[PE]" + stderr_t, "")
         
         # tell the world
         self.update_o.sig.emit(stdout_t)
         self.update_e.sig.emit(stderr_t)
         
      self.exiting=True
      self.complete.sig.emit('Done')



class MainWindow(QDialog):
   
   def __init__(self, parent=None):
      super(MainWindow, self).__init__(parent)
      
      self.out_dir = ""
      self.infile = ""
      
      print("SOD: " + self.out_dir)
      
      # Create widgets
      self.inlabel = QLabel("input file:")
      self.inedit = QLineEdit(self.infile)
      self.inbutton = QPushButton("choose file")
         
      self.outlabel = QLabel("output file:")
      self.outedit = QLineEdit("")
      self.outbutton = QPushButton("choose file")       
      
      self.fieldlabel = QLabel("correction field:")
      self.fieldpixmap = QLabel("field")
      
      self.commandlabel = QLabel("command:")
      self.commandtext = QPlainTextEdit("...")
      
      self.stdoutlabel = QLabel("output(stdout):")
      self.stdouttext = QPlainTextEdit()
      self.stdouttext.ensureCursorVisible()
      
      self.stderrlabel = QLabel("error(stderr):")
      self.stderrtext = QPlainTextEdit()
      self.stderrtext.ensureCursorVisible()
      
      self.gobutton = QPushButton("go")
      
      # Create layout and add widgets
      vlayout = QVBoxLayout()
      vlayout.addWidget(self.inlabel)
      
      self.ihlayout = QHBoxLayout()
      self.ihlayout.addWidget(self.inedit)
      self.ihlayout.addWidget(self.inbutton)
      vlayout.addLayout(self.ihlayout)
      
      vlayout.addWidget(self.outlabel)
      self.ohlayout = QHBoxLayout()
      self.ohlayout.addWidget(self.outedit)
      self.ohlayout.addWidget(self.outbutton)
      vlayout.addLayout(self.ohlayout)
      
      vlayout.addWidget(self.fieldlabel)
      vlayout.addWidget(self.fieldpixmap)
      
      vlayout.addWidget(self.commandlabel)
      vlayout.addWidget(self.commandtext)
      
      vlayout.addWidget(self.stdoutlabel)
      vlayout.addWidget(self.stdouttext)
      
      vlayout.addWidget(self.stderrlabel)
      vlayout.addWidget(self.stderrtext)
      
      vlayout.addWidget(self.gobutton)
      
      # Set dialog layout
      self.setLayout(vlayout)
      
      # Add thread
      self.cmdthread = CmdThread()
      self.cmdthread.update_o.sig.connect(self.cmdupdate_o)
      self.cmdthread.update_e.sig.connect(self.cmdupdate_e)
      self.cmdthread.complete.sig.connect(self.cmdcomplete)
      
      # Add callbacks
      self.inbutton.clicked.connect(self.infile_cb)
      self.outbutton.clicked.connect(self.outfile_cb)
      self.gobutton.clicked.connect(self.cmdstart)
   
   # callbacks
   def cmdstart(self):
      if not self.cmdthread.isRunning():
         self.cmdthread.exiting=False
         
         # create command
         self.cmdthread.cmd = ["nu_correct", "-clobber", self.inedit.text(), self.outedit.text()]
         
         # update widget
         self.commandtext.setPlainText(" ".join(self.cmdthread.cmd))
      
         self.cmdthread.start()
         self.commandlabel.setText('Processing running')
         self.gobutton.setEnabled(False)

   def cmdcomplete(self, data):
      print(">>>>Done>>>>")
      self.commandtext.appendPlainText(">>>>Done>>>> "+data)
      
      pixmap = QPixmap("minc_proc/03-nuc/orig.a.mnc.jpg")
      self.fieldpixmap.setPixmap(pixmap)
      
      
      self.gobutton.setEnabled(True)
   
   def cmdupdate_o(self, data):
      self.stdouttext.appendPlainText(data)
   
   def cmdupdate_e(self, data):
      self.stderrtext.appendPlainText(data)
   
   # select infile
   def infile_cb(self):
      dialog = QFileDialog()
      dialog.setFileMode(QFileDialog.AnyFile)
      if dialog.exec_():
         files = dialog.selectedFiles()
         self.set_infile(files[0])
         #self.inedit.setText(files[0])
    
   # select outfile
   def outfile_cb(self):
      dialog = QFileDialog()
      dialog.setFileMode(QFileDialog.AnyFile)
      if dialog.exec_():
         files = dialog.selectedFiles()
         self.outedit.setText(files[0])
   
   # set input filename
   def set_infile(self, filename):
      print("SI: " + filename)
      self.inedit.setText(filename)
      self.outedit.setText(os.path.join(self.out_dir, os.path.basename(self.inedit.text())))
   
   def set_outdir(self, dirname):
      print("SO: " + dirname)
      self.out_dir = dirname
   
 
if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # setup and make default directories
    out_dir = os.path.join(proc_dir, stage_dir)
    print("Out Dir: " + out_dir)
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
      print("Dir made")
    
    # Create and show the form
    frame = MainWindow()
    frame.set_outdir(out_dir)
    frame.set_infile("infile.mnc")
    frame.show()
    
    # Run the main Qt loop
    app.exec_()
    sys.exit()
