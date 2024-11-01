<template>
  <div class="ontology">
    <h2>Ontology Management</h2>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="loading" class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <div v-else-if="ontologyData">
      <pre>{{ JSON.stringify(ontologyData, null, 2) }}</pre>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'OntologyView',
  data() {
    return {
      loading: false
    }
  },
  computed: {
    ...mapGetters({
      ontologyData: 'getOntologyData',
      error: 'getError'
    })
  },
  async created() {
    this.loading = true
    await this.$store.dispatch('fetchOntology')
    this.loading = false
  }
}
</script> 