# Field Data Encryption for Odoo 19

This addon lets an administrator choose a model and a stored text field, then encrypt values written into that field.

## What it does

- Admin creates an encryption rule for a model field
- New writes to that field are encrypted automatically
- ORM reads are decrypted before values are shown in normal list/form reads
- Existing records can be encrypted with the **Encrypt Existing Records** button
- Uses Fernet symmetric encryption from Python's `cryptography` package

## Supported fields

- `char`
- `text`
- `html`

Only **stored** fields are supported.

## Required server config

Set one of these in `odoo.conf`:

```ini
[options]
field_encryption_key=<FERNET_KEY>
```

Or environment-specific:

```ini
[options]
running_env=dev
field_encryption_key_dev=<FERNET_KEY>
```

Generate a key with:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Important limitations

Because Fernet encryption is non-deterministic:

- encrypted fields are **not searchable**
- encrypted fields are **not filterable/groupable**
- domains on encrypted fields will not behave like plain text
- business logic depending on raw plaintext values should be reviewed carefully

If you need searching on encrypted content, the design needs a companion hash/index strategy.
