#!/usr/bin/env python3
"""
Computer Science Wordle v2 — A PySide6 Desktop Game
Guess the 5-letter Computer Science term in 6 tries!

Features:
  - Hard Mode: revealed hints must be reused
  - Hints: reveal a random correct letter (3 per game)
  - CS Definitions shown after each game
  - Share: copy emoji grid to clipboard
  - Stats Dialog with distribution bar chart
  - Pop animation on typing, flip on reveal
  - Help dialog, persistent stats (JSON)

Run:  python cs_wordle.py
Requires: pip install PySide6
"""

import sys, os, json, math, random
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox, QDialog,
    QGraphicsOpacityEffect, QSizePolicy,
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, Signal,
    QRectF, QSize,
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QKeyEvent, QShortcut, QKeySequence,
    QPainter, QPen, QBrush, QPainterPath, QClipboard,
)

# ═══════════════════════════════════════════════════════════════════════════
#  Colour palette
# ═══════════════════════════════════════════════════════════════════════════
BG        = "#121213"
TILE_EMPTY= "#121213"
TILE_FILL = "#18181a"
BORDER_E  = "#3a3a3c"
GREEN     = "#538d4e"
YELLOW    = "#b59f3b"
GRAY      = "#3a3a3c"
KB_BG     = "#818384"
WHITE     = "#ffffff"
ACCENT    = "#58a6ff"

STATS_FILE = Path.home() / ".cs_wordle_stats.json"

# ═══════════════════════════════════════════════════════════════════════════
#  Word list — 5-letter CS terms
# ═══════════════════════════════════════════════════════════════════════════
SOLUTION_WORDS = sorted(set(w.lower() for w in [
    "array","btree","deque","edges","graph","heaps","lists",
    "nodes","queue","quick","radix","slice","sorts","stack",
    "store","tensor","trees","tries","value","vector",
    "build","cargo","class","django","flask","lambda","linux",
    "rails","react","rust","scala","spark","swift","torch",
    "async","await","crash","debug","fetch","fiber","field",
    "final","float","frame","fused","index","inner","input",
    "ioctl","joins","lexer","local","locks","logic","loops",
    "macro","merge","mixin","model","named","nonce","parse",
    "patch","paths","pipes","pixel","point","print","proxy",
    "pull","push","query","range","ready","regex","relay",
    "render","retry","route","schema","scope","seeds","serve",
    "setup","shell","shift","sigma","sleep","slots","spawn",
    "split","state","steal","stream","struct","super","switch",
    "sync","table","tests","token","trace","trait","trans",
    "tuple","types","valid","views","yield","zones",
    "cache","clone","hosts","http","mount","mutex","oauth",
    "crypt","inode","octal","intel","kernel",
    "azure","cloud","codec","event","layer","modal","panic",
]))
SOLUTION_WORDS = sorted(w for w in SOLUTION_WORDS if len(w)==5 and w.isalpha())

# ═══════════════════════════════════════════════════════════════════════════
#  Extended valid-guess list (CS words + common English 5-letter words)
#  This prevents the frustration of "not in word list" for reasonable
#  guesses while keeping solutions CS-only.
# ═══════════════════════════════════════════════════════════════════════════
_EXTRA_GUESSES = """about above abuse acted acute admit adopt adult after again
agent agree ahead alarm album alert alien align alike alive allow
alone along alter among anger angle angry apart apple apply arena
argue arise armor arise array aside asset avoid awake award aware
awful badge badly basic batch beach began begin being below bench
birth black blade blame blank blast blaze bleed blend bless blind
block blood blown board bonds boost bound brain brand brave bread
break breed brick brief broad broke brown brush buddy build bunch
burst buyer cable carry catch cause chain chair charm chase cheap
check cheek chess chest chief child chose chunk civil claim clash
class clean clear clerk click cliff climb cling clock close cloth
cloud coach coast color comes comic coral could count court cover
crack craft crane crash crazy cream crime cross crowd crown cruel
crush curve cycle daily dance death decay decor delay depth devil
dirty donor doubt draft drain drama drank drawn dream dress dried
drift drill drink drive drone drops drove drugs drunk dying eager
early earth eight elect elite email empty enemy enjoy enter entry
equal error essay event every exact exile exist extra fable facet
faith false fancy fatal fault favor feast fence fewer fiber field
fifth fifty fight final first fixed flame flash flesh flies float
flood floor flora fluid flush focal focus force forge forth found
frame frank fraud fresh front frost froze fruit fully funds funny
ghost giant given glass globe gloom glory going grace grade grain
grand grant graph grasp grass grave great green greet grief grind
gross group grove grown guard guess guest guide guild habit happy
harsh heart heavy hence horse hotel house human humor ideal image
imply index indoor inner input issue ivory joint judge juice label
large laser later laugh layer learn least legal lemon level light
limit linen liver lobby local lodge logic loose lover lower lucky
lunar lunch magic major manor maple march match mayor media mercy
metal might minor minus model money month moral motor mount mouse
mouth moved movie music naked nerve never newly night noble noise
north noted novel nurse occur ocean offer often olive onset opera
orbit order organ other outer owner oxide paint panel panic paper
party paste patch pause peace pearl phase phone photo piano piece
pilot pitch pixel place plain plane plant plate plaza plead plot
plumb point polar pound power press price pride prime prince print
prior prize probe proof proud prove pupil queen query quest quiet
quite quota quote radar radio raise rally ranch range rapid ratio
reach ready realm rebel refer reign relax reply rider ridge right
rival river robot rocky rough round route royal rural sadly saint
salad scale scare scene scope score scout sense serve seven shade
shake shall shame shape share shark sharp sheep sheer sheet shelf
shell shift shock shoot shore short shout shown sight since sixth
sixty skill skull slave sleep slice slide slope smart smell smile
smoke snake solar solid solve sorry sound south space spare speak
speed spend spent spice spike spine split spoke spoon sport spray
squad stack staff stage stake stall stand stare start state stays
steal steam steel steep steer stick stiff still stock stone stood
store storm story strap straw strip stuck study stuff style sugar
super surge swamp swear sweep sweet swept swift swing sword swore
taste teach teeth thank theme thick thing think third those three
threw throw tight timer tired title today token topic total touch
tough tower toxic trace track trade trail train trait trash treat
trend trial tribe trick troop truck truly trump trust truth tumor
twice twist ultra uncle under union unite unity until upper upset
urban usage usual valid value vapor venue verse video vigor vinyl
viral virus visit vital vivid vocal voice waste watch water weary
weave weigh weird wheat wheel where which while white whole whose
width witch woman world worry worse worst worth would wound wrath
write wrong wrote yield young youth"""
VALID_GUESSES = set(SOLUTION_WORDS)
for w in _EXTRA_GUESSES.split():
    if len(w) == 5 and w.isalpha():
        VALID_GUESSES.add(w.lower())

