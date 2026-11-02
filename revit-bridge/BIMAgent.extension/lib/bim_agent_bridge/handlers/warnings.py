# -*- coding: utf-8 -*-
"""Extraccion cruda para get_warnings. Solo lectura. IronPython 2.7."""
from bim_agent_bridge import serializers


def run(doc, version, args):
    warnings = []
    for failure in doc.GetWarnings():
        ids = list(failure.GetFailingElements()) + list(failure.GetAdditionalElements())
        refs = [serializers.element_ref(doc, element_id) for element_id in ids]
        warnings.append({
            "description": failure.GetDescriptionText(),
            "severity": str(failure.GetSeverity()),
            "elements": [ref for ref in refs if ref is not None],
        })
    return {"warnings": warnings}
