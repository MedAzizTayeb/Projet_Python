from ldap3 import Server, Connection, ALL, MODIFY_ADD, SUBTREE
from ldap3.core.exceptions import LDAPException

LDAP_SERVER = "ldap://192.168.92.128" 
ADMIN_DN = "cn=admin,dc=local"
ADMIN_PWD = "Admin123" 
BASE_DN = "ou=users,dc=local"

class LDAPManager:
    def authenticate(self, user, pwd):
        """Authenticate user against LDAP"""
        # Try different DN formats
        dn_formats = [
            f"uid={user},{BASE_DN}",
            f"cn={user},{BASE_DN}",
            f"uid={user},dc=local",
            f"cn={user},dc=local"
        ]
        
        for dn in dn_formats:
            try:
                conn = Connection(Server(LDAP_SERVER, get_info=ALL), dn, pwd, auto_bind=True)
                if conn.bound:
                    conn.unbind()
                    print(f"✓ Authentication successful with DN: {dn}")
                    return True
            except LDAPException as e:
                continue
        
        print(f"✗ Authentication failed for user: {user}")
        return False
    
    def register_user(self, username, password, email):
        """Register new user in LDAP Active Directory"""
        try:
            # Connect as admin
            conn = Connection(
                Server(LDAP_SERVER, get_info=ALL),
                ADMIN_DN,
                ADMIN_PWD,
                auto_bind=True
            )
            
            # User DN
            user_dn = f"uid={username},{BASE_DN}"
            
            # User attributes
            attrs = {
                'objectClass': ['inetOrgPerson', 'posixAccount', 'top'],
                'uid': username,
                'cn': username,
                'sn': username,
                'mail': email,
                'userPassword': password,  # LDAP will hash this
                'uidNumber': str(self._get_next_uid(conn)),
                'gidNumber': '1000',
                'homeDirectory': f'/home/{username}'
            }
            
            # Add user
            success = conn.add(user_dn, attributes=attrs)
            conn.unbind()
            return success
            
        except LDAPException as e:
            print(f"LDAP Registration Error: {e}")
            return False
    
    def _get_next_uid(self, conn):
        """Get next available UID number"""
        conn.search(BASE_DN, '(objectClass=posixAccount)', attributes=['uidNumber'])
        if conn.entries:
            uids = [int(entry.uidNumber.value) for entry in conn.entries]
            return max(uids) + 1
        return 1000
    
    def user_exists(self, username):
        """Check if user exists in LDAP"""
        try:
            conn = Connection(Server(LDAP_SERVER), ADMIN_DN, ADMIN_PWD, auto_bind=True)
            
            # Search in multiple locations
            search_bases = [BASE_DN, "dc=local"]
            
            for base in search_bases:
                # Try searching by uid
                conn.search(base, f'(uid={username})', search_scope=SUBTREE, attributes=['uid'])
                if len(conn.entries) > 0:
                    conn.unbind()
                    return True
                
                # Try searching by cn
                conn.search(base, f'(cn={username})', search_scope=SUBTREE, attributes=['cn'])
                if len(conn.entries) > 0:
                    conn.unbind()
                    return True
            
            conn.unbind()
            return False
        except Exception as e:
            print(f"Error checking user existence: {e}")
            return False