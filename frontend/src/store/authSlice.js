// store/authSlice.js — JWT auth state with localStorage persistence.
//
// - Login uses OAuth2PasswordRequestForm (form-urlencoded) to match FastAPI.
// - Register posts JSON.
// - fetchCurrentUser() runs on app mount to validate a stored token.
// - Initial loading=!!storedToken so gated UI (e.g. ProtectedRoute) shows a
//   spinner until the /users/me round-trip resolves on refresh.
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const res = await api.get('/users/me');
      localStorage.setItem('user', JSON.stringify(res.data));
      return res.data;
    } catch {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return rejectWithValue('Session expired');
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      const { access_token } = res.data;
      localStorage.setItem('token', access_token);

      const userRes = await api.get('/users/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      localStorage.setItem('user', JSON.stringify(userRes.data));
      return { token: access_token, user: userRes.data };
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Login failed');
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (data, { rejectWithValue }) => {
    try {
      const res = await api.post('/auth/register', data);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Registration failed');
    }
  }
);

export const logoutUser = createAsyncThunk('auth/logout', async () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
});

const storedToken = localStorage.getItem('token');

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    token: storedToken || null,
    user: null,
    isAuthenticated: false,
    loading: !!storedToken, // wait for fetchCurrentUser on refresh
    error: null,
  },
  reducers: {
    clearError: (state) => { state.error = null; },
    setUser: (state, { payload }) => {
      state.user = payload;
      state.isAuthenticated = !!payload;
      if (payload) {
        localStorage.setItem('user', JSON.stringify(payload));
      } else {
        localStorage.removeItem('user');
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCurrentUser.pending, (state) => { state.loading = true; })
      .addCase(fetchCurrentUser.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.user = payload;
        state.isAuthenticated = true;
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.loading = false;
        state.token = null;
        state.user = null;
        state.isAuthenticated = false;
      })

      .addCase(loginUser.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(loginUser.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.token = payload.token;
        state.user = payload.user;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      .addCase(registerUser.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(registerUser.fulfilled, (state) => { state.loading = false; })
      .addCase(registerUser.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      .addCase(logoutUser.fulfilled, (state) => {
        state.token = null;
        state.user = null;
        state.isAuthenticated = false;
        state.loading = false;
        state.error = null;
      });
  },
});

export const { clearError, setUser } = authSlice.actions;
export default authSlice.reducer;
