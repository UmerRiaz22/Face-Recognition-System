# Face Recognition System Backend

This is the backend for the Face Recognition System, built with FastAPI and using PostgreSQL for database storage.

## Prerequisites

*   Python 3.10.9
*   PostgreSQL database server

Ensure you have these installed before proceeding.

## Setup

1.  **Clone the repository:**

    ```bash
git clone https://github.com/UmerRiaz22/Face-Recognition-System

```

2.  **Create a virtual environment and activate it:**

    ```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    *Note: A `requirements.txt` file is required with the necessary packages listed. Ensure the following packages are included:
    *   `fastapi`
    *   `uvicorn`
    *   `python-multipart`
    *   `face_recognition`
    *   `opencv-python`
    *   `numpy`
    *   `Pillow`
    *   `psycopg2-binary`
    *   `matplotlib`

4.  **Set up the PostgreSQL database:**

    *   Ensure your PostgreSQL server is running.
    *   The application will attempt to connect to a database named `face_recognition_system` on `localhost` with user `postgres` and password `2486`. You may need to create this database and user or update the connection details in `Helper.py` if your setup is different.

## Running the Backend

1.  **Navigate to the `Backendapis` directory:**

    ```bash
Goes to Cloned Folder
```

2.  **Activate your virtual environment (if not already active):**

    ```bash
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3.  **Run the FastAPI application:**

    ```bash
uvicorn app:app --reload
```

    The application will run on `http://0.0.0.0:8000`.

## API Endpoints

The backend exposes the following endpoints:

*   `POST /register`: Register a new user with a username and face image.
*   `POST /verify`: Verify a user's face against the registered users.
*   `GET /list-users`: List all registered users.
*   `DELETE /delete-user/{user_id}`: Delete a user by their ID.

**Important:** All endpoints require a `secret` form parameter with the value `99tech3344` for authentication.

## Secret Key

The secret key `99tech3344` is used to protect the API endpoints. It is **highly recommended** to use a more secure method for authentication in a production environment.