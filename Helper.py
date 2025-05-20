from PIL import Image
import uvicorn
import matplotlib
matplotlib.use('agg')  # Set non-interactive backend
import matplotlib.pyplot as plt
import os
import cv2
import numpy as np
import face_recognition
import psycopg2
import io
import base64

class FaceDBManager:
    def __init__(self, known_dir="known_faces"):
        self.KNOWN_DIR = known_dir
        os.makedirs(self.KNOWN_DIR, exist_ok=True)
        self.db_config = {
            'host': 'localhost',
            'database': 'face_recognition_system',
            'user': 'postgres', # Assuming default postgres user
            'password': '2486' # User provided password
        }
        self.create_database_and_table()

    def create_database_and_table(self):
        conn = psycopg2.connect(
            host=self.db_config['host'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database='postgres' # Connect to default database to create new one
        )
        cursor = conn.cursor()
        # Check if database exists and create if not
        conn.autocommit = True
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'face_recognition_system'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("CREATE DATABASE face_recognition_system")
        conn.autocommit = False # Turn off autocommit for subsequent operations
        cursor.close()
        conn.close()

        # Reconnect to the new database
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                embedding BYTEA NOT NULL,
                image_path VARCHAR(500),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def serialize_embedding(self, embedding: np.ndarray) -> bytes:
        return embedding.astype(np.float64).tobytes()

    def deserialize_embedding(self, blob: bytes) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float64)

    def save_user_to_db(self, username, embedding, image_path):
        serialized = self.serialize_embedding(embedding)
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        sql = "INSERT INTO users (username, embedding, image_path) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, serialized, image_path))
        conn.commit()
        cursor.close()
        conn.close()

    def load_known_faces(self):
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, embedding FROM users")
        self.known_ids = []
        self.known_names = []
        self.known_encodings = []
        for user_id, username, blob in cursor.fetchall():
            self.known_ids.append(user_id)
            self.known_names.append(username)
            self.known_encodings.append(self.deserialize_embedding(blob))
        cursor.close()
        conn.close()

    def register_user(self, img_np: np.ndarray, username: str, return_image: bool = False):
        boxes = face_recognition.face_locations(img_np, model="hog")
        encs = face_recognition.face_encodings(img_np, boxes)
        if not encs:
            print("No face found in image.")
            return "No face found in image"

        if not hasattr(self, 'known_encodings'):
            self.load_known_faces()

        if self.known_encodings:
            distances = face_recognition.face_distance(self.known_encodings, encs[0])
            if min(distances) < 0.6:
                print("Face already registered.")
                return None

        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        # For psycopg2, we need to use RETURNING clause to get the last inserted id
        # Modify the INSERT query to include RETURNING id
        sql = "INSERT INTO users (username, embedding) VALUES (%s, %s) RETURNING id"
        cursor.execute(sql, (username, self.serialize_embedding(encs[0])))
        user_id = cursor.fetchone()[0]
        conn.commit()

        save_path = os.path.join(
        self.KNOWN_DIR,
        f"Registered_{username}{user_id}.jpg"
    )

        cv2.imwrite(save_path, cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR))

        sql_update = "UPDATE users SET image_path = %s WHERE id = %s"
        cursor.execute(sql_update, (save_path, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        self.load_known_faces()
        print(f"User '{username}' with ID {user_id} registered successfully.")

        img_rgb = img_np.copy()
        for top, right, bottom, left in boxes:
            cv2.rectangle(img_rgb, (left, top), (right, bottom), (0, 255, 0), 2)

        if return_image:
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            _, encoded_img = cv2.imencode('.jpg', img_bgr)
            return encoded_img.tobytes()
        else:
            return None

    def verify_user(self, img_np: np.ndarray, tolerance: float = 0.6, return_image: bool = False):
        if not hasattr(self, 'known_encodings'):
            self.load_known_faces()

        boxes = face_recognition.face_locations(img_np, model="hog")
        encs = face_recognition.face_encodings(img_np, boxes)
        if not encs:
            print("No face found in image.")
            return None

        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        for face_encoding, (top, right, bottom, left) in zip(encs, boxes):
            dists = face_recognition.face_distance(self.known_encodings, face_encoding)
            best_index = np.argmin(dists)
            label = self.known_names[best_index] if dists[best_index] <= tolerance else "Unknown"

            cv2.rectangle(img_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(img_bgr, (left, bottom - 20), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(img_bgr, label, (left + 2, bottom - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            print(f"Match: {label}" if label != "Unknown" else "Unknown face")

        if return_image:
            _, encoded_img = cv2.imencode('.jpg', img_bgr)
            return encoded_img.tobytes()
        else:
            return None

    def list_users(self):
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, image_path, registered_at FROM users")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        users = []
        for row in rows:
            user = {
                "id": row[0],
                "username": row[1],
                "registered_at": row[3].isoformat() if row[3] else None
            }
            if row[2]:  # image_path
                try:
                    with open(row[2], 'rb') as img_file:
                        user['image'] = base64.b64encode(img_file.read()).decode('utf-8')
                except Exception as e:
                    user['image'] = None
                    print(f"Error reading image for user {row[0]}: {e}")
            else:
                user['image'] = None
            users.append(user)
        return users

    
    def delete_user(self, user_id):
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            image_path = result[0]
            if os.path.exists(image_path):
                os.remove(image_path)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"User with ID {user_id} deleted.")
        self.load_known_faces()
