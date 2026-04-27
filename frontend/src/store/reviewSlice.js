// store/reviewSlice.js — review list + create/update/delete with 202/201 awareness.
//
// createReview.fulfilled branches on HTTP status:
//   - 202 Accepted → backend queued the event via Kafka; we set reviewStatus
//     to 'accepted' and do NOT prepend into `reviews` (consumer persists async).
//   - 201 Created  → synchronous persistence; prepend the returned review.
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';

export const fetchReviews = createAsyncThunk(
  'reviews/fetchByRestaurant',
  async (restaurantId, { rejectWithValue }) => {
    try {
      const res = await api.get(`/reviews/restaurant/${restaurantId}`);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch reviews');
    }
  }
);

export const createReview = createAsyncThunk(
  'reviews/create',
  async (data, { rejectWithValue }) => {
    try {
      const res = await api.post('/reviews/', data);
      return { status: res.status, data: res.data };
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((e) => e.msg).join(', ')
        : detail || 'Failed to submit review';
      return rejectWithValue(msg);
    }
  }
);

export const updateReview = createAsyncThunk(
  'reviews/update',
  async ({ id, data }, { rejectWithValue }) => {
    try {
      const res = await api.put(`/reviews/${id}`, data);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to update review');
    }
  }
);

export const deleteReview = createAsyncThunk(
  'reviews/delete',
  async (id, { rejectWithValue }) => {
    try {
      await api.delete(`/reviews/${id}`);
      return id;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to delete review');
    }
  }
);

const reviewSlice = createSlice({
  name: 'reviews',
  initialState: {
    reviews: [],
    // null | 'pending' | 'accepted' (202 Kafka) | 'created' (201 sync)
    reviewStatus: null,
    loading: false,
    error: null,
  },
  reducers: {
    clearReviewStatus: (state) => { state.reviewStatus = null; },
    clearReviewError: (state) => { state.error = null; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchReviews.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchReviews.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.reviews = payload;
      })
      .addCase(fetchReviews.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      .addCase(createReview.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.reviewStatus = 'pending';
      })
      .addCase(createReview.fulfilled, (state, { payload }) => {
        state.loading = false;
        if (payload.status === 202) {
          state.reviewStatus = 'accepted';
          // Deliberately do NOT prepend — backend persists via Kafka consumer.
        } else {
          state.reviewStatus = 'created';
          if (payload.data) state.reviews = [payload.data, ...state.reviews];
        }
      })
      .addCase(createReview.rejected, (state, { payload }) => {
        state.loading = false;
        state.reviewStatus = null;
        state.error = payload;
      })

      .addCase(updateReview.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(updateReview.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.reviews = state.reviews.map((r) => (r.id === payload.id ? payload : r));
      })
      .addCase(updateReview.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      .addCase(deleteReview.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(deleteReview.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.reviews = state.reviews.filter((r) => r.id !== payload);
      })
      .addCase(deleteReview.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      });
  },
});

export const { clearReviewStatus, clearReviewError } = reviewSlice.actions;
export default reviewSlice.reducer;
