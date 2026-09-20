import sys,threading,time,base64,os,shutil
from pathlib import Path
from PySide6.QtCore import Qt,Signal,QObject,QTimer
from PySide6.QtGui import QPixmap,QImage
from PySide6.QtWidgets import *
from .config import *
from .settings import load_settings,save_settings
from .security import get_api_key,save_api_key
from .api import OpenAIImageClient
from .db import add_generation,recent,totals
from .validation import validate_size,validate_options
from .local_image import resize_or_crop

DARK="""QWidget{background:#0d0f12;color:#e8eaed;font-family:'Segoe UI';font-size:13px}
QLineEdit,QComboBox,QPlainTextEdit,QSpinBox,QDoubleSpinBox,QTableWidget{background:#15181d;border:1px solid #2b3038;border-radius:7px;padding:7px}
QPushButton{background:#20242b;border:1px solid #343a44;border-radius:7px;padding:8px 12px} QPushButton:hover{background:#292e37}
QPushButton:disabled{color:#737983} QProgressBar{border:1px solid #2b3038;border-radius:5px;text-align:center;background:#15181d}"""

class DropLabel(QLabel):
    fileDropped=Signal(str)
    def __init__(self,text):
        super().__init__(text);self.setAcceptDrops(True);self.setAlignment(Qt.AlignCenter);self.setMinimumHeight(120)
        self.setStyleSheet("border:1px dashed #3a414d;border-radius:9px;padding:16px")
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():e.acceptProposedAction()
    def dropEvent(self,e):
        p=e.mimeData().urls()[0].toLocalFile()
        if Path(p).suffix.lower() in (".png",".jpg",".jpeg",".webp"):self.fileDropped.emit(p)

class Bus(QObject):
    event=Signal(str,object);done=Signal(object);failed=Signal(str)

