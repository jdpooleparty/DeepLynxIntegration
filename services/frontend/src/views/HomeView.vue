<template>
  <div class="home">
    <h1>Deep Lynx Integration Dashboard</h1>
    <div class="row mt-4">
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Ontology</h5>
            <p class="card-text">Manage and view your Deep Lynx ontology structure.</p>
            <router-link to="/ontology" class="btn btn-primary">View Ontology</router-link>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Data Sources</h5>
            <p class="card-text">Configure and manage your data sources.</p>
            <router-link to="/datasources" class="btn btn-primary">Manage Sources</router-link>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Type Mappings</h5>
            <p class="card-text">Define and manage your data type mappings.</p>
            <router-link to="/typemappings" class="btn btn-primary">View Mappings</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView'
}
</script> 