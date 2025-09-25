import firebase_admin
from firebase_admin import credentials, auth, storage
from typing import Optional
import os
from src.app.utils.config import settings
from src.app.utils.exceptions import AuthenticationError, FileProcessingError


class FirebaseService:
    """Firebase authentication and storage service"""
    
    def __init__(self):
        self._app = None
        self._bucket = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialize Firebase app and services"""
        try:
            if not firebase_admin._apps:
                if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    self._app = firebase_admin.initialize_app(cred, {
                        'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                    })
                else:
                    # For development/testing without credentials
                    self._app = firebase_admin.initialize_app()
            else:
                self._app = firebase_admin.get_app()
            
            if settings.FIREBASE_STORAGE_BUCKET:
                self._bucket = storage.bucket(settings.FIREBASE_STORAGE_BUCKET)
        except Exception as e:
            print(f"Firebase initialization warning: {e}")
    
    async def verify_token(self, token: str) -> dict:
        """Verify Firebase ID token"""
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise AuthenticationError(f"Token verification failed: {str(e)}")
    
    async def upload_file(self, file_path: str, destination_path: str) -> str:
        """Upload file to Firebase Storage"""
        try:
            if not self._bucket:
                raise FileProcessingError("Firebase Storage not initialized")
            
            blob = self._bucket.blob(destination_path)
            blob.upload_from_filename(file_path)
            
            # Make the file publicly accessible (for development)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            raise FileProcessingError(f"File upload failed: {str(e)}")
    
    async def download_file(self, file_path: str, destination: str) -> str:
        """Download file from Firebase Storage"""
        try:
            if not self._bucket:
                raise FileProcessingError("Firebase Storage not initialized")
            
            blob = self._bucket.blob(file_path)
            blob.download_to_filename(destination)
            return destination
        except Exception as e:
            raise FileProcessingError(f"File download failed: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Firebase Storage"""
        try:
            if not self._bucket:
                return False
            
            blob = self._bucket.blob(file_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"File deletion failed: {str(e)}")
            return False


# Global Firebase service instance
firebase_service = FirebaseService()