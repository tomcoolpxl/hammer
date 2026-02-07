"""Entrypoint models for HAMMER spec."""

from typing import List, Optional

from pydantic import BaseModel

from hammer.validators import SafeIdentifier, SafeRelativePath


class ProvidedFile(BaseModel):
    """A file provided by the assignment to students."""
    source: SafeRelativePath
    destination: SafeRelativePath


class Entrypoints(BaseModel):
    playbook_path: SafeRelativePath
    required_roles: Optional[List[SafeIdentifier]] = None
    required_files: Optional[List[SafeRelativePath]] = None
    provided_files: Optional[List[ProvidedFile]] = None
