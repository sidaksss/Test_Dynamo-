# -*- coding: utf-8 -*-
"""Zentrale Konfiguration des Nachtragsmodus.

Diese Datei darf angepasst werden (z. B. weitere GA-Kategorien).
Nach einer Änderung in pyRevit "Reload" ausführen.
"""

# Überwachte GA-Kategorien (Namen aus Autodesk.Revit.DB.BuiltInCategory).
# Nur Exemplare dieser Kategorien werden vom Nachtragsmodus gekennzeichnet.
GA_KATEGORIEN = [
    "OST_FireAlarmDevices",     # Brandmelder
    "OST_DataDevices",          # Datengeräte
    "OST_ElectricalEquipment",  # Elektrische Ausstattung
    "OST_ElectricalFixtures",   # Elektroinstallationen
    "OST_MechanicalEquipment",  # HLS-Bauteile
    "OST_CommunicationDevices", # Kommunikationsgeräte
    "OST_NurseCallDevices",     # Notrufgeräte
    "OST_SecurityDevices",      # Sicherheitsgeräte
]

# GUIDs aus GA_Nachtrag_SharedParameters_v2.txt (nicht ändern).
# Die Parameter werden über die GUID gesucht, nicht über den Namen.
GUID_NACHTRAGSNUMMER = "64465223-a5d0-43ca-9858-c232469951ec"
GUID_GRUND = "30f833d2-db94-41f5-a049-f75749aae47f"
GUID_ENTFALLEN = "0abb70bc-7034-4bf2-b141-0f955c8bf204"  # erst Stufe 2

# Parameter, die der Nachtragsmodus in Stufe 1 schreibt: Name -> GUID.
# NT_Vertragsstand, NT_Art und NT_Nachtrags_LN gehören den Dynamo-Skripten
# und werden hier bewusst nicht aufgeführt.
PARAMETER_STUFE_1 = [
    ("NT_Nachtragsnummer", GUID_NACHTRAGSNUMMER),
    ("NT_Grund", GUID_GRUND),
]

# Höchstlänge für den Grund des Nachtrags ("kurz").
MAX_LAENGE_GRUND = 100

# Worksharing: Nur neue Bauteile kennzeichnen, die dem aktuellen Benutzer
# gehören. Neu erstellte Bauteile gehören bis zur Synchronisierung ihrem
# Ersteller. Bauteile von Kollegen werden so nie verändert (Testfall T10).
NUR_EIGENE_BAUTEILE_KENNZEICHNEN = True

# Feste Kennung des Dynamic Model Updaters. Nicht ändern, sonst gilt der
# Updater in bestehenden Modellen als neuer Updater.
UPDATER_GUID = "47072b94-38bc-4511-9df3-11758a15a86c"

# Name des pyRevit-Reiters und der Gruppe (müssen zu den Ordnernamen passen).
REITER_NAME = "Nachtrag"
GRUPPE_NAME = "Nachtragsmodus"

# Abschnitt in der pyRevit-Benutzerkonfiguration (pyRevit_config.ini).
KONFIG_ABSCHNITT = "GA_Nachtrag"
