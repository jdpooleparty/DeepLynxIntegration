import axios from 'axios';

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
  // Ontology actions
  async fetchOntology({ commit }) {
    try {
      const { data } = await axios.get('ontology');
      commit('setOntologyData', data);
    } catch (error) {
      commit('setError', error.message);
    }
  },

  // Data source actions
  async fetchDataSources({ commit }) {
    try {
      const { data } = await axios.get('datasources');
      commit('setDataSources', data);
    } catch (error) {
      commit('setError', error.message);
    }
  },

  // Type mapping actions
  async fetchTypeMappings({ commit }) {
    try {
      const { data } = await axios.get('typemappings');
      commit('setTypeMappings', data);
    } catch (error) {
      commit('setError', error.message);
    }
  }
};

const mutations = {
  setOntologyData(state, data) {
    state.ontologyData = data;
  },
  setDataSources(state, sources) {
    state.dataSources = sources;
  },
  setTypeMappings(state, mappings) {
    state.typeMappings = mappings;
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