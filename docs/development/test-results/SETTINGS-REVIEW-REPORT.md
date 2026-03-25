# Settings Migration Review Report

## ⚠️  Environment-Specific Settings (Review Required)

These settings contain URLs, paths, or hostnames that may differ between environments:

### `AUTH_LDAP_1_BIND_DN`
**Source value:** `cn=ansible-svc-backup,ou=ServiceAccounts,dc=example,dc=com`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_BIND_DN': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_CONNECTION_OPTIONS`
**Source value:** `{'OPT_REFERRALS': 0, 'OPT_NETWORK_TIMEOUT': 30}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_CONNECTION_OPTIONS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_DENY_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_DENY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_GROUP_SEARCH`
**Source value:** `['ou=Groups,dc=example,dc=com', 'SCOPE_SUBTREE', '(objectClass=groupOfNames)']`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_GROUP_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_GROUP_TYPE`
**Source value:** `GroupOfNamesType`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_GROUP_TYPE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_GROUP_TYPE_PARAMS`
**Source value:** `{'member_attr': 'member', 'name_attr': 'cn'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_GROUP_TYPE_PARAMS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_ORGANIZATION_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_ORGANIZATION_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_REQUIRE_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_REQUIRE_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_SERVER_URI`
**Source value:** `ldaps://ldap-backup.example.com:636`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_SERVER_URI': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_START_TLS`
**Source value:** `False`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_START_TLS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_TEAM_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_TEAM_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_USER_ATTR_MAP`
**Source value:** `{'email': 'mail', 'last_name': 'sn', 'first_name': 'givenName'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_USER_ATTR_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_USER_DN_TEMPLATE`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_USER_DN_TEMPLATE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_USER_FLAGS_BY_GROUP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_USER_FLAGS_BY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_1_USER_SEARCH`
**Source value:** `['ou=Users,dc=example,dc=com', 'SCOPE_SUBTREE', '(uid=%(user)s)']`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_USER_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_BIND_DN`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_BIND_DN': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_CONNECTION_OPTIONS`
**Source value:** `{'OPT_REFERRALS': 0, 'OPT_NETWORK_TIMEOUT': 30}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_CONNECTION_OPTIONS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_DENY_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_DENY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_GROUP_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_GROUP_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_GROUP_TYPE`
**Source value:** `MemberDNGroupType`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_GROUP_TYPE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_GROUP_TYPE_PARAMS`
**Source value:** `{'member_attr': 'member', 'name_attr': 'cn'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_GROUP_TYPE_PARAMS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_ORGANIZATION_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_ORGANIZATION_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_REQUIRE_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_REQUIRE_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_SERVER_URI`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_SERVER_URI': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_START_TLS`
**Source value:** `False`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_START_TLS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_TEAM_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_TEAM_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_USER_ATTR_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_USER_ATTR_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_USER_DN_TEMPLATE`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_USER_DN_TEMPLATE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_USER_FLAGS_BY_GROUP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_USER_FLAGS_BY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_2_USER_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_USER_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_BIND_DN`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_BIND_DN': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_CONNECTION_OPTIONS`
**Source value:** `{'OPT_REFERRALS': 0, 'OPT_NETWORK_TIMEOUT': 30}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_CONNECTION_OPTIONS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_DENY_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_DENY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_GROUP_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_GROUP_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_GROUP_TYPE`
**Source value:** `MemberDNGroupType`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_GROUP_TYPE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_GROUP_TYPE_PARAMS`
**Source value:** `{'member_attr': 'member', 'name_attr': 'cn'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_GROUP_TYPE_PARAMS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_ORGANIZATION_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_ORGANIZATION_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_REQUIRE_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_REQUIRE_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_SERVER_URI`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_SERVER_URI': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_START_TLS`
**Source value:** `False`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_START_TLS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_TEAM_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_TEAM_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_USER_ATTR_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_USER_ATTR_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_USER_DN_TEMPLATE`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_USER_DN_TEMPLATE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_USER_FLAGS_BY_GROUP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_USER_FLAGS_BY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_3_USER_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_USER_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_BIND_DN`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_BIND_DN': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_CONNECTION_OPTIONS`
**Source value:** `{'OPT_REFERRALS': 0, 'OPT_NETWORK_TIMEOUT': 30}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_CONNECTION_OPTIONS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_DENY_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_DENY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_GROUP_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_GROUP_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_GROUP_TYPE`
**Source value:** `MemberDNGroupType`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_GROUP_TYPE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_GROUP_TYPE_PARAMS`
**Source value:** `{'member_attr': 'member', 'name_attr': 'cn'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_GROUP_TYPE_PARAMS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_ORGANIZATION_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_ORGANIZATION_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_REQUIRE_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_REQUIRE_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_SERVER_URI`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_SERVER_URI': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_START_TLS`
**Source value:** `False`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_START_TLS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_TEAM_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_TEAM_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_USER_ATTR_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_USER_ATTR_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_USER_DN_TEMPLATE`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_USER_DN_TEMPLATE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_USER_FLAGS_BY_GROUP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_USER_FLAGS_BY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_4_USER_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_USER_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_BIND_DN`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_BIND_DN': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_CONNECTION_OPTIONS`
**Source value:** `{'OPT_REFERRALS': 0, 'OPT_NETWORK_TIMEOUT': 30}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_CONNECTION_OPTIONS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_DENY_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_DENY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_GROUP_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_GROUP_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_GROUP_TYPE`
**Source value:** `MemberDNGroupType`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_GROUP_TYPE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_GROUP_TYPE_PARAMS`
**Source value:** `{'member_attr': 'member', 'name_attr': 'cn'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_GROUP_TYPE_PARAMS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_ORGANIZATION_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_ORGANIZATION_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_REQUIRE_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_REQUIRE_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_SERVER_URI`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_SERVER_URI': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_START_TLS`
**Source value:** `False`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_START_TLS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_TEAM_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_TEAM_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_USER_ATTR_MAP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_USER_ATTR_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_USER_DN_TEMPLATE`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_USER_DN_TEMPLATE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_USER_FLAGS_BY_GROUP`
**Source value:** `{}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_USER_FLAGS_BY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_5_USER_SEARCH`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_USER_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_BIND_DN`
**Source value:** `cn=ansible-svc,ou=ServiceAccounts,dc=example,dc=com`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_BIND_DN': 'NEW_VALUE'}'
```

### `AUTH_LDAP_CONNECTION_OPTIONS`
**Source value:** `{'OPT_REFERRALS': 0, 'OPT_NETWORK_TIMEOUT': 30}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_CONNECTION_OPTIONS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_DENY_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_DENY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_GROUP_SEARCH`
**Source value:** `['ou=Groups,dc=example,dc=com', 'SCOPE_SUBTREE', '(objectClass=group)']`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_GROUP_SEARCH': 'NEW_VALUE'}'
```

### `AUTH_LDAP_GROUP_TYPE`
**Source value:** `MemberDNGroupType`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_GROUP_TYPE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_GROUP_TYPE_PARAMS`
**Source value:** `{'member_attr': 'member', 'name_attr': 'cn'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_GROUP_TYPE_PARAMS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_ORGANIZATION_MAP`
**Source value:** `{'IT Operations': {'users': 'cn=Operations-Users,ou=Groups,dc=example,dc=com', 'admins': 'cn=Operations-Admins,ou=Groups,dc=example,dc=com', 'remove_users': False, 'remove_admins': False}, 'Global Engineering': {'users': 'cn=Engineering-Users,ou=Groups,dc=example,dc=com', 'admins': 'cn=Engineering-Admins,ou=Groups,dc=example,dc=com', 'remove_users': False, 'remove_admins': False}, 'Security & Compliance': {'users': 'cn=Security-Users,ou=Groups,dc=example,dc=com', 'admins': 'cn=Security-Admins,ou=Groups,dc=example,dc=com', 'remove_users': False, 'remove_admins': False}}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_ORGANIZATION_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_REQUIRE_GROUP`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_REQUIRE_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_SERVER_URI`
**Source value:** `ldap://ldap.example.com:389`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_SERVER_URI': 'NEW_VALUE'}'
```

### `AUTH_LDAP_START_TLS`
**Source value:** `False`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_START_TLS': 'NEW_VALUE'}'
```

### `AUTH_LDAP_TEAM_MAP`
**Source value:** `{'Backend Development': {'users': 'cn=Backend-Developers,ou=Groups,dc=example,dc=com', 'remove': False, 'organization': 'Global Engineering'}, 'Infrastructure Team': {'users': 'cn=Infrastructure-Team,ou=Groups,dc=example,dc=com', 'remove': False, 'organization': 'IT Operations'}, 'Security Operations': {'users': 'cn=Security-Ops,ou=Groups,dc=example,dc=com', 'remove': False, 'organization': 'Security & Compliance'}}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_TEAM_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_USER_ATTR_MAP`
**Source value:** `{'email': 'mail', 'last_name': 'sn', 'first_name': 'givenName'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_USER_ATTR_MAP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_USER_DN_TEMPLATE`
**Source value:** `uid=%(user)s,ou=Users,dc=example,dc=com`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_USER_DN_TEMPLATE': 'NEW_VALUE'}'
```

### `AUTH_LDAP_USER_FLAGS_BY_GROUP`
**Source value:** `{'is_superuser': ['cn=AAP-Admins,ou=Groups,dc=example,dc=com'], 'is_system_auditor': ['cn=AAP-Auditors,ou=Groups,dc=example,dc=com']}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_USER_FLAGS_BY_GROUP': 'NEW_VALUE'}'
```

### `AUTH_LDAP_USER_SEARCH`
**Source value:** `['ou=Users,dc=example,dc=com', 'SCOPE_SUBTREE', '(sAMAccountName=%(user)s)']`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_USER_SEARCH': 'NEW_VALUE'}'
```

### `AUTOMATION_ANALYTICS_URL`
**Source value:** `https://cloud.redhat.com/api/ingress/v1/upload`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTOMATION_ANALYTICS_URL': 'NEW_VALUE'}'
```

### `AWX_CLEANUP_PATHS`
**Source value:** `True`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AWX_CLEANUP_PATHS': 'NEW_VALUE'}'
```

### `AWX_ISOLATION_BASE_PATH`
**Source value:** `/tmp`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AWX_ISOLATION_BASE_PATH': 'NEW_VALUE'}'
```

### `AWX_ISOLATION_SHOW_PATHS`
**Source value:** `['/etc/pki/ca-trust:/etc/pki/ca-trust:O', '/usr/share/pki:/usr/share/pki:O']`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AWX_ISOLATION_SHOW_PATHS': 'NEW_VALUE'}'
```

### `AWX_MOUNT_ISOLATED_PATHS_ON_K8S`
**Source value:** `False`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AWX_MOUNT_ISOLATED_PATHS_ON_K8S': 'NEW_VALUE'}'
```

### `BULK_HOST_MAX_CREATE`
**Source value:** `100`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'BULK_HOST_MAX_CREATE': 'NEW_VALUE'}'
```

### `CLEANUP_HOST_METRICS_LAST_TS`
**Source value:** `2026-03-03T00:19:38.596279Z`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'CLEANUP_HOST_METRICS_LAST_TS': 'NEW_VALUE'}'
```

### `CUSTOM_VENV_PATHS`
**Source value:** `[]`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'CUSTOM_VENV_PATHS': 'NEW_VALUE'}'
```

### `HOST_METRIC_SUMMARY_TASK_LAST_TS`
**Source value:** `2026-03-24T12:49:40.621297Z`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'HOST_METRIC_SUMMARY_TASK_LAST_TS': 'NEW_VALUE'}'
```

### `LOG_AGGREGATOR_HOST`
**Source value:** `None`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'LOG_AGGREGATOR_HOST': 'NEW_VALUE'}'
```

### `LOG_AGGREGATOR_MAX_DISK_USAGE_PATH`
**Source value:** `/var/lib/awx`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'LOG_AGGREGATOR_MAX_DISK_USAGE_PATH': 'NEW_VALUE'}'
```

### `NAMED_URL_FORMATS`
**Source value:** `{'execution_environments': '<name>', 'organizations': '<name>', 'teams': '<name>++<organization.name>', 'credential_types': '<name>+<kind>', 'credentials': '<name>++<credential_type.name>+<credential_type.kind>++<organization.name>', 'notification_templates': '<name>++<organization.name>', 'job_templates': '<name>++<organization.name>', 'projects': '<name>++<organization.name>', 'inventories': '<name>++<organization.name>', 'hosts': '<name>++<inventory.name>++<organization.name>', 'groups': '<name>++<inventory.name>++<organization.name>', 'inventory_sources': '<name>++<inventory.name>++<organization.name>', 'instance_groups': '<name>', 'workflow_job_templates': '<name>++<organization.name>', 'workflow_job_template_nodes': '<identifier>++<workflow_job_template.name>++<organization.name>', 'labels': '<name>++<organization.name>', 'applications': '<name>++<organization.name>', 'users': '<username>', 'instances': '<hostname>'}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'NAMED_URL_FORMATS': 'NEW_VALUE'}'
```

### `NAMED_URL_GRAPH_NODES`
**Source value:** `{'execution_environments': {'fields': ['name'], 'adj_list': []}, 'organizations': {'fields': ['name'], 'adj_list': []}, 'teams': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'credential_types': {'fields': ['name', 'kind'], 'adj_list': []}, 'credentials': {'fields': ['name'], 'adj_list': [['credential_type', 'credential_types'], ['organization', 'organizations']]}, 'notification_templates': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'job_templates': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'projects': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'inventories': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'hosts': {'fields': ['name'], 'adj_list': [['inventory', 'inventories']]}, 'groups': {'fields': ['name'], 'adj_list': [['inventory', 'inventories']]}, 'inventory_sources': {'fields': ['name'], 'adj_list': [['inventory', 'inventories']]}, 'instance_groups': {'fields': ['name'], 'adj_list': []}, 'workflow_job_templates': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'workflow_job_template_nodes': {'fields': ['identifier'], 'adj_list': [['workflow_job_template', 'workflow_job_templates']]}, 'labels': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'applications': {'fields': ['name'], 'adj_list': [['organization', 'organizations']]}, 'users': {'fields': ['username'], 'adj_list': []}, 'instances': {'fields': ['hostname'], 'adj_list': []}}`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'NAMED_URL_GRAPH_NODES': 'NEW_VALUE'}'
```

### `RADIUS_SERVER`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'RADIUS_SERVER': 'NEW_VALUE'}'
```

### `REMOTE_HOST_HEADERS`
**Source value:** `['HTTP_X_FORWARDED_FOR']`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'REMOTE_HOST_HEADERS': 'NEW_VALUE'}'
```

### `TACACSPLUS_HOST`
**Source value:** ``

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'TACACSPLUS_HOST': 'NEW_VALUE'}'
```

### `TOWER_URL_BASE`
**Source value:** `https://localhost:8443`

