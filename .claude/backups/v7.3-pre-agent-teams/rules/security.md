# Security Rules

## Blocked Patterns (ALWAYS DENY)

### Destructive File Operations
```
rm -rf /
sudo rm -rf
chmod 777
```

### SQL Injection / Data Destruction
```
DROP TABLE
DROP DATABASE
DELETE FROM
TRUNCATE TABLE
```

### System Control
```
shutdown
reboot
init 0
init 6
```

### Remote Code Execution
```
curl | bash
curl | sh
wget | bash
wget | sh
```

### Fork Bombs & Denial of Service
```
:(){:|:&};:
```

### Disk/Device Operations
```
mkfs.
dd if=
> /dev/sda
```

## Sensitive Files (Auto-Blocked)

| Pattern | Reason |
|---------|--------|
| `.env*` | Environment secrets |
| `*credentials*` | API keys, passwords |
| `.ssh/id_*` | SSH private keys |
| `**/secrets/**` | Secret directories |
| `*.pem`, `*.key` | Private keys |

## Code Security

### Input Validation
- Sanitize all user inputs
- Use parameterized queries for SQL
- Escape HTML output to prevent XSS

### Authentication
- Never hardcode credentials
- Use environment variables for secrets
- Implement proper session management

### Dependencies
- Check for known vulnerabilities before adding
- Keep dependencies updated
- Use lockfiles (package-lock.json, poetry.lock)

## Reporting

If security vulnerability detected:
1. Do NOT commit the vulnerable code
2. Report to user immediately
3. Suggest remediation
