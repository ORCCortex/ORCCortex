import firebase_admin
from firebase_admin import credentials, auth, storage, firestore
from google.cloud.firestore import SERVER_TIMESTAMP, Query
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
from src.app.utils.config import settings
from src.app.utils.exceptions import AuthenticationError, FileProcessingError


class FirebaseService:
    """Firebase authentication, storage, and database service"""
    
    def __init__(self):
        self._app = None
        self._bucket = None
        self._db = None
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
            
            # Initialize Storage
            if settings.FIREBASE_STORAGE_BUCKET:
                self._bucket = storage.bucket(settings.FIREBASE_STORAGE_BUCKET)
            
            # Initialize Firestore
            if self._app:
                self._db = firestore.client()
                print("Firestore database initialized")
                
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

    # ==================== DATABASE OPERATIONS ====================
    
    async def save_user(self, user_data: Dict[str, Any]) -> str:
        """Save or update user in Firestore"""
        try:
            if not self._db:
                raise FileProcessingError("Firestore not initialized")
            
            user_ref = self._db.collection('users').document(user_data['uid'])
            user_ref.set({
                'uid': user_data['uid'],
                'email': user_data.get('email', ''),
                'display_name': user_data.get('display_name'),
                'created_at': user_data.get('created_at', SERVER_TIMESTAMP),
                'updated_at': SERVER_TIMESTAMP
            }, merge=True)
            
            return user_data['uid']
        except Exception as e:
            raise FileProcessingError(f"Failed to save user: {str(e)}")

    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user by UID from Firestore"""
        try:
            if not self._db:
                return None
            
            user_ref = self._db.collection('users').document(uid)
            doc = user_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Failed to get user: {str(e)}")
            return None

    async def save_problem(self, problem_data: Dict[str, Any]) -> str:
        """Save problem to Firestore"""
        try:
            if not self._db:
                raise FileProcessingError("Firestore not initialized")
            
            problem_ref = self._db.collection('problems').document(problem_data['id'])
            problem_ref.set({
                'id': problem_data['id'],
                'user_id': problem_data['user_id'],
                'original_filename': problem_data['original_filename'],
                'file_path': problem_data['file_path'],
                'extracted_text': problem_data.get('extracted_text'),
                'math_expressions': problem_data.get('math_expressions', []),
                'status': problem_data['status'],
                'created_at': problem_data.get('created_at', SERVER_TIMESTAMP),
                'updated_at': SERVER_TIMESTAMP
            })
            
            return problem_data['id']
        except Exception as e:
            raise FileProcessingError(f"Failed to save problem: {str(e)}")

    async def get_problem(self, problem_id: str) -> Optional[Dict[str, Any]]:
        """Get problem by ID from Firestore"""
        try:
            if not self._db:
                return None
            
            problem_ref = self._db.collection('problems').document(problem_id)
            doc = problem_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Failed to get problem: {str(e)}")
            return None

    async def update_problem(self, problem_id: str, update_data: Dict[str, Any]) -> bool:
        """Update problem in Firestore"""
        try:
            if not self._db:
                return False
            
            problem_ref = self._db.collection('problems').document(problem_id)
            update_data['updated_at'] = SERVER_TIMESTAMP
            problem_ref.update(update_data)
            
            return True
        except Exception as e:
            print(f"Failed to update problem: {str(e)}")
            return False

    async def get_user_problems(self, user_id: str, status: Optional[str] = None, 
                              limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all problems for a user with pagination"""
        try:
            if not self._db:
                return []
            
            query = self._db.collection('problems').where('user_id', '==', user_id)
            
            if status:
                query = query.where('status', '==', status)
            
            query = query.order_by('created_at', direction=Query.DESCENDING)
            query = query.offset(offset).limit(limit)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Failed to get user problems: {str(e)}")
            return []

    async def delete_problem(self, problem_id: str) -> bool:
        """Delete problem from Firestore"""
        try:
            if not self._db:
                return False
            
            problem_ref = self._db.collection('problems').document(problem_id)
            problem_ref.delete()
            
            return True
        except Exception as e:
            print(f"Failed to delete problem: {str(e)}")
            return False

    async def save_solution(self, solution_data: Dict[str, Any]) -> str:
        """Save solution to Firestore"""
        try:
            if not self._db:
                raise FileProcessingError("Firestore not initialized")
            
            solution_ref = self._db.collection('solutions').document(solution_data['id'])
            solution_ref.set({
                'id': solution_data['id'],
                'problem_id': solution_data['problem_id'],
                'user_id': solution_data['user_id'],
                'math_expression': solution_data['math_expression'],
                'solution_steps': solution_data.get('solution_steps'),
                'final_answer': solution_data.get('final_answer'),
                'status': solution_data['status'],
                'error_message': solution_data.get('error_message'),
                'created_at': solution_data.get('created_at', SERVER_TIMESTAMP),
                'updated_at': SERVER_TIMESTAMP
            })
            
            return solution_data['id']
        except Exception as e:
            raise FileProcessingError(f"Failed to save solution: {str(e)}")

    async def get_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """Get solution by ID from Firestore"""
        try:
            if not self._db:
                return None
            
            solution_ref = self._db.collection('solutions').document(solution_id)
            doc = solution_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Failed to get solution: {str(e)}")
            return None

    async def update_solution(self, solution_id: str, update_data: Dict[str, Any]) -> bool:
        """Update solution in Firestore"""
        try:
            if not self._db:
                return False
            
            solution_ref = self._db.collection('solutions').document(solution_id)
            update_data['updated_at'] = SERVER_TIMESTAMP
            solution_ref.update(update_data)
            
            return True
        except Exception as e:
            print(f"Failed to update solution: {str(e)}")
            return False

    async def get_problem_solutions(self, problem_id: str) -> List[Dict[str, Any]]:
        """Get all solutions for a specific problem"""
        try:
            if not self._db:
                return []
            
            query = self._db.collection('solutions').where('problem_id', '==', problem_id)
            query = query.order_by('created_at', direction=Query.DESCENDING)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Failed to get problem solutions: {str(e)}")
            return []


# Global Firebase service instance
firebase_service = FirebaseService()
