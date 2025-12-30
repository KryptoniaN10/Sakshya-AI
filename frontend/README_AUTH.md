Firebase Auth setup (Advocate login)

1) Install dependency

```bash
cd frontend
npm install firebase
```

2) Add environment variables

Create a file named `.env` at the `frontend` root (Vite expects `VITE_` prefixed vars):

```
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

3) Create advocate user accounts

- In the Firebase Console > Authentication > Users, create email/password accounts for advocates.

4) Development

```bash
cd frontend
npm run dev
```

Notes:
- The app uses `src/firebase.ts` and `src/contexts/AuthContext.tsx`.
- You can expand auth rules or add role checks in the `AuthContext` if you want to restrict to users with an "advocate" role stored in Firestore or custom claims.
