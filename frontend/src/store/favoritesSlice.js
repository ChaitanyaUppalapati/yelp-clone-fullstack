// store/favoritesSlice.js — user favorites with cross-slice coordination.
//
// Listens to authSlice actions so favorites can't leak across users:
//   - logoutUser.fulfilled        → wipe state
//   - fetchCurrentUser.fulfilled  → if loaded for a different user, wipe
// The `loadedForUserId` marker lets pages skip refetches when data is already
// loaded for the current user (see RestaurantDetailPage).
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';
import { fetchCurrentUser, logoutUser } from './authSlice';

export const fetchFavorites = createAsyncThunk(
  'favorites/fetch',
  async (_, { getState, rejectWithValue }) => {
    const userIdAtStart = getState().auth.user?.id ?? null;
    try {
      const res = await api.get('/favorites/');
      const userIdAtEnd = getState().auth.user?.id ?? null;
      // If logout or user-switch happened mid-flight, drop the response so we
      // don't repopulate favorites for a different (or no) user.
      if (userIdAtStart !== userIdAtEnd) {
        return rejectWithValue('User changed during fetch');
      }
      return { items: res.data, userId: userIdAtEnd };
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load favorites');
    }
  }
);

export const addFavorite = createAsyncThunk(
  'favorites/add',
  async (restaurantId, { rejectWithValue }) => {
    try {
      await api.post(`/favorites/${restaurantId}`);
      return { restaurant_id: restaurantId };
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to add favorite');
    }
  }
);

export const removeFavorite = createAsyncThunk(
  'favorites/remove',
  async (restaurantId, { rejectWithValue }) => {
    try {
      await api.delete(`/favorites/${restaurantId}`);
      return restaurantId;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to remove favorite');
    }
  }
);

const favoritesSlice = createSlice({
  name: 'favorites',
  initialState: {
    favorites: [],
    loading: false,
    error: null,
    loadedForUserId: null,
  },
  reducers: {
    resetFavorites: (state) => {
      state.favorites = [];
      state.error = null;
      state.loadedForUserId = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFavorites.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchFavorites.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.favorites = payload.items;
        state.loadedForUserId = payload.userId;
      })
      .addCase(fetchFavorites.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      .addCase(addFavorite.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(addFavorite.fulfilled, (state, { payload }) => {
        state.loading = false;
        if (!state.favorites.some((f) => f.restaurant_id === payload.restaurant_id)) {
          state.favorites.push(payload);
        }
      })
      .addCase(addFavorite.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      .addCase(removeFavorite.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(removeFavorite.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.favorites = state.favorites.filter((f) => f.restaurant_id !== payload);
      })
      .addCase(removeFavorite.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      // Cross-slice: clear on logout; clear on user-switch refresh
      .addCase(logoutUser.fulfilled, (state) => {
        state.favorites = [];
        state.loading = false;
        state.error = null;
        state.loadedForUserId = null;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, { payload }) => {
        if (state.loadedForUserId && state.loadedForUserId !== payload?.id) {
          state.favorites = [];
          state.loadedForUserId = null;
        }
      });
  },
});

export const { resetFavorites } = favoritesSlice.actions;
export default favoritesSlice.reducer;
