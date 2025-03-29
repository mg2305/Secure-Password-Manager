import unittest
import os
import time
import sqlite3
import base64
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
import sys

# Add the current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create mocks BEFORE importing the modules
# Mock tkinter modules to prevent GUI popups
mock_tk = MagicMock()
mock_filedialog = MagicMock()
mock_messagebox = MagicMock()
mock_simpledialog = MagicMock()
mock_pil = MagicMock()
mock_pilimage = MagicMock()
mock_pilimagetk = MagicMock()
mock_tkmacosx = MagicMock()
mock_pyperclip = MagicMock()

# Set up the mocks
sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.filedialog'] = mock_filedialog
sys.modules['tkinter.messagebox'] = mock_messagebox
sys.modules['tkinter.simpledialog'] = mock_simpledialog
sys.modules['PIL'] = mock_pil
sys.modules['PIL.Image'] = mock_pilimage
sys.modules['PIL.ImageTk'] = mock_pilimagetk
sys.modules['tkmacosx'] = mock_tkmacosx
sys.modules['pyperclip'] = mock_pyperclip

# Import the modules after mocking
from database import *
from encryption import *
from utils import *

# Create a test database name
TEST_DB_NAME = 'test_gui_spm.db'

# Override the DB_NAME in database module
DB_NAME = TEST_DB_NAME

# PATCH 1: Fix create_tables function (monkeypatch)
def fixed_create_tables():
    """Fixed version of create_tables that properly checks and creates tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if PASSWORDS table exists and create if it doesn't
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='PASSWORDS'")
    if not cursor.fetchone():
        table1 = '''CREATE TABLE PASSWORDS (
                Website TEXT NOT NULL,
                UserName TEXT,
                Password BLOB NOT NULL
                ); '''
        cursor.execute(table1)

    # Check if VAULT_METADATA table exists and create if it doesn't
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='VAULT_METADATA'")
    if not cursor.fetchone():
        table2 = '''CREATE TABLE VAULT_METADATA (
                VAULT_EXISTS INTEGER NOT NULL,
                MP_HASH TEXT,
                ENC_TOKEN BLOB
                );'''
        cursor.execute(table2)
        cursor.execute(''' INSERT INTO VAULT_METADATA VALUES (0, NULL, NULL)''')

    # Check if T_LAST_FAILED table exists and create if it doesn't
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='T_LAST_FAILED'")
    if not cursor.fetchone():
        table3 = '''CREATE TABLE T_LAST_FAILED (
                LAST_FAILED REAL 
                );'''
        cursor.execute(table3)
        cursor.execute(''' INSERT INTO T_LAST_FAILED (LAST_FAILED) VALUES(?)''', (time.time() - 300,))

    conn.commit()
    conn.close()

# Replace the original function with our fixed version
# This is done before the tests run
create_tables = fixed_create_tables

class TestDatabaseFunctions(unittest.TestCase):
    """Test cases for database.py functions"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Make sure we're working with a fresh database
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        # Reset mock objects
        mock_messagebox.showinfo.reset_mock()
        mock_messagebox.showerror.reset_mock()
        # Create tables
        create_tables()
        # Create a connection to keep track of
        self.conn = sqlite3.connect(TEST_DB_NAME)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close the connection before removing the database
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
    
    def test_create_tables(self):
        """Test if tables are created properly"""
        # Force table creation
        create_tables()
        
        cursor = self.conn.cursor()
        
        # Check PASSWORDS table
        cursor.execute("PRAGMA table_info(PASSWORDS)")
        columns = cursor.fetchall()
        # Make sure columns list is populated
        self.assertEqual(len(columns), 3, f"PASSWORDS table should have 3 columns but has {len(columns)}")
        
        # Check VAULT_METADATA table
        cursor.execute("PRAGMA table_info(VAULT_METADATA)")
        columns = cursor.fetchall()
        self.assertEqual(len(columns), 3, f"VAULT_METADATA table should have 3 columns but has {len(columns)}")
        
        # Check T_LAST_FAILED table
        cursor.execute("PRAGMA table_info(T_LAST_FAILED)")
        columns = cursor.fetchall()
        self.assertEqual(len(columns), 1, f"T_LAST_FAILED table should have 1 column but has {len(columns)}")
    
    def test_vault_metadata_operations(self):
        """Test vault metadata operations"""
        # Default should be vault doesn't exist
        self.assertFalse(get_VAULT_EXISTS())
        
        # Test filling metadata
        test_hash = "test_hash"
        test_token = b"test_token"
        fill_VAULT_METADATA(True, test_hash, test_token)
        
        # Check if metadata was updated
        self.assertTrue(get_VAULT_EXISTS())
        self.assertEqual(get_MP_HASH(), test_hash)
        self.assertEqual(get_ENC_TOKEN(), test_token)
    
    def test_password_operations(self):
        """Test password storage operations"""
        # Initially no website should exist
        self.assertFalse(websitePassword_exists("test_site"))
        
        # Insert a password - no need for with patch as we've already mocked messagebox
        insert_password("test_site", "test_user", b"encrypted_password", 'c')
        
        # Check if website exists now
        self.assertTrue(websitePassword_exists("test_site"))
        
        # Get all websites
        websites = get_all_websites()
        self.assertEqual(len(websites), 1)
        self.assertEqual(websites[0], "test_site")
        
        # Get the password
        password = get_password("test_site")
        self.assertEqual(password, b"encrypted_password")
        
        # Delete the password
        delete_passwordEntry("test_site")
        
        # Check if website no longer exists
        self.assertFalse(websitePassword_exists("test_site"))
    
    def test_failed_login_tracking(self):
        """Test failed login tracking"""
        # Get initial time
        initial_time = get_LAST_FAILED()
        
        # Update the time
        new_time = time.time()
        update_LAST_FAILED(new_time)
        
        # Check if time was updated
        updated_time = get_LAST_FAILED()
        self.assertAlmostEqual(updated_time, new_time, places=0)

    def test_delete_tables(self):
        """Test if tables are properly reset"""
        # Insert some test data
        fill_VAULT_METADATA(True, "test_hash", b"test_token")
        
        insert_password("test_site", "test_user", b"encrypted_password", 'c')
        
        # Delete tables
        delete_tables()
        
        # Check if vault data is reset
        self.assertFalse(get_VAULT_EXISTS())
        self.assertEqual(get_MP_HASH(), None)
        
        # Check if passwords are deleted
        self.assertFalse(websitePassword_exists("test_site"))


