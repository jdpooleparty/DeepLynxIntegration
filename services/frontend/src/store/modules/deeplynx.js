import axios from 'axios';

// Create axios instance with custom config
const api = axios.create({
  baseURL: 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add response interceptor for debugging
api.interceptors.response.use(
  response => {
    console.log('API Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

const state = {
  ontologyData: null,
  dataSources: null,
  typeMappings: null,
  error: null
};

const getters = {
  getOntologyData: state => state.ontologyData,
  getDataSources: state => state.dataSources,
  getTypeMappings: state => state.typeMappings,
  getError: state => state.error
};

const actions = {
  async fetchOntology({ commit }) {
    try {
      console.log('Fetching ontology data...');
      const response = await api.get('/ontology');
      console.log('Raw ontology response:', response);
      
      if (!response.data) {
        throw new Error('No data received from API');
      }

      const formattedData = {
        nodes: Array.isArray(response.data.nodes) ? response.data.nodes : [],
        relationships: Array.isArray(response.data.relationships) ? response.data.relationships : []
      };
      
      console.log('Formatted ontology data:', formattedData);
      commit('setOntologyData', formattedData);
    } catch (error) {
      console.error('Error fetching ontology:', error);
      commit('setError', error.response?.data?.detail || error.message || 'Failed to fetch ontology data');
      throw error;  // Re-throw to handle in component
    }
  },

  async fetchDataSources({ commit }) {
    try {
      console.log('Fetching data sources...');
      const response = await api.get('/datasources');
      console.log('Data sources response:', response);
      commit('setDataSources', response.data);
    } catch (error) {
      console.error('Error fetching data sources:', error);
      commit('setError', error.response?.data?.detail || error.message);
      throw error;
    }
  },

  async fetchTypeMappings({ commit }) {
    try {
      console.log('Fetching type mappings...');
      const response = await api.get('/typemappings');
      console.log('Type mappings response:', response);
      commit('setTypeMappings', response.data);
    } catch (error) {
      console.error('Error fetching type mappings:', error);
      commit('setError', error.response?.data?.detail || error.message);
      throw error;
    }
  }
};

const mutations = {
  setOntologyData(state, data) {
    state.ontologyData = data;
    state.error = null;
  },
  setDataSources(state, data) {
    state.dataSources = data;
    state.error = null;
  },
  setTypeMappings(state, data) {
    state.typeMappings = data;
    state.error = null;
  },
  setError(state, error) {
    state.error = error;
  }
};

export default {
  state,
  getters,
  actions,
  mutations
}; 