**Action:** Review and update if needed:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'TOWER_URL_BASE': 'NEW_VALUE'}'
```

## 🔒 Sensitive Settings (Manual Input Required)

These settings contain passwords, secrets, or API keys that were redacted:

### `AUTH_LDAP_1_BIND_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_1_BIND_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `AUTH_LDAP_2_BIND_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_2_BIND_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `AUTH_LDAP_3_BIND_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_3_BIND_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `AUTH_LDAP_4_BIND_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_4_BIND_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `AUTH_LDAP_5_BIND_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_5_BIND_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `AUTH_LDAP_BIND_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'AUTH_LDAP_BIND_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `LOCAL_PASSWORD_MIN_DIGITS`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'LOCAL_PASSWORD_MIN_DIGITS': 'YOUR_NEW_VALUE'}'
```

### `LOCAL_PASSWORD_MIN_LENGTH`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'LOCAL_PASSWORD_MIN_LENGTH': 'YOUR_NEW_VALUE'}'
```

### `LOCAL_PASSWORD_MIN_SPECIAL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'LOCAL_PASSWORD_MIN_SPECIAL': 'YOUR_NEW_VALUE'}'
```

### `LOCAL_PASSWORD_MIN_UPPER`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'LOCAL_PASSWORD_MIN_UPPER': 'YOUR_NEW_VALUE'}'
```

