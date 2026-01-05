from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException

LDAP_SERVER = "ldap://192.168.92.128"
ADMIN_DN = "cn=admin,dc=local"
ADMIN_PWD = "Admin123"
BASE_DN = "ou=users,dc=local"

class LDAPManager:
    def authenticate(self, user, pwd):
        """Authenticate user against LDAP Active Directory"""
        dn_formats = [
            f"uid={user},{BASE_DN}",
            f"cn={user},{BASE_DN}",
        ]
        
        for dn in dn_formats:
            try:
                conn = Connection(
                    Server(LDAP_SERVER, get_info=ALL),
                    dn, pwd, auto_bind=True
                )
                if conn.bound:
                    conn.unbind()
                    return True
            except:
                continue
        
        return False
    
    def register_user(self, username, password, email):
        """Register new user in LDAP Active Directory"""
        try:
            conn = Connection(
                Server(LDAP_SERVER, get_info=ALL),
                ADMIN_DN, ADMIN_PWD, auto_bind=True
            )
            
            user_dn = f"uid={username},{BASE_DN}"
            
            attrs = {
                'objectClass': ['inetOrgPerson', 'posixAccount', 'top'],
                'uid': username,
                'cn': username,
                'sn': username,
                'mail': email,
                'userPassword': password,
                'uidNumber': str(self._get_next_uid(conn)),
                'gidNumber': '1000',
                'homeDirectory': f'/home/{username}'
            }
            
            success = conn.add(user_dn, attributes=attrs)
            conn.unbind()
            return success
            
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def _get_next_uid(self, conn):
        """Get next available UID number"""
        conn.search(BASE_DN, '(objectClass=posixAccount)', 
                   attributes=['uidNumber'])
        if conn.entries:
            uids = [int(e.uidNumber.value) for e in conn.entries]
            return max(uids) + 1
        return 1000
    
    def user_exists(self, username):
        """Check if user exists in LDAP"""
        try:
            conn = Connection(
                Server(LDAP_SERVER),
                ADMIN_DN, ADMIN_PWD, auto_bind=True
            )
            
            conn.search(BASE_DN, f'(uid={username})', 
                       search_scope=SUBTREE, attributes=['uid'])
            
            exists = len(conn.entries) > 0
            conn.unbind()
            return exists
        except:
            return False