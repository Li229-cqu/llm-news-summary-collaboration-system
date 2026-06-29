"""Compatibility shim exposing DBUtils.PooledDB for local verification scripts."""

from dbutils.pooled_db import PooledDB

__all__ = ["PooledDB"]
