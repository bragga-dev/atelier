def drop_none(fields: dict) -> dict:
    """Remove as chaves cujo valor é None — só os campos realmente informados seguem pro repository."""
    return {key: value for key, value in fields.items() if value is not None}