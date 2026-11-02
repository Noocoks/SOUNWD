from __future__ import annotations
import queue
import threading
from pathlib import Path
from urllib.parse import urlparse
import yt_dlp
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle

BG=(18/255,17/255,26/255,1); CARD=(33/255,30/255,43/255,1)
LAVENDER=(136/255,114/255,174/255,1); TEXT=(244/255,239/255,250/255,1)
MUTED=(182/255,173/255,191/255,1)
FORMATS={"Mejor disponible":"bestaudio/best","M4A (si existe)":"bestaudio[ext=m4a]/bestaudio/best","OPUS (si existe)":"bestaudio[acodec=opus]/bestaudio/best"}
DESTINATIONS={"Música / SOUNWD":"Music","Descargas / SOUNWD":"Downloads"}
HOSTS={"youtube.com","www.youtube.com","music.youtube.com","m.youtube.com","youtu.be"}

def valid_url(value):
    try:
        p=urlparse(value.strip()); host=(p.hostname or "").lower()
        return p.scheme in {"http","https"} and (host in HOSTS or any(host.endswith("."+h) for h in HOSTS))
    except ValueError: return False

class Panel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.padding=dp(15); self.spacing=dp(9)
        with self.canvas.before:
            Color(*CARD); self.rect=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(17)])
        self.bind(pos=self.sync,size=self.sync)
    def sync(self,*_): self.rect.pos=self.pos; self.rect.size=self.size

