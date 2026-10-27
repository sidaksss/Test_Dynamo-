# -*- coding: utf-8 -*-
"""Wird von pyRevit beim Start von Revit und bei "Reload" ausgeführt.

1. Aktiven Nachtrag aus der Benutzerkonfiguration laden.
2. Dynamic Model Updater registrieren (optional, für alle Dokumente).
3. Idling-Handler für Hinweise und Button-Zustand anmelden.
"""

import os
import sys

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _LIB not in sys.path:
    sys.path.append(_LIB)

from pyrevit import HOST_APP, script

from ga_nachtrag import hinweise, updater, zustand

logger = script.get_logger()

try:
    zustand.lade_nachtrag_aus_benutzerkonfiguration()
except Exception as fehler:
    logger.error(u"Nachtragsmodus: Benutzerkonfiguration nicht lesbar: {}"
                 .format(fehler))

try:
    updater.registriere_updater(HOST_APP.uiapp)
except Exception as fehler:
    logger.error(u"Nachtragsmodus: Updater konnte nicht registriert werden. "
                 u"Neue Bauteile werden NICHT gekennzeichnet. Ursache: {}"
                 .format(fehler))

try:
    hinweise.abonniere_leerlauf(HOST_APP.uiapp)
except Exception as fehler:
    logger.error(u"Nachtragsmodus: Hinweise nicht verfügbar: {}".format(fehler))
