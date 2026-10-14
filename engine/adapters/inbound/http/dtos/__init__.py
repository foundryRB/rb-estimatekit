"""HTTP request and response DTOs for the REST API.

Each DTO is a Pydantic ``BaseModel`` living in its own file.
Request DTOs deserialise inbound JSON; response DTOs serialise
outbound JSON — keeping the adapter boundary explicit.
"""