# ═══════════════════════════════════════════════════════════════════════════
#  CS Definitions — brief hint for each solution word
# ═══════════════════════════════════════════════════════════════════════════
DEFINITIONS = {
    "array": "Ordered collection of elements accessed by index.",
    "async": "Asynchronous execution — non-blocking operations.",
    "await": "Pauses async execution until a promise resolves.",
    "azure": "Microsoft's cloud computing platform.",
    "btree": "Self-balancing tree data structure for databases.",
    "build": "Compile or assemble software from source code.",
    "cache": "Fast temporary storage for frequently accessed data.",
    "cargo": "Rust's package manager and build tool.",
    "class": "Blueprint for creating objects in OOP.",
    "clone": "Create an exact copy of a data structure or repo.",
    "cloud": "On-demand computing resources over the internet.",
    "codec": "Encoder/decoder for compressing data streams.",
    "crash": "Sudden failure or termination of a program.",
    "crypt": "Encrypt or decrypt data for security.",
    "debug": "Find and fix errors in software.",
    "deque": "Double-ended queue — insert/remove from both ends.",
    "django": "Python web framework emphasizing rapid development.",
    "edges": "Connections between nodes in a graph.",
    "event": "An action or occurrence detected by the system.",
    "fetch": "Retrieve data from a network or database.",
    "fiber": "Lightweight thread managed in userspace.",
    "field": "A data member of a class or struct.",
    "final": "Keyword preventing further modification or inheritance.",
    "flask": "Lightweight Python web framework.",
    "float": "Floating-point number type for decimals.",
    "frame": "A single still image in a video or stack frame.",
    "fused": "Combined operations (e.g. GPU fused multiply-add).",
    "graph": "Data structure of nodes connected by edges.",
    "heaps": "Complete binary tree satisfying the heap property.",
    "hosts": "Computers that provide services on a network.",
    "http": "HyperText Transfer Protocol for the web.",
    "index": "Data structure that speeds up data retrieval.",
    "inode": "Unix data structure storing file metadata.",
    "inner": "Nested loop or class inside another.",
    "input": "Data received by a program from external sources.",
    "intel": "Major CPU manufacturer; also intelligence data.",
    "ioctl": "I/O control — system call for device-specific ops.",
    "joins": "SQL operations combining rows from multiple tables.",
    "kernel": "Core component of an OS managing resources.",
    "layer": "Abstraction level in networking (OSI) or graphics.",
    "lexer": "Converts source code text into tokens.",
    "linux": "Open-source Unix-like operating system kernel.",
    "lists": "Ordered mutable sequence data structure.",
    "local": "Variable scoped to a function or block.",
    "locks": "Synchronization primitive for mutual exclusion.",
    "logic": "Boolean operations and reasoning in computation.",
    "loops": "Repeated execution of a block of code.",
    "macro": "Automated sequence of commands or text expansion.",
    "merge": "Combine two sorted sequences into one.",
    "mixin": "Class providing methods for use in other classes.",
    "modal": "UI dialog that blocks interaction with the parent.",
    "model": "Data representation or ML trained system.",
    "mount": "Attach a filesystem to a directory tree.",
    "mutex": "Mutual exclusion lock for thread safety.",
    "named": "Identified by a name (e.g. named pipes, tuples).",
    "nodes": "Fundamental units in a data structure or network.",
    "nonce": "Number used once — prevents replay attacks.",
    "oauth": "Open Authorization protocol for delegated access.",
    "octal": "Base-8 number system (0-7 digits).",
    "panic": "Unrecoverable runtime error (Rust/Go).",
    "parse": "Analyze a string according to grammar rules.",
    "patch": "Small code change or OS-level data transfer.",
    "paths": "File system routes or graph traversal sequences.",
    "pipes": "IPC mechanism connecting output of one process to input of another.",
    "pixel": "Smallest addressable element of a display.",
    "point": "Geometric primitive; also pointer dereference.",
    "print": "Output text to the console or a printer.",
    "proxy": "Intermediary server forwarding client requests.",
    "pull": "Download remote changes to a local repository.",
    "push": "Upload local changes to a remote repository.",
    "query": "Request for data from a database or search engine.",
    "queue": "FIFO (First In, First Out) data structure.",
    "quick": "QuickSort — average O(n log n) sorting algorithm.",
    "radix": "Numeral system base; also Radix Sort algorithm.",
    "rails": "Ruby on Rails — MVC web application framework.",
    "range": "Sequence of numbers or iterable bounds.",
    "react": "JavaScript library for building user interfaces.",
    "ready": "State indicating a resource is available for use.",
    "regex": "Regular expressions for pattern matching.",
    "relay": "Forward data packets or signals between networks.",
    "render": "Generate visuals from a model or scene description.",
    "retry": "Repeat a failed operation automatically.",
    "route": "Determine the path for network traffic.",
    "rust": "Systems programming language focused on safety.",
    "scala": "JVM language combining OOP and functional programming.",
    "schema": "Blueprint defining database or document structure.",
    "scope": "Region of code where a variable is accessible.",
    "seeds": "Initial values for random number generators.",
    "serve": "Provide data or services to client requests.",
    "setup": "Installation or configuration of software.",
    "shell": "Command-line interface for OS interaction.",
    "shift": "Bitwise or array element shift operation.",
    "sigma": "Standard deviation symbol; also process monitor.",
    "sleep": "Suspend execution for a specified duration.",
    "slice": "Extract a sub-sequence from an array or string.",
    "slots": "Python mechanism to restrict dynamic attributes.",
    "sorts": "Algorithms that arrange elements in order.",
    "spark": "Apache Spark — distributed data processing engine.",
    "spawn": "Create a new process or thread.",
    "split": "Divide a string or array into parts.",
    "stack": "LIFO (Last In, First Out) data structure.",
    "state": "Current condition or data of a system at a point in time.",
    "steal": "Work-stealing scheduler pattern in parallelism.",
    "store": "Persist data in memory, disk, or database.",
    "stream": "Sequence of data elements processed incrementally.",
    "struct": "Composite data type grouping related fields.",
    "super": "Access a parent class in OOP inheritance.",
    "swift": "Apple's programming language for iOS/macOS.",
    "switch": "Multi-branch conditional control flow.",
    "sync": "Synchronize data or coordinate concurrent access.",
    "table": "Data organized in rows and columns (DB / hash).",
    "tensor": "Multi-dimensional array used in ML and math.",
    "tests": "Code that verifies correctness of other code.",
    "token": "Opaque string for authentication or parsing.",
    "torch": "PyTorch — ML framework for deep learning.",
    "trace": "Follow execution path; also distributed tracing.",
    "trait": "Collection of methods (Rust, Scala) for type composition.",
    "trans": "Database transaction or gender prefix.",
    "trees": "Hierarchical data structure with root and branches.",
    "tries": "Tree structure for efficient prefix-based retrieval.",
    "tuple": "Immutable ordered sequence of elements.",
    "types": "Classifications of data (int, str, float, etc.).",
    "valid": "Meeting the required constraints or conditions.",
    "value": "Data stored in a variable or memory location.",
    "vector": "Dynamic array or mathematical quantity with direction.",
    "views": "Virtual tables or MVC UI components.",
    "yield": "Produce a value from a generator function.",
    "zones": "DNS zones or availability zones in cloud.",
}

