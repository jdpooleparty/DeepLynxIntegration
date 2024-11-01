<template>
  <div class="type-mappings">
    <h2>Type Mappings</h2>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="loading" class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <div v-else-if="typeMappings">
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Source Type</th>
              <th>Target Type</th>
              <th>Mapping Rules</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="mapping in typeMappings" :key="mapping.id">
              <td>{{ mapping.sourceType }}</td>
              <td>{{ mapping.targetType }}</td>
              <td>{{ mapping.rules }}</td>
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
  name: 'TypeMappingsView',
  data() {
    return {
      loading: false
    }
  },
  computed: {
    ...mapGetters({
      typeMappings: 'getTypeMappings',
      error: 'getError'
    })
  },
  async created() {
    this.loading = true
    await this.$store.dispatch('fetchTypeMappings')
    this.loading = false
  }
}
</script>
