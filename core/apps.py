from django.apps import AppConfig
import os
import firebase_admin
from firebase_admin import credentials


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        """
        Initialise the Firebase Admin SDK once when Django starts.
        Requires FIREBASE_CREDENTIALS_PATH in .env pointing to your
        downloaded service account JSON file.
        """

        # Avoid double-initialisation (e.g. during tests or autoreload)
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # In development without a real Firebase project,
                # skip initialisation — notifications will silently no-op.
                pass