KB_ROWS = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    ["ENTER"] + list("ZXCVBNM") + ["DEL"],
]

# ═══════════════════════════════════════════════════════════════════════════
#  FlipTile — single grid cell with 3-D flip & pop animation
# ═══════════════════════════════════════════════════════════════════════════
class FlipTile(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(62, 62)
        self._letter = ""
        self._state = "empty"
        self._flip = 0.0
        self._scale = 1.0
        self._flip_anim = QPropertyAnimation(self, b"flip")
        self._flip_anim.setDuration(350)
        self._flip_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._pop_anim = QPropertyAnimation(self, b"scale")
        self._pop_anim.setDuration(100)
        self._pop_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._pop_anim.setStartValue(1.0)
        self._pop_anim.setEndValue(1.0)

    def _g_flip(self): return self._flip
    def _s_flip(self, v):
        self._flip = v; self.update()
    flip = Property(float, _g_flip, _s_flip)

    def _g_scale(self): return self._scale
    def _s_scale(self, v):
        self._scale = v; self.update()
    scale = Property(float, _g_scale, _s_scale)

    def set_letter(self, ch):
        self._letter = ch.upper() if ch else ""
        if ch and self._state == "empty":
            self._state = "tbd"
        # pop animation
        self._pop_anim.stop()
        self._pop_anim.setStartValue(1.0)
        self._pop_anim.setKeyValueAt(0.4, 1.15)
        self._pop_anim.setEndValue(1.0)
        self._pop_anim.start()
        self.update()

    def clear(self):
        self._letter = ""; self._state = "empty"
        self._flip = 0.0; self._scale = 1.0
        self.update()

    def get_letter(self): return self._letter

    def flip_to(self, state, delay_ms=0):
        self._applied = False
        self._new_state = state
        def on_change(v):
            if v >= 0.5 and not self._applied:
                self._state = self._new_state
                self._applied = True; self.update()
        self._flip_anim.valueChanged.connect(on_change)
        QTimer.singleShot(delay_ms, self._flip_anim.start)

    def _bg(self):
        return {"empty":TILE_EMPTY,"tbd":TILE_FILL,
                "correct":GREEN,"present":YELLOW,"absent":GRAY}.get(self._state,TILE_EMPTY)
    def _bord(self):
        if self._state in ("correct","present","absent"): return self._bg()
        return BORDER_E if self._state=="empty" else "#565758"

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w/2, h/2
        # flip
        angle = self._flip * 180
        sx = max(abs(math.cos(math.radians(angle))), 0.02)
        # pop scale
        s = self._scale
        rw, rh = w * sx * s, (h - 4) * s
        rx, ry = cx - rw/2, cy - rh/2
        p.setPen(QPen(QColor(self._bord()), 2))
        p.setBrush(QBrush(QColor(self._bg())))
        p.drawRoundedRect(rx, ry, rw, rh, 4, 4)
        if sx > 0.3 and self._letter:
            p.setPen(WHITE)
            p.setFont(QFont("Segoe UI", 28, QFont.Bold))
            p.drawText(rx, ry, rw, rh, Qt.AlignmentFlag.AlignCenter, self._letter)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  TileRow — 5 tiles, shakes and bounces
# ═══════════════════════════════════════════════════════════════════════════
class TileRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0,0,0,0); lay.setSpacing(5)
        self.tiles = [FlipTile() for _ in range(5)]
        for t in self.tiles: lay.addWidget(t)
        self._offset = 0

    def shake(self):
        for i, dx in enumerate([-6,6,-4,4,-2,2,0]):
            QTimer.singleShot(i*60, lambda d=dx: self._move(d))
        QTimer.singleShot(7*60+60, lambda: self._move(0))

    def bounce(self):
        for i, tile in enumerate(self.tiles):
            by = tile.pos().y()
            for j, dy in enumerate([-28,0,-14,0]):
                QTimer.singleShot(i*80+j*100, lambda t=tile,d=dy,b=by: t.move(t.pos().x(),b+d))
            QTimer.singleShot(i*80+400, lambda t=tile,b=by: t.move(t.pos().x(),b))

    def _move(self, dx):
        for tile in self.tiles:
            tile.move(tile.pos().x()-self._offset+dx, tile.pos().y())
        self._offset = dx


