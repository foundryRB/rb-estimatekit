"""Outbound ports — interfaces the engine needs from the outside world.

These Protocols define what the application layer *requires* from
infrastructure: persistence, file writers, template access, etc.
Concrete implementations live in ``engine.adapters.outbound``.
"""