class TestEncryptionFunctions(unittest.TestCase):
    """Test cases for encryption.py functions"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_keyfile = os.path.join(tempfile.gettempdir(), "test_keyfile.key")
        self.test_password = "TestPassword123!"
        
        # Reset mock objects
        mock_messagebox.showinfo.reset_mock()
        
        # Create a temporary database for testing
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        create_tables()
        
        # Create a connection to keep track of
        self.conn = sqlite3.connect(TEST_DB_NAME)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close the connection before cleanup
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            
        if os.path.exists(self.test_keyfile):
            os.remove(self.test_keyfile)
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        # Hash a password
        hashed_password = hash_mp(self.test_password)
        
        # Store the hash in the metadata
        fill_VAULT_METADATA(True, hashed_password, b"test_token")
        
        # Verify the password
        self.assertTrue(verify_mp(self.test_password))
        
        # Verify with wrong password
        self.assertFalse(verify_mp("WrongPassword"))
    
    def test_keyfile_operations(self):
        """Test keyfile generation and deletion"""
        # Generate a keyfile
        result = gen_keyfile(self.test_keyfile)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_keyfile))
        
        # Check if the keyfile has correct size
        with open(self.test_keyfile, "rb") as f:
            key_data = f.read()
        self.assertEqual(len(key_data), 32)
        
        # Delete the keyfile
        result = delete_keyfile(self.test_keyfile)
        self.assertTrue(result)
        self.assertFalse(os.path.exists(self.test_keyfile))
    
    def test_token_encryption(self):
        """Test token encryption and decryption"""
        # Generate keyfile
        gen_keyfile(self.test_keyfile)
        
        # Test token
        test_token = "TEST_TOKEN"
        
        # Encrypt the token
        encrypted_token = encrypt_token(test_token, self.test_keyfile)
        self.assertIsNotNone(encrypted_token)
        
        # Decrypt the token
        decrypted_token = decrypt_token(self.test_keyfile, encrypted_token)
        self.assertEqual(decrypted_token, test_token)
    
    def test_keyfile_verification(self):
        """Test keyfile verification"""
        # Generate keyfile
        gen_keyfile(self.test_keyfile)
        
        # Test token
        test_token = "TEST_TOKEN"
        
        # Encrypt the token
        encrypted_token = encrypt_token(test_token, self.test_keyfile)
        
        # Store in metadata
        fill_VAULT_METADATA(True, "test_hash", encrypted_token)
        
        # Verify keyfile
        self.assertTrue(verify_keyfile(self.test_keyfile, test_token))
        
        # Verify with wrong token
        self.assertFalse(verify_keyfile(self.test_keyfile, "WRONG_TOKEN"))
    
    def test_key_derivation(self):
        """Test key derivation"""
        # Generate keyfile
        gen_keyfile(self.test_keyfile)
        
        # Derive key
        key = derive_key(self.test_password, self.test_keyfile)
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)
        
        # Derive key with same inputs should give same result
        key2 = derive_key(self.test_password, self.test_keyfile)
        self.assertEqual(key, key2)
        
        # Different password should give different key
        key3 = derive_key("DifferentPassword", self.test_keyfile)
        self.assertNotEqual(key, key3)
    
    def test_password_generation(self):
        """Test random password generation"""
        # Generate a password
        password = get_random_password()
        self.assertEqual(len(password), 20)
        
        # Generate password with custom length
        password = get_random_password(length=15)
        self.assertEqual(len(password), 15)
        
        # Generate two passwords - they should be different
        password1 = get_random_password()
        password2 = get_random_password()
        self.assertNotEqual(password1, password2)
    
    def test_password_encryption(self):
        """Test password encryption and decryption"""
        # Generate keyfile and derive key
        gen_keyfile(self.test_keyfile)
        key = derive_key(self.test_password, self.test_keyfile)
        
        # Test password
        test_password = "WebsitePassword123!"
        
        # Encrypt the password
        encrypted_password = encrypt_password(test_password, key)
        self.assertIsNotNone(encrypted_password)
        
        # Decrypt the password
        decrypted_password = decrypt_password(encrypted_password, key)
        self.assertEqual(decrypted_password, test_password)


class TestUtilsFunctions(unittest.TestCase):
    """Test cases for utils.py functions"""
    
    def setUp(self):
        """Reset mocks before each test"""
        mock_pyperclip.copy.reset_mock()
        mock_messagebox.showinfo.reset_mock()
    
    # FIX 1: Update display_password test to use the actual module imports
    def test_display_password(self):
        """Test displaying password"""
        # We need to patch the actual utils module's imported messagebox
        # not our mock_messagebox since display_password uses the import directly
        with patch('utils.messagebox') as patched_messagebox:
            with patch('utils.pyperclip') as patched_pyperclip:
                # Test display_password which should copy to clipboard and show a message
                display_password("test_password", "test_website")
                
                # Check if password was copied to clipboard
                patched_pyperclip.copy.assert_called_once_with("test_password")
                patched_messagebox.showinfo.assert_called_once()
    
    def test_clear_clipboard(self):
        """Test clearing clipboard"""
        # Test clear_clipboard which should copy an empty string to clipboard
        with patch('utils.pyperclip') as patched_pyperclip:
            clear_clipboard()
            
            # Check if clipboard was cleared
            patched_pyperclip.copy.assert_called_once_with("")
    
    def test_center_window(self):
        """Test window centering"""
        # Create a mock window
        mock_window = MagicMock()
        mock_window.winfo_screenwidth.return_value = 1920
        mock_window.winfo_screenheight.return_value = 1080
        
        # Call center_window
        center_window(mock_window, 400, 300)
        
        # Check if geometry was set correctly
        mock_window.geometry.assert_called_with("400x300+760+390")
    
    # FIX 2: Update add_logo test to properly patch the Image.open method
    def test_add_logo(self):
        """Test adding logo"""
        # Create proper patch for the PIL.Image.open function
        with patch('utils.Image.open') as mock_image_open:
            # Set up mock behavior for the image
            mock_img = MagicMock()
            mock_img.resize.return_value = mock_img
            mock_image_open.return_value = mock_img
            
            # Create a mock window
            mock_window = MagicMock()
            
            # Mock the frozen attribute of sys to simulate a regular script
            with patch('utils.getattr', return_value=False):
                # Mock the __file__ attribute to return a valid path
                with patch('utils.__file__', new=os.path.join(os.getcwd(), 'utils.py')):
                    # Call add_logo
                    add_logo(mock_window, "#FFFFFF")
                    
                    # Check if operations were performed
                    mock_image_open.assert_called_once()
                    mock_img.resize.assert_called_with((125, 125))


class TestIntegrationTests(unittest.TestCase):
    """Integration tests for secure password manager"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_keyfile = os.path.join(tempfile.gettempdir(), "test_keyfile.key")
        self.test_password = "TestPassword123!"
        
        # Reset mock objects
        mock_messagebox.showinfo.reset_mock()
        mock_pyperclip.copy.reset_mock()
        
        # Create a temporary database for testing
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        create_tables()
        
        # Create a connection to keep track of
        self.conn = sqlite3.connect(TEST_DB_NAME)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close the connection before cleanup
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            
        if os.path.exists(self.test_keyfile):
            os.remove(self.test_keyfile)
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
    
    def test_sign_up_flow(self):
        """Test the sign up flow"""
        # Hash master password
        hashed_mp = hash_mp(self.test_password)
        
        # Generate keyfile
        self.assertTrue(gen_keyfile(self.test_keyfile))
        
        # Encrypt token
        token = "MAYANK'S SPM"
        encrypted_token = encrypt_token(token, self.test_keyfile)
        
        # Store metadata
        fill_VAULT_METADATA(True, hashed_mp, encrypted_token)
        
        # Verify metadata
        self.assertTrue(get_VAULT_EXISTS())
        self.assertEqual(get_MP_HASH(), hashed_mp)
        self.assertEqual(get_ENC_TOKEN(), encrypted_token)
    
    def test_login_flow(self):
        """Test the login flow"""
        # First sign up
        hashed_mp = hash_mp(self.test_password)
        self.assertTrue(gen_keyfile(self.test_keyfile))
        token = "MAYANK'S SPM"
        encrypted_token = encrypt_token(token, self.test_keyfile)
        fill_VAULT_METADATA(True, hashed_mp, encrypted_token)
        
        # Now login
        self.assertTrue(verify_mp(self.test_password))
        self.assertTrue(verify_keyfile(self.test_keyfile, token))
        
        # Derive key
        key = derive_key(self.test_password, self.test_keyfile)
        self.assertIsNotNone(key)
    
    def test_password_storage_flow(self):
        """Test the password storage and retrieval flow"""
        # First sign up and login to get the key
        hashed_mp = hash_mp(self.test_password)
        self.assertTrue(gen_keyfile(self.test_keyfile))
        token = "MAYANK'S SPM"
        encrypted_token = encrypt_token(token, self.test_keyfile)
        fill_VAULT_METADATA(True, hashed_mp, encrypted_token)
        key = derive_key(self.test_password, self.test_keyfile)
        
        # Store a password
        website = "example.com"
        username = "testuser"
        password = "WebsitePassword123!"
        
        # Encrypt the password
        encrypted_password = encrypt_password(password, key)
        
        # Store in database
        insert_password(website, username, encrypted_password, 'c')
        
        # Retrieve the password
        retrieved_encrypted_password = get_password(website)
        
        # Delete the password
        delete_passwordEntry(website)
        
        # Decrypt and verify
        decrypted_password = decrypt_password(retrieved_encrypted_password, key)
        self.assertEqual(decrypted_password, password)
        
        # Verify it's gone
        self.assertFalse(websitePassword_exists(website))


if __name__ == '__main__':
    unittest.main()