# ═══════════════════════════════════════════════════════════════════════════
#  KeyButton
# ═══════════════════════════════════════════════════════════════════════════
class KeyButton(QPushButton):
    key_pressed = Signal(str)
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._state = "unused"
        wide = text in ("ENTER","DEL")
        self.setFixedSize(68 if wide else 44, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._refresh()
        self.clicked.connect(lambda: self.key_pressed.emit(text))

    def set_state(self, state):
        prio = {"unused":0,"absent":1,"present":2,"correct":3}
        if prio.get(state,0) > prio.get(self._state,0):
            self._state = state; self._refresh()

    def _hover(self, base):
        c = QColor(base)
        c.setHsv(c.hsvHue(), max(c.hsvSaturation()-30,0), min(c.value()+30,255))
        return c.name()

    def _refresh(self):
        bg = {"unused":KB_BG,"absent":GRAY,"present":YELLOW,"correct":GREEN}.get(self._state,KB_BG)
        h = self._hover(bg)
        self.setStyleSheet(
            f"QPushButton{{color:{WHITE};background:{bg};border:none;border-radius:4px;padding:0;}}"
            f"QPushButton:hover{{background:{h};}}"
            f"QPushButton:pressed{{background:#58595b;}}")


# ═══════════════════════════════════════════════════════════════════════════
#  StatsDialog — win distribution, streaks, win %
# ═══════════════════════════════════════════════════════════════════════════
class StatsDialog(QDialog):
    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Statistics")
        self.setFixedSize(340, 440)
        self.setStyleSheet(f"background-color:{BG};color:{WHITE};")
        self._build(stats)

    def _build(self, st):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(24,24,24,24)

        # summary row
        row = QHBoxLayout()
        played = st["played"]
        won = st["won"]
        pct = int(won / played * 100) if played else 0
        for label, val in [("Played", played), ("Win %", pct),
                           ("Streak", st["streak"]),
                           ("Max", st["max_streak"])]:
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            n = QLabel(str(val))
            n.setFont(QFont("Segoe UI", 28, QFont.Bold))
            n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QLabel(label)
            l.setFont(QFont("Segoe UI", 10))
            l.setStyleSheet("color:#818384;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(n); col.addWidget(l)
            row.addLayout(col)
        lay.addLayout(row)

        # distribution title
        dt = QLabel("GUESS DISTRIBUTION")
        dt.setFont(QFont("Segoe UI", 11, QFont.Bold))
        dt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(dt)

        # bar chart
        dist = st.get("dist", [0]*6)
        max_d = max(dist) if max(dist) > 0 else 1
        for i, count in enumerate(dist):
            r = QHBoxLayout()
            r.setSpacing(6)
            num = QLabel(str(i+1))
            num.setFont(QFont("Segoe UI", 13, QFont.Bold))
            num.setFixedWidth(16)
            num.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            r.addWidget(num)

            bar = QFrame()
            bar.setFixedHeight(24)
            w = max(int(count / max_d * 200), 8) if count else 8
            bar.setFixedWidth(w)
            bar.setStyleSheet(
                f"background:{GREEN};border-radius:3px;" if count == max(dist) and count > 0
                else f"background:{GRAY};border-radius:3px;"
            )
            r.addWidget(bar)

            cnt = QLabel(str(count))
            cnt.setFont(QFont("Segoe UI", 13, QFont.Bold))
            cnt.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            r.addWidget(cnt)
            r.addStretch()
            lay.addLayout(r)

        # close button
        btn = QPushButton("CLOSE")
        btn.setFixedHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn.setStyleSheet(
            f"QPushButton{{color:{WHITE};background:{GREEN};border:none;border-radius:19px;}}"
            f"QPushButton:hover{{background:#6aaf5e;}}")
        btn.clicked.connect(self.close)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)


# ═══════════════════════════════════════════════════════════════════════════
#  HelpDialog — how to play
# ═══════════════════════════════════════════════════════════════════════════
class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How To Play")
        self.setFixedSize(380, 460)
        self.setStyleSheet(f"background-color:{BG};color:{WHITE};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(24,20,24,24)

        title = QLabel("HOW TO PLAY")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        rules = [
            "Guess the 5-letter Computer Science term in 6 tries.",
            "Each guess must be a valid 5-letter word.",
            "After each guess, tiles change color to show\nhow close you were:",
            "",
            "  GREEN  = correct letter, correct spot",
            "  YELLOW = correct letter, wrong spot",
            "  GRAY   = letter not in the word",
            "",
            "New features:",
            "  HARD MODE: revealed hints must be reused.",
            "  HINTS: reveal a letter (3 per game).",
            "  SHARE: copy emoji grid to clipboard.",
            "",
            "Press any key or click to close.",
        ]
        for line in rules:
            lbl = QLabel(line)
            lbl.setWordWrap(True)
            lbl.setFont(QFont("Segoe UI", 10))
            if line.startswith("  GREEN") or line.startswith("  YELLOW") or line.startswith("  GRAY"):
                color = GREEN if "GREEN" in line else YELLOW if "YELLOW" in line else GRAY
                lbl.setStyleSheet(f"color:{color};font-weight:bold;")
            elif line.startswith("New features"):
                lbl.setStyleSheet(f"color:{ACCENT};font-weight:bold;")
            lay.addWidget(lbl)

        lay.addStretch()


# ═══════════════════════════════════════════════════════════════════════════
#  CSWordleWindow — main game
# ═══════════════════════════════════════════════════════════════════════════
class CSWordleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CS Wordle v2")
        self.setFixedSize(500, 820)
        self.setStyleSheet(f"background-color:{BG};")

        self.MAX_GUESSES = 6
        self.WORD_LEN = 5
        self.target = ""
        self.row_idx = 0
        self.col_idx = 0
        self.game_over = False
        self.revealing = False
        self.hard_mode = False
        self.hints_left = 3
        self.rows = []
        self.keys = {}
        self.guess_results = []   # list of (guess, [states]) for share
        self._known = {}         # hard mode: {pos: letter} and {letter: set positions}
        self._known_exact = {}   # pos -> letter
        self._known_present = {} # letter -> set of positions that are NOT it

        # load persistent stats
        self.stats = self._load_stats()

        self._build_ui()
        self._new_game()

    # ────────── persistent stats ──────────

    @staticmethod
    def _load_stats():
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE) as f:
                    d = json.load(f)
                d.setdefault("dist", [0]*6)
                while len(d["dist"]) < 6:
                    d["dist"].append(0)
                return d
            except Exception:
                pass
        return {"played":0,"won":0,"streak":0,"max_streak":0,"dist":[0]*6,
                "hard_mode":False}

    def _save_stats(self):
        self.stats["hard_mode"] = self.hard_mode
        try:
            with open(STATS_FILE, "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass

    # ────────── UI ──────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(12,6,12,12)
        vbox.setSpacing(0)

        # ── header row ──
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)

        self._btn_help = self._icon_btn("?", 34, 34, "#565758")
        self._btn_help.clicked.connect(self._show_help)
        hbox.addWidget(self._btn_help)

        title = QLabel("CS WORDLE")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color:{WHITE};border:none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox.addWidget(title, stretch=1)

        self._btn_stats = self._icon_btn("S", 34, 34, "#565758")
        self._btn_stats.clicked.connect(self._show_stats)
        hbox.addWidget(self._btn_stats)
        vbox.addLayout(hbox)
        vbox.addSpacing(4)

        # ── toolbar ──
        tb = QHBoxLayout()
        tb.setContentsMargins(0,0,0,0)
        tb.setSpacing(8)

        self._btn_new = QPushButton("New Game")
        self._btn_new.setFixedHeight(30)
        self._btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_new.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._btn_new.setStyleSheet(
            f"QPushButton{{color:{WHITE};background:{GREEN};border:none;border-radius:15px;padding:0 16px;}}"
            f"QPushButton:hover{{background:#6aaf5e;}}")
        self._btn_new.clicked.connect(self._new_game)
        tb.addWidget(self._btn_new)

        self._btn_hard = QPushButton("Hard Mode: OFF")
        self._btn_hard.setFixedHeight(30)
        self._btn_hard.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_hard.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._refresh_hard_btn()
        self._btn_hard.clicked.connect(self._toggle_hard)
        tb.addWidget(self._btn_hard)

        self._btn_hint = QPushButton("Hint (3)")
        self._btn_hint.setFixedHeight(30)
        self._btn_hint.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_hint.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._refresh_hint_btn()
        self._btn_hint.clicked.connect(self._use_hint)
        tb.addWidget(self._btn_hint)

        self._btn_share = QPushButton("Share")
        self._btn_share.setFixedHeight(30)
        self._btn_share.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_share.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._btn_share.setStyleSheet(
            f"QPushButton{{color:{WHITE};background:#565758;border:none;border-radius:15px;padding:0 16px;}}"
            f"QPushButton:hover{{background:#787c7e;}}")
        self._btn_share.clicked.connect(self._share)
        tb.addWidget(self._btn_share)
        vbox.addLayout(tb)
        vbox.addSpacing(6)

        # ── subtitle ──
        sub = QLabel("Guess the 5-letter Computer Science term")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color:#818384;border:none;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(sub)
        vbox.addSpacing(2)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{BORDER_E};border:none;")
        vbox.addWidget(line)
        vbox.addSpacing(8)

        # ── grid ──
        grid_w = QWidget()
        grid_w.setStyleSheet("background:transparent;")
        gv = QVBoxLayout(grid_w)
        gv.setContentsMargins(0,0,0,0); gv.setSpacing(5)
        for _ in range(self.MAX_GUESSES):
            row = TileRow()
            self.rows.append(row)
            gv.addWidget(row)
        vbox.addWidget(grid_w, alignment=Qt.AlignmentFlag.AlignCenter)
        vbox.addSpacing(8)

        # ── toast ──
        self._toast = QLabel("")
        self._toast.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._toast.setStyleSheet(
            f"color:{WHITE};border:none;background:transparent;")
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast.setFixedHeight(26)
        vbox.addWidget(self._toast)
        vbox.addSpacing(4)

        # ── definition area (shown after game) ──
        self._def_label = QLabel("")
        self._def_label.setWordWrap(True)
        self._def_label.setFont(QFont("Segoe UI", 10))
        self._def_label.setStyleSheet(
            f"color:{ACCENT};border:1px solid {BORDER_E};border-radius:6px;"
            f"background:#1a1a2e;padding:8px;")
        self._def_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._def_label.setFixedHeight(0)
        self._def_label.setVisible(False)
        vbox.addWidget(self._def_label)
        vbox.addSpacing(4)

        # ── keyboard ──
        kb_w = QWidget()
        kb_w.setStyleSheet("background:transparent;")
        kbl = QVBoxLayout(kb_w)
        kbl.setContentsMargins(0,0,0,0); kbl.setSpacing(6)
        for r in KB_ROWS:
            rh = QHBoxLayout()
            rh.setSpacing(5)
            rh.setAlignment(Qt.AlignmentFlag.AlignCenter)
            for k in r:
                btn = KeyButton(k)
                btn.key_pressed.connect(self._on_key)
                rh.addWidget(btn)
                self.keys[k.upper()] = btn
                self.keys[k.lower()] = btn
            kbl.addLayout(rh)
        vbox.addWidget(kb_w)

        # ── keyboard shortcuts ──
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, lambda: self._on_key("ENTER"))
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self, lambda: self._on_key("DEL"))
        QShortcut(QKeySequence("Ctrl+H"), self, self._use_hint)
        QShortcut(QKeySequence("Ctrl+N"), self, self._new_game)

    def _icon_btn(self, text, w, h, bg):
        b = QPushButton(text)
        b.setFixedSize(w, h)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFont(QFont("Segoe UI", 14, QFont.Bold))
        b.setStyleSheet(
            f"QPushButton{{color:{WHITE};background:{bg};border:none;border-radius:{w//2}px;}}"
            f"QPushButton:hover{{background:#787c7e;}}")
        return b

    # ────────── hard mode ──────────

    def _refresh_hard_btn(self):
        on = self.hard_mode
        self._btn_hard.setText("Hard: ON" if on else "Hard: OFF")
        color = GREEN if on else "#565758"
        self._btn_hard.setStyleSheet(
            f"QPushButton{{color:{WHITE};background:{color};border:none;"
            f"border-radius:15px;padding:0 12px;}}"
            f"QPushButton:hover{{background:{'#6aaf5e' if on else '#787c7e'};}}")

    def _toggle_hard(self):
        self.hard_mode = not self.hard_mode
        self._refresh_hard_btn()
        self._save_stats()
        self._toast_show("Hard mode " + ("ON" if self.hard_mode else "OFF"))

    # ────────── hints ──────────

    def _refresh_hint_btn(self):
        n = self.hints_left
        self._btn_hint.setText(f"Hint ({n})")
        color = GREEN if n > 0 else GRAY
        hover = "#6aaf5e" if n > 0 else GRAY
        self._btn_hint.setStyleSheet(
            f"QPushButton{{color:{WHITE};background:{color};border:none;"
            f"border-radius:15px;padding:0 12px;}}"
            f"QPushButton:hover{{background:{hover};}}")

    def _use_hint(self):
        if self.game_over or self.revealing or self.hints_left <= 0:
            return
        # Find positions not yet correctly guessed
        current = "".join(t.get_letter() for t in self.rows[self.row_idx].tiles)
        unrevealed = [i for i in range(self.WORD_LEN)
                      if current[i] != self.target[i]]
        if not unrevealed:
            self._toast_show("All letters revealed!")
            return
        pos = random.choice(unrevealed)
        letter = self.target[pos]
        # Place it
        if self.col_idx <= pos:
            while self.col_idx < pos:
                self.rows[self.row_idx].tiles[self.col_idx].set_letter(letter if False else "")
                self.col_idx += 1
            self.rows[self.row_idx].tiles[pos].set_letter(letter)
            self.col_idx = pos + 1
        else:
            # overwrite
            self.rows[self.row_idx].tiles[pos].set_letter(letter)

        self.hints_left -= 1
        self._refresh_hint_btn()
        self._toast_show(f"Hint: position {pos+1} is '{letter}'")

    # ────────── game logic ──────────

    def _new_game(self):
        self.target = random.choice(SOLUTION_WORDS).upper()
        self.row_idx = 0; self.col_idx = 0
        self.game_over = False; self.revealing = False
        self.hints_left = 3; self.guess_results = []
        self._known_exact = {}; self._known_present = {}
        for row in self.rows:
            for t in row.tiles:
                t.clear()
        for btn in self.keys.values():
            btn._state = "unused"; btn._refresh()
        self._toast.setText("")
        self._def_label.setVisible(False)
        self._def_label.setFixedHeight(0)
        self._refresh_hint_btn()
        self.hard_mode = self.stats.get("hard_mode", False)
        self._refresh_hard_btn()

    def _on_key(self, key):
        if self.game_over or self.revealing:
            return
        if key == "ENTER":
            self._submit()
        elif key in ("DEL","\u232b","\u0008"):
            self._delete()
        elif len(key) == 1 and key.isalpha():
            self._type(key)

    def _type(self, ch):
        if self.col_idx >= self.WORD_LEN:
            return
        self.rows[self.row_idx].tiles[self.col_idx].set_letter(ch)
        self.col_idx += 1

    def _delete(self):
        if self.col_idx <= 0:
            return
        self.col_idx -= 1
        self.rows[self.row_idx].tiles[self.col_idx].clear()

    def _check_hard(self, guess_upper):
        """Return error message or empty string."""
        if not self.hard_mode:
            return ""
        # Must use all known-correct letters in their exact positions
        for pos, letter in self._known_exact.items():
            if guess_upper[pos] != letter:
                return f"Position {pos+1} must be '{letter}'"
        # Must include all known-present letters (not in positions they're known-absent)
        for letter, bad_positions in self._known_present.items():
            if letter not in guess_upper:
                return f"Must include '{letter}'"
            for bp in bad_positions:
                if guess_upper[bp] == letter:
                    return f"'{letter}' is not in position {bp+1}"
        return ""

    def _submit(self):
        if self.col_idx < self.WORD_LEN:
            self._toast_show("Not enough letters")
            self.rows[self.row_idx].shake()
            return

        guess_upper = "".join(
            t.get_letter() for t in self.rows[self.row_idx].tiles
        ).upper()
        guess_lower = guess_upper.lower()

        # Hard mode check
        hard_err = self._check_hard(guess_upper)
        if hard_err:
            self._toast_show(hard_err)
            self.rows[self.row_idx].shake()
            return

        if guess_lower not in VALID_GUESSES:
            self._toast_show("Not in word list")
            self.rows[self.row_idx].shake()
            return

        result = self._evaluate(guess_lower)
        self.guess_results.append((guess_lower, result))
        self.revealing = True

        # Update hard-mode knowledge BEFORE animation
        for i in range(self.WORD_LEN):
            if result[i] == "correct":
                self._known_exact[i] = guess_upper[i]
                # Remove from present if it was there
                if guess_upper[i] in self._known_present:
                    self._known_present[guess_upper[i]].discard(i)
            elif result[i] == "present":
                if guess_upper[i] not in self._known_present:
                    self._known_present[guess_upper[i]] = set()
                self._known_present[guess_upper[i]].add(i)
            elif result[i] == "absent":
                if guess_upper[i] in self._known_present:
                    self._known_present[guess_upper[i]].add(i)

        # Animate
        for c in range(self.WORD_LEN):
            tile = self.rows[self.row_idx].tiles[c]
            tile.flip_to(result[c], delay_ms=c * 320)
            kb = self.keys.get(guess_upper[c])
            if kb:
                kb.set_state(result[c])

        self.row_idx += 1
        self.col_idx = 0
        won = guess_upper == self.target
        lost = self.row_idx >= self.MAX_GUESSES and not won
        reveal_ms = self.WORD_LEN * 320 + 400

        if won:
            self.game_over = True
            self.stats["played"] += 1
            self.stats["won"] += 1
            self.stats["streak"] += 1
            self.stats["max_streak"] = max(self.stats["max_streak"], self.stats["streak"])
            self.stats["dist"][self.row_idx - 1] += 1
            self._save_stats()
            msgs = ["Genius!","Magnificent!","Impressive!","Splendid!","Great!","Phew!"]
            QTimer.singleShot(reveal_ms,
                lambda: self._win(msgs[min(self.row_idx-1, 5)]))
        elif lost:
            self.game_over = True
            self.stats["played"] += 1
            self.stats["streak"] = 0
            self._save_stats()
            QTimer.singleShot(reveal_ms, self._lose)
        else:
            QTimer.singleShot(reveal_ms, self._reveal_done)

    def _evaluate(self, guess):
        target = self.target
        gu = guess.upper()
        res = ["absent"] * self.WORD_LEN
        pool = list(target)
        for i in range(self.WORD_LEN):
            if gu[i] == target[i]:
                res[i] = "correct"; pool[i] = None
        for i in range(self.WORD_LEN):
            if res[i] == "correct": continue
            if gu[i] in pool:
                res[i] = "present"; pool[pool.index(gu[i])] = None
        return res

    def _reveal_done(self):
        self.revealing = False

    # ────────── win / lose ──────────

    def _show_definition(self):
        word = self.target.lower()
        defn = DEFINITIONS.get(word, f"A Computer Science term.")
        self._def_label.setText(f"  {self.target}  —  {defn}  ")
        self._def_label.setVisible(True)
        self._def_label.setFixedHeight(60)
        self._def_label.adjustSize()

    def _win(self, msg):
        self.revealing = False
        self.rows[self.row_idx - 1].bounce()
        self._toast_show(msg, 3000)
        self._show_definition()
        n = self.row_idx
        QTimer.singleShot(2000, lambda: QMessageBox.information(
            self, "You Won!",
            f"{msg}\n\nSolved in {n}/{self.MAX_GUESSES} tries.\n"
            f"The word was:  {self.target}\n\n"
            f"{DEFINITIONS.get(self.target.lower(), '')}",
            QMessageBox.StandardButton.Ok))

    def _lose(self):
        self.revealing = False
        self._show_definition()
        QMessageBox.information(
            self, "Game Over",
            f"Better luck next time!\n\n"
            f"The word was:  {self.target}\n\n"
            f"{DEFINITIONS.get(self.target.lower(), '')}",
            QMessageBox.StandardButton.Ok)

    # ────────── share ──────────

    def _share(self):
        if not self.guess_results:
            self._toast_show("Play a game first!")
            return
        emoji_map = {"correct": "\U0001f7e9", "present": "\U0001f7e8", "absent": "\u2b1b"}
        lines = ["CS Wordle v2", ""]
        for guess, states in self.guess_results:
            line = " ".join(emoji_map.get(s, "\u2b1b") for s in states)
            lines.append(line)
        text = "\n".join(lines)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self._toast_show("Copied to clipboard!", 2500)

    # ────────── dialogs ──────────

    def _show_stats(self):
        dlg = StatsDialog(self.stats, self)
        dlg.exec()

    def _show_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    # ────────── toast ──────────

    def _toast_show(self, text, ms=2000):
        self._toast.setText(text)
        try: self._toast_timer.stop()
        except AttributeError: pass
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(lambda: self._toast.setText(""))
        self._toast_timer.start(ms)

    # ────────── keyboard ──────────

    def keyPressEvent(self, ev):
        t = ev.text().upper()
        if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_key("ENTER")
        elif ev.key() == Qt.Key.Key_Backspace:
            self._on_key("DEL")
        elif t.isalpha() and len(t) == 1:
            self._on_key(t)
        else:
            super().keyPressEvent(ev)


# ═══════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(BG))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(WHITE))
    pal.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
    pal.setColor(QPalette.ColorRole.Text, QColor(WHITE))
    pal.setColor(QPalette.ColorRole.Button, QColor(KB_BG))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(WHITE))
    app.setPalette(pal)

    win = CSWordleWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()