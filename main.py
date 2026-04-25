import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
from datetime import datetime, date
import os
import sys

# ── Thème ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BG_DARK   = "#071209"
BG_PANEL  = "#0d2012"
BG_CARD   = "#0a1a0f"
GREEN_PRI = "#3d9b52"
GREEN_LT  = "#7ec88a"
GREEN_DIM = "#4a7a52"
AMBER     = "#c8a84a"
RED_ALERT = "#c86a6a"
TEXT_PRI  = "#e8f5e9"
TEXT_SEC  = "#7ea886"
BORDER    = "#1e3a22"

# ── Base de données ────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agriwatch.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS parcelles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            proprietaire TEXT NOT NULL,
            superficie REAL NOT NULL,
            culture TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            zone TEXT,
            date_creation TEXT DEFAULT CURRENT_DATE
        );
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_parcelle INTEGER,
            date TEXT,
            type_obs TEXT,
            description TEXT,
            FOREIGN KEY(id_parcelle) REFERENCES parcelles(id)
        );
        CREATE TABLE IF NOT EXISTS rendements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_parcelle INTEGER,
            campagne TEXT,
            quantite REAL,
            unite TEXT DEFAULT 't/ha',
            date_recolte TEXT,
            FOREIGN KEY(id_parcelle) REFERENCES parcelles(id)
        );
        CREATE TABLE IF NOT EXISTS alertes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            message TEXT,
            niveau TEXT,
            date_envoi TEXT,
            destinataire TEXT,
            statut TEXT DEFAULT 'envoyé'
        );
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            role TEXT,
            telephone TEXT,
            zone TEXT
        );
    """)
    # Données démo
    c.execute("SELECT COUNT(*) FROM parcelles")
    if c.fetchone()[0] == 0:
        demo_parcelles = [
            ("Parcelle Mahamat K.", "Mahamat Koubra", 3.2, "Mil", 13.83, 20.83, "Abéché"),
            ("Parcelle Fatimé A.",  "Fatimé Abdelkader", 1.8, "Sorgho", 14.73, 20.45, "Biltine"),
            ("Groupement Dogdoré",  "COOP Dogdoré", 12.5, "Arachide", 13.50, 21.10, "Dogdoré"),
            ("COOP Adré Est",       "Coopérative Adré", 6.0, "Niébé", 13.46, 22.20, "Adré"),
            ("Parcelle Ibrahim Y.", "Ibrahim Youssouf", 2.1, "Maïs", 13.84, 20.87, "Abéché"),
        ]
        c.executemany(
            "INSERT INTO parcelles (nom,proprietaire,superficie,culture,latitude,longitude,zone) VALUES (?,?,?,?,?,?,?)",
            demo_parcelles
        )
        demo_alertes = [
            ("Sécheresse", "ALERTE: Risque sécheresse élevé. Réduire irrigation.", "Critique", datetime.now().strftime("%Y-%m-%d %H:%M"), "Biltine", "envoyé"),
            ("Ravageur",   "Chenilles légionnaires détectées sur parcelles mil.", "Critique", datetime.now().strftime("%Y-%m-%d %H:%M"), "Abéché", "envoyé"),
            ("Météo",      "Pluies prévues mer-jeu. Préparer les parcelles.", "Info", datetime.now().strftime("%Y-%m-%d %H:%M"), "Ouaddaï", "envoyé"),
        ]
        c.executemany(
            "INSERT INTO alertes (type,message,niveau,date_envoi,destinataire,statut) VALUES (?,?,?,?,?,?)",
            demo_alertes
        )
        demo_rendements = [
            (1, "2024-2025", 2.8, "t/ha", "2025-04-10"),
            (2, "2024-2025", 1.6, "t/ha", "2025-04-12"),
            (3, "2024-2025", 3.1, "t/ha", "2025-04-08"),
            (4, "2024-2025", 0.9, "t/ha", "2025-04-15"),
            (5, "2024-2025", 2.4, "t/ha", "2025-04-11"),
        ]
        c.executemany(
            "INSERT INTO rendements (id_parcelle,campagne,quantite,unite,date_recolte) VALUES (?,?,?,?,?)",
            demo_rendements
        )
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)

# ── Helpers UI ─────────────────────────────────────────────────────────────────
def make_label(parent, text, size=13, color=TEXT_PRI, bold=False, **kw):
    weight = "bold" if bold else "normal"
    return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size, weight),
                        text_color=color, **kw)

def make_btn(parent, text, cmd, width=140, color=GREEN_PRI, fg=TEXT_PRI, **kw):
    return ctk.CTkButton(parent, text=text, command=cmd, width=width,
                         fg_color=color, hover_color="#2d7042",
                         text_color=fg, font=("Segoe UI", 12),
                         corner_radius=8, **kw)

def card_frame(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=BG_PANEL,
                        border_color=BORDER, border_width=1,
                        corner_radius=10, **kw)

# ══════════════════════════════════════════════════════════════════════════════
# VUES
# ══════════════════════════════════════════════════════════════════════════════

class VueDashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()

    def build(self):
        # Titre
        make_label(self, "Vue générale — Campagne 2025", size=18, bold=True).pack(anchor="w", pady=(0,4))
        make_label(self, "Région du Ouaddaï · Abéché, Biltine", size=12, color=GREEN_DIM).pack(anchor="w", pady=(0,16))

        # Métriques
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", pady=(0,16))
        metrics_row.grid_columnconfigure((0,1,2,3), weight=1)

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM parcelles"); nb_parcelles = c.fetchone()[0]
        c.execute("SELECT AVG(quantite) FROM rendements"); avg_rend = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM utilisateurs"); nb_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM alertes"); nb_alertes = c.fetchone()[0]
        conn.close()

        stats = [
            ("Parcelles suivies", f"{nb_parcelles}", "ha enregistrées"),
            ("Rendement moyen",   f"{avg_rend:.1f} t/ha", "campagne 2025"),
            ("Agriculteurs",      f"{nb_users}", "utilisateurs actifs"),
            ("Alertes envoyées",  f"{nb_alertes}", "messages SMS"),
        ]
        for i, (label, val, sub) in enumerate(stats):
            f = card_frame(metrics_row)
            f.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            make_label(f, label, size=10, color=GREEN_DIM).pack(anchor="w", padx=14, pady=(12,2))
            make_label(f, val, size=22, bold=True, color=GREEN_LT).pack(anchor="w", padx=14)
            make_label(f, sub, size=10, color=GREEN_DIM).pack(anchor="w", padx=14, pady=(0,12))

        # Grille inférieure
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="both", expand=True)
        bottom.grid_columnconfigure((0,1), weight=1)

        # Parcelles récentes
        left = card_frame(bottom)
        left.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        make_label(left, "PARCELLES — RENDEMENTS", size=10, color=GREEN_DIM, bold=True).pack(anchor="w", padx=14, pady=(12,8))

        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT p.nom, p.culture, p.zone, r.quantite
                     FROM parcelles p LEFT JOIN rendements r ON r.id_parcelle=p.id
                     ORDER BY p.id LIMIT 6""")
        rows = c.fetchall(); conn.close()

        for nom, culture, zone, rend in rows:
            row_f = ctk.CTkFrame(left, fg_color=BG_CARD, corner_radius=6)
            row_f.pack(fill="x", padx=10, pady=3)
            make_label(row_f, nom, size=12, bold=True).pack(side="left", padx=10, pady=8)
            make_label(row_f, f"{culture} · {zone}", size=10, color=GREEN_DIM).pack(side="left")
            color = GREEN_LT if (rend or 0) >= 2 else (AMBER if (rend or 0) >= 1 else RED_ALERT)
            make_label(row_f, f"{rend or 0:.1f} t/ha", size=12, bold=True, color=color).pack(side="right", padx=10)

        # Alertes récentes
        right = card_frame(bottom)
        right.grid(row=0, column=1, padx=(8,0), sticky="nsew")
        make_label(right, "ALERTES RÉCENTES", size=10, color=GREEN_DIM, bold=True).pack(anchor="w", padx=14, pady=(12,8))

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT type, message, niveau, date_envoi, destinataire FROM alertes ORDER BY id DESC LIMIT 5")
        alertes = c.fetchall(); conn.close()

        niveau_color = {"Critique": RED_ALERT, "Avertissement": AMBER, "Info": "#4a9bc8"}
        for typ, msg, niveau, date_e, dest in alertes:
            af = ctk.CTkFrame(right, fg_color=BG_CARD, corner_radius=6)
            af.pack(fill="x", padx=10, pady=3)
            dot_color = niveau_color.get(niveau, GREEN_DIM)
            ctk.CTkLabel(af, text="●", text_color=dot_color, font=("Segoe UI", 10)).pack(side="left", padx=(10,4), pady=8)
            inner = ctk.CTkFrame(af, fg_color="transparent")
            inner.pack(side="left", fill="x", expand=True, pady=6)
            make_label(inner, msg[:55]+"…" if len(msg)>55 else msg, size=11).pack(anchor="w")
            make_label(inner, f"{dest} · {date_e[:10]}", size=9, color=GREEN_DIM).pack(anchor="w")


