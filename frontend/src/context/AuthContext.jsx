// context/AuthContext.jsx — thin Redux-backed compatibility shim.
//
// Historically this file held an AuthProvider. That's gone; auth lives in the
// Redux `auth` slice now. We keep the `useAuth()` hook so legacy components
// (ChatWidget, etc.) that still import it keep working unchanged.
import { useSelector, useDispatch } from 'react-redux';
import { loginUser, registerUser, logoutUser } from '../store/authSlice';

export function useAuth() {
  const dispatch = useDispatch();
  const { user, isAuthenticated, loading, token } = useSelector((state) => state.auth);

  return {
    user,
    token,
    loading,
    isAuthenticated,
    isOwner: user?.role === 'owner',
    login: (email, password) => dispatch(loginUser({ email, password })).unwrap(),
    signup: (data) => dispatch(registerUser(data)).unwrap(),
    logout: () => dispatch(logoutUser()),
  };
}

// No default export / Provider — `<Provider>` from react-redux handles wiring now.