class SOUNWDApp(App):
    def build(self):
        self.title="SOUNWD"; self.events=queue.Queue(); self.downloading=False; self.last_files=[]
        self.private_dir=Path(self.user_data_dir)/"downloads"; self.private_dir.mkdir(parents=True,exist_ok=True)
        Window.clearcolor=BG; Window.softinput_mode="below_target"
        root=BoxLayout(orientation="vertical",padding=[dp(17),dp(12),dp(17),dp(12)])
        scroll=ScrollView(do_scroll_x=False,bar_width=dp(3))
        body=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(11),padding=[0,0,0,dp(12)])
        body.bind(minimum_height=body.setter("height"))
        brand=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(100),spacing=0)
        brand.add_widget(self.label("◖♪",30,LAVENDER,True,dp(34)))
        brand.add_widget(self.label("SOUNWD.",27,TEXT,True,dp(38)))
        brand.add_widget(self.label("YOUR SOUND. YOUR MOMENTS.",10,MUTED,True,dp(22)))
        body.add_widget(brand)
        body.add_widget(self.label("Tu música. Tu espacio. Tu estilo.",20,TEXT,True,dp(34)))
        body.add_widget(self.label("Un lugar tranquilo para guardar los sonidos que te acompañan.",12,MUTED,False,dp(34)))
        link=Panel(orientation="vertical",size_hint_y=None,height=dp(132))
        link.add_widget(self.label("1.  PEGA AQUÍ EL ENLACE",11,LAVENDER,True,dp(22)))
        self.url=TextInput(hint_text="Copia el enlace de YouTube y pégalo aquí",multiline=False,size_hint_y=None,height=dp(52),
            background_normal="",background_active="",background_color=(23/255,21/255,31/255,1),
            foreground_color=TEXT,hint_text_color=(142/255,132/255,153/255,1),cursor_color=LAVENDER,
            padding=[dp(11),dp(15)],font_size="14sp")
        link.add_widget(self.url); body.add_widget(link)
        row=GridLayout(cols=2,spacing=dp(9),size_hint_y=None,height=dp(124))
        fmt=Panel(orientation="vertical",padding=dp(11))
        fmt.add_widget(self.label("2. FORMATO",10,LAVENDER,True,dp(22)))
        self.format=Spinner(text="Mejor disponible",values=list(FORMATS),size_hint_y=None,height=dp(42),
            background_normal="",background_color=(64/255,54/255,79/255,1),color=TEXT,font_size="11sp")
        fmt.add_widget(self.format)
        dest=Panel(orientation="vertical",padding=dp(11))
        dest.add_widget(self.label("3. GUARDAR EN",10,LAVENDER,True,dp(22)))
        self.destination=Spinner(text="Música / SOUNWD",values=list(DESTINATIONS),size_hint_y=None,height=dp(42),
            background_normal="",background_color=(64/255,54/255,79/255,1),color=TEXT,font_size="11sp")
        dest.add_widget(self.destination); row.add_widget(fmt); row.add_widget(dest); body.add_widget(row)
        self.more_btn=self.button("＋  Más opciones",dp(38),(55/255,48/255,67/255,1))
        self.more_btn.bind(on_release=self.toggle_more); body.add_widget(self.more_btn)
        self.more=Panel(orientation="vertical",size_hint_y=None,height=0,opacity=0,disabled=True)
        checkrow=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(36),spacing=dp(8))
        self.playlist=CheckBox(size_hint=(None,None),size=(dp(30),dp(30)),color=LAVENDER)
        checkrow.add_widget(self.playlist)
        checkrow.add_widget(self.label("Descargar la lista completa si el enlace contiene una",11,MUTED))
        self.more.add_widget(checkrow); body.add_widget(self.more)
        action=Panel(orientation="vertical",size_hint_y=None,height=dp(178))
        self.status=self.label("4.  Pulsa el botón y espera un momento.",12,MUTED,False,dp(25)); action.add_widget(self.status)
        self.progress=self.label("",10,LAVENDER,False,dp(20)); action.add_widget(self.progress)
        self.download=self.button("Guardar audio",dp(52),LAVENDER,17); self.download.bind(on_release=self.start_download); action.add_widget(self.download)
        self.share=self.button("Compartir último audio",dp(36),(55/255,48/255,67/255,1)); self.share.bind(on_release=self.share_last); action.add_widget(self.share)
        body.add_widget(action)
        body.add_widget(self.label("Descarga solo contenido que tengas permiso para guardar.\nSOUNWD no descarga música desde Spotify.",10,MUTED,False,dp(42)))
        scroll.add_widget(body); root.add_widget(scroll)
        Clock.schedule_interval(self.poll_events,0.15)
        return root

    def label(self,text,size,color,bold=False,height=None):
        return Label(text=text,color=color,font_size=f"{size}sp",bold=bold,halign="center",valign="middle",
                     size_hint_y=None,height=height or dp(28),text_size=(Window.width-dp(42),None))
    def button(self,text,height,color,size=13):
        return Button(text=text,size_hint_y=None,height=height,background_normal="",background_down="",
                      background_color=color,color=TEXT,font_size=f"{size}sp",bold=True)
    def toggle_more(self,*_):
        show=self.more.height==0
        self.more.height=dp(65) if show else 0; self.more.opacity=1 if show else 0; self.more.disabled=not show
        self.more_btn.text="−  Ocultar opciones" if show else "＋  Más opciones"
    def start_download(self,*_):
        if self.downloading:return
        link=self.url.text.strip()
        if not valid_url(link):
            self.status.text="Pega un enlace válido de YouTube o YouTube Music."; return
        self.downloading=True; self.download.disabled=True; self.download.text="Un momento…"
        self.status.text="Conectando… no cierres SOUNWD."; self.progress.text=""
        threading.Thread(target=self.download_worker,args=(link,FORMATS[self.format.text],self.playlist.active,self.destination.text),daemon=True).start()
    def download_worker(self,link,selector,playlist,destination):
        before=set(self.private_dir.iterdir())
        def hook(d):
            if d.get("status")=="downloading":
                total=d.get("total_bytes") or d.get("total_bytes_estimate"); got=d.get("downloaded_bytes",0)
                pct=int(max(0,min(100,got/total*100))) if total else 0
                Clock.schedule_once(lambda _dt,p=pct:setattr(self.progress,"text",f"{p}%"),0)
        options={"format":selector,"outtmpl":str(self.private_dir/"%(title)s.%(ext)s"),
                 "noplaylist":not playlist,"quiet":True,"no_warnings":True,"progress_hooks":[hook],"overwrites":False}
        try:
            with yt_dlp.YoutubeDL(options) as ydl: code=ydl.download([link])
            if code: raise RuntimeError("La descarga no ha podido terminar.")
            files=[p for p in self.private_dir.iterdir() if p.is_file() and p not in before]
            if not files: raise RuntimeError("No se ha encontrado el archivo descargado.")
            saved=[]
            if platform=="android":
                from androidstorage4kivy import SharedStorage
                from jnius import autoclass
                Environment=autoclass("android.os.Environment"); shared=SharedStorage()
                collection=Environment.DIRECTORY_DOWNLOADS if destination.startswith("Descargas") else Environment.DIRECTORY_MUSIC
                for path in files:
                    uri=shared.copy_to_shared(str(path),collection=collection)
                    if uri:saved.append(path.name)
                if not saved: raise RuntimeError("Android no ha podido guardar el audio en la carpeta compartida.")
            else: saved=[p.name for p in files]
            self.events.put(("done",saved))
        except Exception as e:self.events.put(("error",str(e)))
    def poll_events(self,*_):
        try:
            while True:
                kind,payload=self.events.get_nowait(); self.downloading=False; self.download.disabled=False
                self.download.text="Guardar otro audio" if kind=="done" else "Intentar de nuevo"
                if kind=="done":
                    self.last_files=payload; self.status.text="¡Listo! Audio guardado correctamente."
                    self.progress.text=f"{len(payload)} archivo(s) guardado(s)"; self.url.text=""
                else:
                    self.status.text="No se ha podido guardar. Comprueba el enlace e inténtalo otra vez."
                    self.progress.text=""; self.popup(str(payload))
        except queue.Empty:pass
    def popup(self,message):
        box=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(10))
        box.add_widget(Label(text=message[:600],color=TEXT))
        popup=Popup(title="SOUNWD",content=box,size_hint=(0.88,0.48))
        close=self.button("Entendido",dp(42),LAVENDER); close.bind(on_release=popup.dismiss); box.add_widget(close); popup.open()
    def share_last(self,*_):
        if not self.last_files:
            self.status.text="Todavía no hay descargas para compartir.";return
        try:
            from androidstorage4kivy import ShareSheet,SharedStorage
            from jnius import autoclass
            Environment=autoclass("android.os.Environment"); shared=SharedStorage()
            collection=Environment.DIRECTORY_DOWNLOADS if self.destination.text.startswith("Descargas") else Environment.DIRECTORY_MUSIC
            uris=[]
            for name in self.last_files:
                uri=shared.copy_to_shared(str(self.private_dir/name),collection=collection)
                if uri:uris.append(uri)
            if uris:ShareSheet().share_file_list(uris)
            else:self.status.text="No se ha podido preparar el archivo para compartir."
        except Exception as e:self.popup("No se ha podido compartir: "+str(e))

if __name__=="__main__": SOUNWDApp().run()