class VueParcelles(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()

    def build(self):
        # En-tête
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0,14))
        make_label(header, "Gestion des Parcelles", size=18, bold=True).pack(side="left")
        make_btn(header, "+ Nouvelle parcelle", self.ajouter, width=160).pack(side="right")

        # Tableau
        cols = ("Nom", "Propriétaire", "Superficie", "Culture", "Zone", "Rendement")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("AW.Treeview",
                        background=BG_PANEL, foreground=TEXT_PRI,
                        rowheight=34, fieldbackground=BG_PANEL,
                        borderwidth=0, font=("Segoe UI", 11))
        style.configure("AW.Treeview.Heading",
                        background=BG_CARD, foreground=GREEN_LT,
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("AW.Treeview", background=[("selected", "#1a4a22")])

        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                 style="AW.Treeview", selectmode="browse")
        widths = [200, 160, 100, 110, 110, 110]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        # Scrollbar
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        # Boutons bas
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=10)
        make_btn(btn_row, "Modifier", self.modifier, color=BG_PANEL, fg=GREEN_LT).pack(side="left", padx=(0,8))
        make_btn(btn_row, "Supprimer", self.supprimer, color="#3a1010", fg=RED_ALERT).pack(side="left")
        make_btn(btn_row, "Actualiser", self.charger, color=BG_CARD, fg=GREEN_DIM).pack(side="right")

        self.charger()

    def charger(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT p.id, p.nom, p.proprietaire, p.superficie, p.culture, p.zone,
                            COALESCE(r.quantite, 0)
                     FROM parcelles p
                     LEFT JOIN rendements r ON r.id_parcelle=p.id
                     ORDER BY p.id""")
        for row in c.fetchall():
            pid, nom, proprio, sup, culture, zone, rend = row
            self.tree.insert("", "end", iid=str(pid),
                             values=(nom, proprio, f"{sup} ha", culture, zone, f"{rend:.1f} t/ha"))
        conn.close()

    def ajouter(self):
        DialogParcelle(self, mode="ajout", callback=self.charger)

    def modifier(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionner une parcelle d'abord.")
            return
        DialogParcelle(self, mode="modif", pid=int(sel[0]), callback=self.charger)

    def supprimer(self):
        sel = self.tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette parcelle ?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM parcelles WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close()
            self.charger()


class DialogParcelle(ctk.CTkToplevel):
    def __init__(self, parent, mode="ajout", pid=None, callback=None):
        super().__init__(parent)
        self.title("Nouvelle parcelle" if mode == "ajout" else "Modifier parcelle")
        self.geometry("480x480")
        self.configure(fg_color=BG_DARK)
        self.grab_set()
        self.pid = pid
        self.callback = callback
        self.mode = mode
        self.build()
        if mode == "modif" and pid:
            self.prefill()

    def build(self):
        make_label(self, "Informations de la parcelle", size=15, bold=True).pack(pady=(20,16))
        fields = [
            ("Nom de la parcelle", "nom"),
            ("Propriétaire", "proprietaire"),
            ("Superficie (ha)", "superficie"),
            ("Culture principale", "culture"),
            ("Zone / Localité", "zone"),
            ("Latitude", "latitude"),
            ("Longitude", "longitude"),
        ]
        self.entries = {}
        for label, key in fields:
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=30, pady=4)
            make_label(f, label, size=11, color=GREEN_DIM).pack(anchor="w")
            e = ctk.CTkEntry(f, fg_color=BG_PANEL, border_color=BORDER,
                             text_color=TEXT_PRI, font=("Segoe UI", 12), height=34)
            e.pack(fill="x")
            self.entries[key] = e

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=20)
        make_btn(btn_row, "Enregistrer", self.sauvegarder, width=140).pack(side="left", padx=8)
        make_btn(btn_row, "Annuler", self.destroy, width=100, color=BG_PANEL, fg=TEXT_SEC).pack(side="left")

    def prefill(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT nom,proprietaire,superficie,culture,zone,latitude,longitude FROM parcelles WHERE id=?", (self.pid,))
        row = c.fetchone(); conn.close()
        if row:
            keys = ["nom","proprietaire","superficie","culture","zone","latitude","longitude"]
            for key, val in zip(keys, row):
                self.entries[key].insert(0, str(val or ""))

    def sauvegarder(self):
        try:
            nom = self.entries["nom"].get().strip()
            proprio = self.entries["proprietaire"].get().strip()
            sup = float(self.entries["superficie"].get())
            culture = self.entries["culture"].get().strip()
            zone = self.entries["zone"].get().strip()
            lat = float(self.entries["latitude"].get() or 0)
            lon = float(self.entries["longitude"].get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Vérifier les champs numériques.")
            return
        conn = get_conn(); c = conn.cursor()
        if self.mode == "ajout":
            c.execute("INSERT INTO parcelles (nom,proprietaire,superficie,culture,zone,latitude,longitude) VALUES (?,?,?,?,?,?,?)",
                      (nom, proprio, sup, culture, zone, lat, lon))
        else:
            c.execute("UPDATE parcelles SET nom=?,proprietaire=?,superficie=?,culture=?,zone=?,latitude=?,longitude=? WHERE id=?",
                      (nom, proprio, sup, culture, zone, lat, lon, self.pid))
        conn.commit(); conn.close()
        if self.callback:
            self.callback()
        self.destroy()


class VueAlertes(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0,14))
        make_label(header, "Alertes & SMS", size=18, bold=True).pack(side="left")
        make_btn(header, "+ Nouvelle alerte", self.nouvelle_alerte, width=160).pack(side="right")

        # Formulaire rapide
        form = card_frame(self)
        form.pack(fill="x", pady=(0,14))
        make_label(form, "ENVOYER UNE ALERTE SMS RAPIDE", size=10, color=GREEN_DIM, bold=True).pack(anchor="w", padx=14, pady=(12,8))

        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(0,8))
        row1.grid_columnconfigure((0,1,2), weight=1)

        make_label(row1, "Type", size=10, color=GREEN_DIM).grid(row=0, column=0, sticky="w")
        self.type_var = ctk.StringVar(value="Sécheresse")
        ctk.CTkOptionMenu(row1, variable=self.type_var, values=["Sécheresse","Ravageur","Météo","Rendement","Autre"],
                          fg_color=BG_PANEL, button_color=GREEN_PRI, font=("Segoe UI",11)).grid(row=1, column=0, padx=(0,8), sticky="ew")

        make_label(row1, "Niveau", size=10, color=GREEN_DIM).grid(row=0, column=1, sticky="w")
        self.niveau_var = ctk.StringVar(value="Critique")
        ctk.CTkOptionMenu(row1, variable=self.niveau_var, values=["Critique","Avertissement","Info"],
                          fg_color=BG_PANEL, button_color=GREEN_PRI, font=("Segoe UI",11)).grid(row=1, column=1, padx=4, sticky="ew")

        make_label(row1, "Destinataire", size=10, color=GREEN_DIM).grid(row=0, column=2, sticky="w")
        self.dest_entry = ctk.CTkEntry(row1, fg_color=BG_PANEL, border_color=BORDER,
                                       text_color=TEXT_PRI, font=("Segoe UI",11), placeholder_text="Zone ou groupe")
        self.dest_entry.grid(row=1, column=2, padx=(8,0), sticky="ew")

        make_label(form, "Message SMS", size=10, color=GREEN_DIM).pack(anchor="w", padx=14)
        self.msg_entry = ctk.CTkTextbox(form, height=60, fg_color=BG_PANEL, border_color=BORDER,
                                        text_color=TEXT_PRI, font=("Segoe UI",11))
        self.msg_entry.pack(fill="x", padx=14, pady=(4,10))
        make_btn(form, "Envoyer l'alerte SMS", self.envoyer_alerte, width=180).pack(anchor="e", padx=14, pady=(0,12))

        # Historique
        make_label(self, "HISTORIQUE DES ALERTES", size=10, color=GREEN_DIM, bold=True).pack(anchor="w", pady=(0,6))
        cols = ("Type", "Message", "Niveau", "Destinataire", "Date", "Statut")
        style = ttk.Style()
        style.configure("AW.Treeview", background=BG_PANEL, foreground=TEXT_PRI,
                        rowheight=30, fieldbackground=BG_PANEL, font=("Segoe UI", 10))
        self.tree = ttk.Treeview(self, columns=cols, show="headings", style="AW.Treeview")
        widths = [100, 260, 100, 120, 120, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.charger()

    def charger(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT type, message, niveau, destinataire, date_envoi, statut FROM alertes ORDER BY id DESC")
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    def envoyer_alerte(self):
        msg = self.msg_entry.get("1.0", "end").strip()
        dest = self.dest_entry.get().strip()
        if not msg or not dest:
            messagebox.showwarning("Champs manquants", "Remplir le message et le destinataire.")
            return
        conn = get_conn(); c = conn.cursor()
        c.execute("INSERT INTO alertes (type,message,niveau,date_envoi,destinataire,statut) VALUES (?,?,?,?,?,?)",
                  (self.type_var.get(), msg, self.niveau_var.get(),
                   datetime.now().strftime("%Y-%m-%d %H:%M"), dest, "envoyé"))
        conn.commit(); conn.close()
        self.msg_entry.delete("1.0", "end")
        self.dest_entry.delete(0, "end")
        messagebox.showinfo("Succès", f"Alerte envoyée à : {dest}")
        self.charger()

    def nouvelle_alerte(self):
        self.envoyer_alerte()


class VueRendements(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0,14))
        make_label(header, "Rendements Agricoles", size=18, bold=True).pack(side="left")
        make_btn(header, "+ Enregistrer rendement", self.ajouter, width=190).pack(side="right")

        # Résumé par culture
        summary = card_frame(self)
        summary.pack(fill="x", pady=(0,14))
        make_label(summary, "RÉSUMÉ PAR CULTURE", size=10, color=GREEN_DIM, bold=True).pack(anchor="w", padx=14, pady=(12,8))

        row_f = ctk.CTkFrame(summary, fg_color="transparent")
        row_f.pack(fill="x", padx=14, pady=(0,12))

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT culture, AVG(r.quantite), COUNT(*) FROM parcelles p JOIN rendements r ON r.id_parcelle=p.id GROUP BY culture")
        cultures = c.fetchall(); conn.close()

        for i, (culture, avg, nb) in enumerate(cultures):
            cf = card_frame(row_f)
            cf.pack(side="left", padx=6, expand=True, fill="x")
            make_label(cf, culture, size=12, bold=True).pack(padx=12, pady=(10,2))
            color = GREEN_LT if (avg or 0) >= 2 else (AMBER if (avg or 0) >= 1 else RED_ALERT)
            make_label(cf, f"{avg or 0:.2f} t/ha", size=20, bold=True, color=color).pack(padx=12)
            make_label(cf, f"{nb} parcelle{'s' if nb>1 else ''}", size=10, color=GREEN_DIM).pack(padx=12, pady=(0,10))

        # Tableau détaillé
        make_label(self, "DÉTAIL DES RENDEMENTS", size=10, color=GREEN_DIM, bold=True).pack(anchor="w", pady=(0,6))
        cols = ("Parcelle", "Culture", "Zone", "Campagne", "Quantité", "Unité", "Date récolte")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", style="AW.Treeview")
        widths = [180, 100, 110, 100, 90, 70, 110]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.charger()

    def charger(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT p.nom, p.culture, p.zone, r.campagne, r.quantite, r.unite, r.date_recolte
                     FROM rendements r JOIN parcelles p ON r.id_parcelle=p.id ORDER BY r.id DESC""")
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    def ajouter(self):
        DialogRendement(self, callback=self.charger)


