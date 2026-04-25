// store/restaurantSlice.js — restaurant list/detail + search filters
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';

export const fetchRestaurants = createAsyncThunk(
  'restaurants/fetchList',
  async (filters = {}, { rejectWithValue }) => {
    try {
      const params = {};
      if (filters.q) params.q = filters.q;
      if (filters.keyword) params.q = filters.keyword; // SearchBar alias
      if (filters.cuisine) params.cuisine = filters.cuisine;
      if (filters.city) params.city = filters.city;
      if (filters.pricing_tier) params.pricing_tier = filters.pricing_tier;
      const res = await api.get('/restaurants/', { params });
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load restaurants');
    }
  }
);

export const fetchRestaurantById = createAsyncThunk(
  'restaurants/fetchOne',
  async (id, { rejectWithValue }) => {
    try {
      const res = await api.get(`/restaurants/${id}`);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Restaurant not found');
    }
  }
);

export const createRestaurant = createAsyncThunk(
  'restaurants/create',
  async (data, { rejectWithValue }) => {
    try {
      const res = await api.post('/restaurants/', data);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to create restaurant');
    }
  }
);

const restaurantSlice = createSlice({
  name: 'restaurants',
  initialState: {
    restaurants: [],
    currentRestaurant: null,
    searchFilters: { q: '', cuisine: '', city: '', pricing_tier: null },
    loading: false,
    error: null,
  },
  reducers: {
    setSearchFilters: (state, { payload }) => {
      state.searchFilters = { ...state.searchFilters, ...payload };
    },
    clearCurrentRestaurant: (state) => { state.currentRestaurant = null; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurants.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchRestaurants.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.restaurants = payload;
      })
      .addCase(fetchRestaurants.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      })

      .addCase(fetchRestaurantById.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchRestaurantById.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.currentRestaurant = payload;
      })
      .addCase(fetchRestaurantById.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
        state.currentRestaurant = null;
      })

      .addCase(createRestaurant.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(createRestaurant.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.restaurants = [payload, ...state.restaurants];
      })
      .addCase(createRestaurant.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload;
      });
  },
});

export const { setSearchFilters, clearCurrentRestaurant } = restaurantSlice.actions;
export default restaurantSlice.reducer;
