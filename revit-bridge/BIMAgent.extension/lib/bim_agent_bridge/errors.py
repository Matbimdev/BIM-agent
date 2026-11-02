# -*- coding: utf-8 -*-
"""Errores tipados del bridge. IronPython 2.7."""


class BridgeError(Exception):
    """Error esperado: viaja al mcp-server como {type, message, action}."""
    status = 500
    error_type = "InternalError"

    def __init__(self, message, action):
        Exception.__init__(self, message)
        self.message = message
        self.action = action

    def to_dict(self):
        return {"error": {"type": self.error_type,
                          "message": self.message,
                          "action": self.action}}


class NoDocument(BridgeError):
    status = 409
    error_type = "NoDocument"


class CategoryNotFound(BridgeError):
    status = 404
    error_type = "CategoryNotFound"