class DialogRendement(ctk.CTkToplevel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.title("Enregistrer un rendement")
        self.geometry("420x360")
        self.configure(fg_color=BG_DARK)
        self.grab_set()
        self.callback = callback
        self.build()

    def build(self):
        make_label(self, "Nouveau rendement", size=15, bold=True).pack(pady=(20,14))
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id, nom FROM parcelles ORDER BY nom")
        parcelles = c.fetchall(); conn.close()

        self.parcelle_map = {nom: pid for pid, nom in parcelles}
        self.parcelle_var = ctk.StringVar(value=parcelles[0][1] if parcelles else "")

        fields = [("Parcelle", None), ("Campagne", "campagne"), ("Quantité (t/ha)", "quantite"), ("Date récolte (YYYY-MM-DD)", "date")]
        self.entries = {}

        for label, key in fields:
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=30, pady=5)
            make_label(f, label, size=11, color=GREEN_DIM).pack(anchor="w")
            if key is None:
                ctk.CTkOptionMenu(f, variable=self.parcelle_var,
                                  values=[n for _,n in parcelles],
                                  fg_color=BG_PANEL, button_color=GREEN_PRI,
                                  font=("Segoe UI",11)).pack(fill="x")
            else:
                e = ctk.CTkEntry(f, fg_color=BG_PANEL, border_color=BORDER,
                                 text_color=TEXT_PRI, font=("Segoe UI",12), height=34)
                if key == "campagne": e.insert(0, "2024-2025")
                if key == "date": e.insert(0, date.today().isoformat())
                e.pack(fill="x")
                self.entries[key] = e

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)
        make_btn(btn_row, "Enregistrer", self.sauvegarder, width=140).pack(side="left", padx=8)
        make_btn(btn_row, "Annuler", self.destroy, width=100, color=BG_PANEL, fg=TEXT_SEC).pack(side="left")

    def sauvegarder(self):
        try:
            pid = self.parcelle_map[self.parcelle_var.get()]
            campagne = self.entries["campagne"].get().strip()
            quantite = float(self.entries["quantite"].get())
            date_r = self.entries["date"].get().strip()
        except (ValueError, KeyError):
            messagebox.showerror("Erreur", "Vérifier les champs.")
            return
        conn = get_conn(); c = conn.cursor()
        c.execute("INSERT INTO rendements (id_parcelle,campagne,quantite,unite,date_recolte) VALUES (?,?,?,'t/ha',?)",
                  (pid, campagne, quantite, date_r))
        conn.commit(); conn.close()
        if self.callback: self.callback()
        self.destroy()


