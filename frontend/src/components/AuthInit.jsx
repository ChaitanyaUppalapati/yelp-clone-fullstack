// components/AuthInit.jsx — validates a stored token on app mount by dispatching
// fetchCurrentUser. Skips the fetch when loginUser has already populated the
// user, avoiding a redundant /users/me round-trip right after login.
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCurrentUser } from '../store/authSlice';

export default function AuthInit({ children }) {
  const dispatch = useDispatch();
  const token = useSelector((state) => state.auth.token);
  const user = useSelector((state) => state.auth.user);

  useEffect(() => {
    if (token && !user) {
      dispatch(fetchCurrentUser());
    }
  }, [dispatch, token, user]);

  return children;
}
