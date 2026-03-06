import tkinter as tk
from PIL import Image, ImageTk
import random
import pygame
import os
import sys
import time
import pygetwindow as gw

# --- DYNAMIC PATHING ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BOB_FOLDER = os.path.join(SCRIPT_DIR, "Bob")

class BobPet:
    def __init__(self):
        # 1. Root Setup
        self.root = tk.Tk()
        self.root.withdraw() # Hide the main manager window
        
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # 2. Window Setup
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.trans_color = '#abcdef'
        self.window.wm_attributes('-transparentcolor', self.trans_color)
        self.window.configure(bg=self.trans_color)

        # 3. Load Assets
        self.bob_img = self.prepare_img("bob.png")
        self.hand_img = self.prepare_img("Bob_Hand.png")
        
        if self.bob_img:
            self.label = tk.Label(self.window, image=self.bob_img, bg=self.trans_color, bd=0)
        else:
            self.label = tk.Label(self.window, text="BOB MISSING", bg="hotpink", fg="white")
        self.label.pack()

        self.note_label = tk.Label(self.window, text="", bg="white", wraplength=100, font=("Arial", 8, "bold"), bd=1, relief="solid")

        # 4. Audio
        pygame.mixer.init()
        self.idle_path = os.path.join(BOB_FOLDER, "Idle.mp3")
        rag_path = os.path.join(BOB_FOLDER, "ragdoll.mp3")
        self.ragdoll_snd = pygame.mixer.Sound(rag_path) if os.path.exists(rag_path) else None

        # 5. Physics & State
        self.bob_w, self.bob_h = 64, 64
        self.x, self.y = random.randint(100, self.screen_w-100), 50
        self.dx, self.dy = random.choice([-3, 3]), 0
        self.gravity = 0.7
        self.is_sitting = False
        self.was_sitting = False
        self.is_grabbed = False
        self.is_ragdoll = False
        self.last_action_check = time.time()

        # Bindings
        self.label.bind("<Button-1>", self.start_grab)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonRelease-1>", self.stop_grab)
        self.label.bind("<Button-3>", lambda e: self.root.destroy())

        self.run_loop()
        self.root.mainloop()

    def prepare_img(self, name):
        path = os.path.join(BOB_FOLDER, name)
        if os.path.exists(path):
            return ImageTk.PhotoImage(Image.open(path).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS))
        return None

    def start_grab(self, event):
        self.is_grabbed, self.is_ragdoll, self.is_sitting = True, False, False
        self.offset_x, self.offset_y = event.x, event.y

    def on_drag(self, event):
        if self.is_grabbed:
            self.x = self.window.winfo_pointerx() - self.offset_x
            self.y = self.window.winfo_pointery() - self.offset_y

    def stop_grab(self, event):
        self.is_grabbed = False

    def handle_collision(self, plat_y):
        self.y = plat_y - self.bob_h
        if self.is_ragdoll:
            if abs(self.dy) > 3: # Bounce!
                if self.ragdoll_snd: self.ragdoll_snd.play()
                self.dy *= -0.6 
            else:
                self.is_ragdoll, self.is_sitting, self.dy = False, True, 0
        else:
            self.is_sitting, self.dy = True, 0

    def run_loop(self):
        # 1. Get Windows
        plats = [{'top': w.top, 'left': w.left, 'right': w.right} 
                 for w in gw.getAllWindows() if w.visible and w.title != "" and w.height > 50]

        # 2. Action Roll (Every 10s)
        now = time.time()
        if now - self.last_action_check >= 10:
            self.last_action_check = now
            roll = random.random()
            if roll < 0.2: # Sound
                try: pygame.mixer.Sound(self.idle_path).play()
                except: pass
            if roll < 0.15 and self.is_sitting: # Note
                self.show_note()

        # 3. Physics
        if not self.is_grabbed:
            if self.is_sitting and random.random() < 0.01: # Jump
                self.dy = -12
                self.is_sitting = False
            
            if self.was_sitting and not self.is_sitting and random.random() < 0.35:
                self.is_ragdoll = True

            if not self.is_sitting:
                self.dy += self.gravity
                self.y += self.dy
            
            if not self.is_ragdoll: self.x += self.dx
            else: self.x += self.dx * 0.95

            self.was_sitting = self.is_sitting
            self.is_sitting = False

            # Collisions
            if self.y + self.bob_h >= self.screen_h - 40: self.handle_collision(self.screen_h - 40)
            if self.dy >= 0:
                for p in plats:
                    if p['left'] < self.x + 32 < p['right'] and abs((self.y + self.bob_h) - p['top']) < 15:
                        self.handle_collision(p['top'])

            if self.x <= 0 or self.x >= self.screen_w - 64: 
                self.dx *= -1
                if self.is_ragdoll and self.ragdoll_snd: self.ragdoll_snd.play()

            self.window.geometry(f"+{int(self.x)}+{int(self.y)}")

        self.root.after(30, self.run_loop)

    def show_note(self):
        p = os.path.join(BOB_FOLDER, "BobNote.txt")
        if os.path.exists(p):
            with open(p, 'r') as f:
                lines = f.readlines()
                if lines:
                    self.label.config(image=self.hand_img)
                    self.note_label.config(text=random.choice(lines).strip())
                    self.note_label.pack(side="top")
                    self.root.after(4000, self.hide_note)

    def hide_note(self):
        self.note_label.pack_forget()
        self.label.config(image=self.bob_img)

if __name__ == "__main__":
    BobPet()