class VueUtilisateurs(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()

    def build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0,14))
        make_label(header, "Gestion des Utilisateurs", size=18, bold=True).pack(side="left")
        make_btn(header, "+ Ajouter utilisateur", self.ajouter, width=180).pack(side="right")

        cols = ("Nom", "Rôle", "Téléphone", "Zone affectée")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", style="AW.Treeview")
        widths = [200, 140, 150, 160]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)
        make_btn(self, "Actualiser", self.charger, width=120, color=BG_CARD, fg=GREEN_DIM).pack(anchor="e", pady=8)
        self.charger()

    def charger(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT nom, role, telephone, zone FROM utilisateurs ORDER BY id DESC")
        for row in c.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    def ajouter(self):
        DialogUtilisateur(self, callback=self.charger)


class DialogUtilisateur(ctk.CTkToplevel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.title("Ajouter un utilisateur")
        self.geometry("400x320")
        self.configure(fg_color=BG_DARK)
        self.grab_set()
        self.callback = callback
        self.build()

    def build(self):
        make_label(self, "Nouvel utilisateur", size=15, bold=True).pack(pady=(20,14))
        fields = [("Nom complet", "nom"), ("Téléphone", "telephone"), ("Zone affectée", "zone")]
        self.entries = {}
        for label, key in fields:
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=30, pady=5)
            make_label(f, label, size=11, color=GREEN_DIM).pack(anchor="w")
            e = ctk.CTkEntry(f, fg_color=BG_PANEL, border_color=BORDER,
                             text_color=TEXT_PRI, font=("Segoe UI",12), height=34)
            e.pack(fill="x")
            self.entries[key] = e

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=30, pady=5)
        make_label(f, "Rôle", size=11, color=GREEN_DIM).pack(anchor="w")
        self.role_var = ctk.StringVar(value="Agriculteur")
        ctk.CTkOptionMenu(f, variable=self.role_var,
                          values=["Agriculteur","Agent terrain","Admin","Responsable ONG"],
                          fg_color=BG_PANEL, button_color=GREEN_PRI, font=("Segoe UI",11)).pack(fill="x")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)
        make_btn(btn_row, "Enregistrer", self.sauvegarder, width=140).pack(side="left", padx=8)
        make_btn(btn_row, "Annuler", self.destroy, width=100, color=BG_PANEL, fg=TEXT_SEC).pack(side="left")

    def sauvegarder(self):
        nom = self.entries["nom"].get().strip()
        tel = self.entries["telephone"].get().strip()
        zone = self.entries["zone"].get().strip()
        if not nom:
            messagebox.showwarning("Erreur", "Le nom est obligatoire.")
            return
        conn = get_conn(); c = conn.cursor()
        c.execute("INSERT INTO utilisateurs (nom,role,telephone,zone) VALUES (?,?,?,?)",
                  (nom, self.role_var.get(), tel, zone))
        conn.commit(); conn.close()
        if self.callback: self.callback()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# APP PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

class AgriWatchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AgriWatch Tchad — Système Intelligent de Surveillance Agricole")
        self.geometry("1200x720")
        self.minsize(1000, 640)
        self.configure(fg_color=BG_DARK)
        self.current_view = None
        self.build_ui()
        self.show_view("dashboard")

    def build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#071209",
                                    corner_radius=0, border_width=1, border_color=BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_f.pack(fill="x", padx=16, pady=(20,16))
        logo_icon = ctk.CTkFrame(logo_f, width=36, height=36, fg_color="#1a6b2e", corner_radius=8)
        logo_icon.pack(side="left")
        logo_icon.pack_propagate(False)
        make_label(logo_icon, "🌱", size=18).place(relx=0.5, rely=0.5, anchor="center")
        txt_f = ctk.CTkFrame(logo_f, fg_color="transparent")
        txt_f.pack(side="left", padx=10)
        make_label(txt_f, "AgriWatch", size=13, bold=True, color=GREEN_LT).pack(anchor="w")
        make_label(txt_f, "Tchad · Système Agricole", size=9, color=GREEN_DIM).pack(anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=0, pady=0)

        # Navigation
        nav_items = [
            ("dashboard",     "📊", "Vue générale"),
            ("parcelles",     "🗂️", "Parcelles"),
            ("rendements",    "📈", "Rendements"),
            ("alertes",       "📱", "Alertes SMS"),
            ("utilisateurs",  "👥", "Utilisateurs"),
        ]
        self.nav_btns = {}
        ctk.CTkLabel(self.sidebar, text="TABLEAU DE BORD", font=("Segoe UI", 9),
                     text_color="#2e5c36").pack(anchor="w", padx=16, pady=(14,4))

        for key, icon, label in nav_items:
            if key == "alertes":
                ctk.CTkLabel(self.sidebar, text="COMMUNICATION", font=("Segoe UI", 9),
                             text_color="#2e5c36").pack(anchor="w", padx=16, pady=(10,4))
            if key == "utilisateurs":
                ctk.CTkLabel(self.sidebar, text="GESTION", font=("Segoe UI", 9),
                             text_color="#2e5c36").pack(anchor="w", padx=16, pady=(10,4))
            btn = ctk.CTkButton(self.sidebar, text=f"  {icon}  {label}",
                                anchor="w", font=("Segoe UI", 12),
                                fg_color="transparent", hover_color="#0f2014",
                                text_color=GREEN_DIM, corner_radius=0, height=38,
                                command=lambda k=key: self.show_view(k))
            btn.pack(fill="x")
            self.nav_btns[key] = btn

        # Statut
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER).pack(fill="x", side="bottom", pady=(0,50))
        status_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_f.pack(side="bottom", fill="x", padx=16, pady=12)
        make_label(status_f, "● Système opérationnel", size=10, color=GREEN_PRI).pack(anchor="w")
        make_label(status_f, "Région du Ouaddaï", size=9, color=GREEN_DIM).pack(anchor="w")

        # Contenu principal
        self.main_area = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

        self.content_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent",
                                                     scrollbar_button_color=GREEN_DIM)
        self.content_frame.pack(fill="both", expand=True, padx=28, pady=24)

    def show_view(self, key):
        # Mettre à jour style boutons nav
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(fg_color="#0d2912", text_color=GREEN_LT)
            else:
                btn.configure(fg_color="transparent", text_color=GREEN_DIM)

        # Vider contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        views = {
            "dashboard":    VueDashboard,
            "parcelles":    VueParcelles,
            "rendements":   VueRendements,
            "alertes":      VueAlertes,
            "utilisateurs": VueUtilisateurs,
        }
        cls = views.get(key, VueDashboard)
        view = cls(self.content_frame)
        view.pack(fill="both", expand=True)
        self.current_view = key


if __name__ == "__main__":
    init_db()
    app = AgriWatchApp()
    app.mainloop()