class Window(QMainWindow):
    def __init__(self):
        super().__init__();self.s=load_settings();self.source=None;self.mask=None;self.cancel_event=threading.Event();self.started=None
        self.bus=Bus();self.bus.event.connect(self.on_event);self.bus.done.connect(self.on_done);self.bus.failed.connect(self.on_failed)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick)
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}");self.resize(1280,860);self.build();self.refresh_history()

    def build(self):
        tabs=QTabWidget();self.setCentralWidget(tabs)
        work=QWidget();tabs.addTab(work,"Create / Edit"); hist=QWidget();tabs.addTab(hist,"History & Costs"); sett=QWidget();tabs.addTab(sett,"Settings")
        main=QHBoxLayout(work); left=QWidget();form=QFormLayout(left)
        self.mode=QComboBox();self.mode.addItems(["Generate","Edit / Reference","Expand / Outpaint","Local Resize / Crop"])
        self.source_box=DropLabel("Drop a PNG/JPEG/WebP here\nor click Browse");self.source_box.fileDropped.connect(self.set_source)
        browse=QPushButton("Browse source image");browse.clicked.connect(self.browse_source)
        self.source_name=QLabel("No source image")
        form.addRow("Mode",self.mode);form.addRow("Source",self.source_box);form.addRow("",browse);form.addRow("",self.source_name)
        self.orientation=QComboBox();self.orientation.addItems(ORIENTATIONS);self.orientation.setCurrentText(self.s["orientation"])
        self.aspect=QComboBox();self.aspect.addItems(ASPECTS);self.aspect.setCurrentText(self.s["aspect"])
        self.size=QComboBox();self.size.setEditable(True)
        self.orientation.currentTextChanged.connect(self.refresh_sizes);self.aspect.currentTextChanged.connect(self.refresh_sizes);self.refresh_sizes()
        self.model=QComboBox();self.model.addItems(MODELS);self.model.setCurrentText(self.s["model"])
        self.quality=QComboBox();self.quality.addItems(QUALITIES);self.quality.setCurrentText(self.s["quality"])
        self.format=QComboBox();self.format.addItems(FORMATS);self.format.setCurrentText(self.s["format"])
        self.background=QComboBox();self.background.addItems(BACKGROUNDS);self.background.setCurrentText(self.s["background"])
        self.compression=QSpinBox();self.compression.setRange(0,100);self.compression.setValue(self.s["compression"])
        self.partial=QSpinBox();self.partial.setRange(0,3);self.partial.setValue(self.s["partial_images"])
        self.local_mode=QComboBox();self.local_mode.addItems(["Fit","Crop","Stretch"])
        for a,b in [("Orientation",self.orientation),("Aspect ratio",self.aspect),("Resolution",self.size),("Model",self.model),
                    ("Quality",self.quality),("Format",self.format),("Background",self.background),("JPEG/WebP compression",self.compression),
                    ("Partial previews",self.partial),("Local resize mode",self.local_mode)]:form.addRow(a,b)
        self.prompt=QPlainTextEdit("Create or edit the image while preserving important subject details and composition.")
        form.addRow("Prompt",self.prompt)
        btns=QHBoxLayout();self.go=QPushButton("Run");self.cancel=QPushButton("Cancel");self.cancel.setEnabled(False);btns.addWidget(self.go);btns.addWidget(self.cancel)
        self.go.clicked.connect(self.run_job);self.cancel.clicked.connect(self.request_cancel);form.addRow(btns)
        right=QWidget();rv=QVBoxLayout(right);self.preview=QLabel("Preview");self.preview.setAlignment(Qt.AlignCenter);self.preview.setMinimumSize(580,420)
        self.preview.setStyleSheet("border:1px solid #2b3038;border-radius:8px");self.status=QLabel("Ready");self.progress=QProgressBar();self.progress.setRange(0,1)
        self.meta=QLabel("No output yet.");self.last_output=None;self.preview_bytes=None;self.preview_format="png"
        outbuttons=QHBoxLayout();self.open_image_btn=QPushButton("Open Image");self.open_folder_btn=QPushButton("Open Folder");self.save_as_btn=QPushButton("Save As...");self.save_preview_btn=QPushButton("Save Preview...")
        self.open_image_btn.clicked.connect(self.open_image);self.open_folder_btn.clicked.connect(self.open_folder);self.save_as_btn.clicked.connect(self.save_as);self.save_preview_btn.clicked.connect(self.save_preview)
        for b in (self.open_image_btn,self.open_folder_btn,self.save_as_btn): b.setEnabled(False);outbuttons.addWidget(b)
        self.save_preview_btn.setEnabled(False);outbuttons.addWidget(self.save_preview_btn)
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(700)
        rv.addWidget(self.preview,4);rv.addWidget(self.status);rv.addWidget(self.progress);rv.addWidget(self.meta);rv.addLayout(outbuttons);rv.addWidget(self.log,2)
        main.addWidget(left,2);main.addWidget(right,3)
        hv=QVBoxLayout(hist);self.summary=QLabel();self.table=QTableWidget(0,8)
        self.table.setHorizontalHeaderLabels(["Date","Operation","Model","Size","Quality","Time","Tokens","Cost"]);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        hv.addWidget(self.summary);hv.addWidget(self.table)
        sf=QFormLayout(sett);self.key=QLineEdit();self.key.setEchoMode(QLineEdit.Password);self.key.setPlaceholderText("Windows Credential Manager")
        self.timeout=QSpinBox();self.timeout.setRange(60,3600);self.timeout.setValue(self.s["timeout_seconds"])
        self.cost_limit=QDoubleSpinBox();self.cost_limit.setRange(0,10000);self.cost_limit.setDecimals(2);self.cost_limit.setValue(self.s["cost_limit_usd"])
        self.output_folder=QLineEdit(self.s.get("output_folder") or str(IMAGE_DIR))
        outrow=QHBoxLayout();outrow.addWidget(self.output_folder);outbrowse=QPushButton("Browse...");outbrowse.clicked.connect(self.choose_output_folder);outrow.addWidget(outbrowse)
        save=QPushButton("Save settings");save.clicked.connect(self.save);sf.addRow("OpenAI API key",self.key);sf.addRow("Timeout",self.timeout);sf.addRow("Tracked cost warning ($)",self.cost_limit);sf.addRow("Output folder",outrow);sf.addRow(save)

    def refresh_sizes(self):
        old=self.s.get("size","3840x2160");vals=RESOLUTION_PRESETS.get((self.orientation.currentText(),self.aspect.currentText()),[])
        self.size.clear();self.size.addItems(vals);self.size.setCurrentText(old if old in vals else (vals[0] if vals else old))
    def choose_output_folder(self):
        p=QFileDialog.getExistingDirectory(self,"Choose output folder",self.output_folder.text() or str(IMAGE_DIR))
        if p:self.output_folder.setText(p)
    def open_image(self):
        if self.last_output and Path(self.last_output).exists(): os.startfile(self.last_output)
    def open_folder(self):
        if self.last_output and Path(self.last_output).exists(): os.startfile(str(Path(self.last_output).parent))
    def save_as(self):
        if not self.last_output or not Path(self.last_output).exists(): return
        ext=Path(self.last_output).suffix
        p,_=QFileDialog.getSaveFileName(self,"Save image as",Path(self.last_output).name,f"Image (*{ext})")
        if p: shutil.copy2(self.last_output,p);self.append(f"Copied to: {p}")
    def save_preview(self):
        default_name=time.strftime("%Y-%m-%d_%H-%M-%S")+"_preview.png"
        dest,_=QFileDialog.getSaveFileName(self,"Save preview",str(Path.home()/"Pictures"/default_name),"PNG image (*.png);;JPEG image (*.jpg *.jpeg)")
        if not dest:return
        pix=self.preview.pixmap()
        if pix is None or pix.isNull(): QMessageBox.warning(self,"Preview","There is no preview image to save.");return
        fmt="JPG" if Path(dest).suffix.lower() in (".jpg",".jpeg") else "PNG"
        if not pix.save(dest,fmt,95): QMessageBox.critical(self,"Save failed",f"Could not save preview to:\n{dest}");return
        self.append(f"Preview saved manually: {dest}")
    def browse_source(self):
        p,_=QFileDialog.getOpenFileName(self,"Select image","","Images (*.png *.jpg *.jpeg *.webp)")
        if p:self.set_source(p)
    def set_source(self,p):
        self.source=p;self.source_name.setText(Path(p).name);pix=QPixmap(p)
        if not pix.isNull(): self.preview.setPixmap(pix.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation));self.save_preview_btn.setEnabled(True)
    def save(self):
        if self.key.text().strip():save_api_key(self.key.text())
        self.save_silent();QMessageBox.information(self,"Saved","Settings saved.")
    def save_silent(self):
        self.s.update(model=self.model.currentText(),quality=self.quality.currentText(),size=self.size.currentText(),
          format=self.format.currentText(),background=self.background.currentText(),partial_images=self.partial.value(),
          timeout_seconds=self.timeout.value(),cost_limit_usd=self.cost_limit.value(),orientation=self.orientation.currentText(),
          aspect=self.aspect.currentText(),compression=self.compression.value(),output_folder=self.output_folder.text().strip());save_settings(self.s)
    def append(self,x):self.log.appendPlainText(time.strftime("[%H:%M:%S] ")+str(x))
    def run_job(self):
        mode=self.mode.currentText();size=self.size.currentText().strip()
        try:validate_size(size)
        except Exception as e:QMessageBox.warning(self,"Invalid resolution",str(e));return
        if mode!="Generate" and not self.source:QMessageBox.warning(self,"Source image","Choose a source image first.");return
        if mode=="Local Resize / Crop":
            try:
                p=resize_or_crop(self.source,size,self.local_mode.currentText(),self.output_folder.text().strip());self.last_output=p;self.set_source(p);self.meta.setText(f"Local output: {p}");self.append(f"Local resize complete: {p}");[b.setEnabled(True) for b in (self.open_image_btn,self.open_folder_btn,self.save_as_btn)]
            except Exception as e:QMessageBox.critical(self,"Resize failed",str(e))
            return
        key=get_api_key() or self.key.text().strip()
        if not key:QMessageBox.warning(self,"API key","Enter an API key in Settings.");return
        prompt=self.prompt.toPlainText().strip()
        if not prompt:QMessageBox.warning(self,"Prompt","Prompt cannot be empty.");return
        try:validate_options(self.model.currentText(),self.quality.currentText(),self.format.currentText())
        except Exception as e:QMessageBox.warning(self,"Invalid options",str(e));return
        if self.background.currentText()=="transparent" and self.format.currentText()=="jpeg":
            QMessageBox.warning(self,"Invalid options","Transparent background requires PNG or WebP.");return
        if mode=="Expand / Outpaint":
            prompt=("Expand the provided image naturally to the requested canvas and aspect ratio. Preserve the original subject, identity, pose, style, lighting, perspective and important details. "
                    "Create coherent new content only where needed to fill the wider/taller composition. Do not simply stretch the source. "+prompt)
        self.save_silent();self.cancel_event.clear();self.go.setEnabled(False);self.cancel.setEnabled(True);self.progress.setRange(0,0);self.started=time.monotonic();self.timer.start(1000)
        args=(mode,prompt,key);threading.Thread(target=self.worker,args=args,daemon=True).start()
    def worker(self,mode,prompt,key):
        try:
            c=OpenAIImageClient(key,self.timeout.value())
            common=dict(model=self.model.currentText(),size=self.size.currentText(),quality=self.quality.currentText(),
                        output_format=self.format.currentText(),background=self.background.currentText(),compression=self.compression.value(),
                        on_event=lambda a,b:self.bus.event.emit(a,b),cancel=self.cancel_event,output_dir=self.output_folder.text().strip())
            if mode=="Generate":r=c.generate(prompt,partial_images=self.partial.value(),**common)
            else:r=c.edit(self.source,prompt,**common)
            self.bus.done.emit(r)
        except Exception as e:self.bus.failed.emit(str(e))
    def on_event(self,k,d):
        if k=="partial" and isinstance(d,dict):
            b=d.get("b64_json") or d.get("partial_image_b64")
            if b:
                im=QImage.fromData(base64.b64decode(b))
                if not im.isNull():
                    self.preview_bytes=base64.b64decode(b);self.preview_format="png"
                    self.preview.setPixmap(QPixmap.fromImage(im).scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation));self.save_preview_btn.setEnabled(True)
            self.append("Partial preview received.")
        else:self.append(d if isinstance(d,str) else k)
    def on_done(self,r):
        add_generation(r);self.finish();self.last_output=r.path;[b.setEnabled(True) for b in (self.open_image_btn,self.open_folder_btn,self.save_as_btn,self.save_preview_btn)];pix=QPixmap(r.path);self.preview.setPixmap(pix.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
        tok="Unavailable" if r.total_tokens is None else f"{r.total_tokens:,}";cost="Unavailable" if r.cost_usd is None else f"${r.cost_usd:.5f}"
        self.meta.setText(f"{r.operation} • {r.width}×{r.height} • {r.file_size/1048576:.2f} MB • {r.duration:.1f}s • {tok} tokens • {cost}")
        self.append(f"Saved successfully: {r.path} ({Path(r.path).stat().st_size/1048576:.2f} MB)");self.refresh_history()
    def on_failed(self,m):self.finish();self.append("ERROR: "+m);QMessageBox.critical(self,"Operation failed",m)
    def finish(self):self.timer.stop();self.progress.setRange(0,1);self.progress.setValue(1);self.go.setEnabled(True);self.cancel.setEnabled(False);self.status.setText("Ready");self.started=None
    def tick(self):
        if self.started:
            s=int(time.monotonic()-self.started);self.status.setText(f"Working / waiting for API • {s//60:02d}:{s%60:02d}")
    def request_cancel(self):self.cancel_event.set();self.cancel.setEnabled(False);self.append("Cancellation requested.")
    def refresh_history(self):
        rows=recent();t=totals();self.summary.setText(f"Tracked: {t['count']} • Tokens: {t['tokens']:,} • Cost: ${t['cost']:.5f}");self.table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            vals=[r["created_at"][:19],r["operation"] or "generate",r["model"],f'{r["width"]}×{r["height"]}',r["quality"],f'{r["duration"]:.1f}s',str(r["total_tokens"] or "—"),"—" if r["cost_usd"] is None else f'${r["cost_usd"]:.5f}']
            for j,v in enumerate(vals):self.table.setItem(i,j,QTableWidgetItem(v))
def run():
    app=QApplication(sys.argv);app.setStyleSheet(DARK);w=Window();w.show();sys.exit(app.exec())
