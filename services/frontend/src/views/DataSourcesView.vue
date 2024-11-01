<template>
  <div class="datasources">
    <h2>Data Sources</h2>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="loading" class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <div v-else-if="dataSources">
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="source in dataSources" :key="source.id">
              <td>{{ source.name }}</td>
              <td>{{ source.type }}</td>
              <td>{{ source.status }}</td>
              <td>
                <button class="btn btn-sm btn-primary me-2">Edit</button>
                <button class="btn btn-sm btn-danger">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'DataSourcesView',
  data() {
    return {
      loading: false
    }
  },
  computed: {
    ...mapGetters({
      dataSources: 'getDataSources',
      error: 'getError'
    })
  },
  async created() {
    this.loading = true
    await this.$store.dispatch('fetchDataSources')
    this.loading = false
  }
}
</script> 