### `LOG_AGGREGATOR_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'LOG_AGGREGATOR_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `RADIUS_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'RADIUS_SECRET': 'YOUR_NEW_VALUE'}'
```

### `REDHAT_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'REDHAT_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_AZUREAD_OAUTH2_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_AZUREAD_OAUTH2_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_AZUREAD_OAUTH2_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_AZUREAD_OAUTH2_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_AZUREAD_OAUTH2_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_AZUREAD_OAUTH2_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_AZUREAD_OAUTH2_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_API_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_API_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ENTERPRISE_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ENTERPRISE_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ORG_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ORG_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ORG_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ORG_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ORG_NAME`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ORG_NAME': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ORG_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ORG_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_TEAM_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_TEAM_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_TEAM_ID`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_TEAM_ID': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_TEAM_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_TEAM_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_TEAM_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_TEAM_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_TEAM_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_TEAM_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GOOGLE_OAUTH2_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GOOGLE_OAUTH2_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_OIDC_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_OIDC_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_OIDC_OIDC_ENDPOINT`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_OIDC_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_OIDC_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_OIDC_VERIFY_SSL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_OIDC_VERIFY_SSL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_CALLBACK_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_CALLBACK_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_ENABLED_IDPS`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_ENABLED_IDPS': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_EXTRA_DATA`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_EXTRA_DATA': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_METADATA_URL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_METADATA_URL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_ORGANIZATION_ATTR`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_ORGANIZATION_ATTR': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_ORGANIZATION_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_ORGANIZATION_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_ORG_INFO`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_ORG_INFO': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_SECURITY_CONFIG`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_SECURITY_CONFIG': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_SP_ENTITY_ID`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_SP_ENTITY_ID': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_SP_EXTRA`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_SP_EXTRA': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_SP_PRIVATE_KEY`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_SP_PRIVATE_KEY': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_SP_PUBLIC_CERT`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_SUPPORT_CONTACT`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_SUPPORT_CONTACT': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_TEAM_ATTR`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_TEAM_ATTR': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_TECHNICAL_CONTACT`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_TECHNICAL_CONTACT': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_TEAM_MAP`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_TEAM_MAP': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL': 'YOUR_NEW_VALUE'}'
```

### `SOCIAL_AUTH_USER_FIELDS`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SOCIAL_AUTH_USER_FIELDS': 'YOUR_NEW_VALUE'}'
```

### `SUBSCRIPTIONS_CLIENT_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SUBSCRIPTIONS_CLIENT_SECRET': 'YOUR_NEW_VALUE'}'
```

### `SUBSCRIPTIONS_PASSWORD`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'SUBSCRIPTIONS_PASSWORD': 'YOUR_NEW_VALUE'}'
```

### `TACACSPLUS_SECRET`
**Action:** Provide new value:
```bash
curl -sk -X PATCH -H 'Authorization: Bearer $TOKEN' \
  'https://target-aap/api/v2/settings/all/' \
  -d '{'TACACSPLUS_SECRET': 'YOUR_NEW_VALUE'}'
```

