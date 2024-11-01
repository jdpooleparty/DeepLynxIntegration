<template>
  <div class="ontology">
    <h2>Ontology Management</h2>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="loading" class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <div v-else class="row">
      <div class="col-md-8">
        <div ref="graphContainer" id="ontology-graph" style="height: 600px; border: 1px solid #ccc;"></div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Selected Node</h5>
            <div v-if="selectedNode">
              <p><strong>Name:</strong> {{ selectedNode.name }}</p>
              <p><strong>Type:</strong> {{ selectedNode.type }}</p>
              <button class="btn btn-primary me-2">Edit</button>
              <button class="btn btn-danger">Delete</button>
            </div>
            <div v-else>
              <p>No node selected</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import * as d3 from 'd3'

export default {
  name: 'OntologyView',
  data() {
    return {
      loading: false,
      selectedNode: null,
      simulation: null,
      svg: null
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
  },
  mounted() {
    this.initializeGraph()
  },
  methods: {
    initializeGraph() {
      if (!this.ontologyData) return

      const container = this.$refs.graphContainer
      const width = container.clientWidth
      const height = container.clientHeight

      // Clear any existing SVG
      d3.select("#ontology-graph svg").remove()

      // Create SVG
      this.svg = d3.select("#ontology-graph")
        .append("svg")
        .attr("width", width)
        .attr("height", height)

      // Create force simulation
      this.simulation = d3.forceSimulation(this.ontologyData.nodes)
        .force("link", d3.forceLink(this.ontologyData.relationships)
          .id(d => d.id)
          .distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))

      // Draw links
      const links = this.svg.append("g")
        .selectAll("line")
        .data(this.ontologyData.relationships)
        .enter()
        .append("line")
        .attr("stroke", "#999")
        .attr("stroke-width", 2)

      // Draw nodes
      const nodes = this.svg.append("g")
        .selectAll("circle")
        .data(this.ontologyData.nodes)
        .enter()
        .append("circle")
        .attr("r", 10)
        .attr("fill", "#69b3a2")
        .call(d3.drag()
          .on("start", this.dragstarted)
          .on("drag", this.dragged)
          .on("end", this.dragended))
        .on("click", (event, d) => {
          this.selectedNode = d
        })

      // Add node labels
      const labels = this.svg.append("g")
        .selectAll("text")
        .data(this.ontologyData.nodes)
        .enter()
        .append("text")
        .text(d => d.name)
        .attr("font-size", "12px")
        .attr("dx", 15)
        .attr("dy", 4)

      // Update positions on each tick
      this.simulation.on("tick", () => {
        links
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y)

        nodes
          .attr("cx", d => d.x)
          .attr("cy", d => d.y)

        labels
          .attr("x", d => d.x)
          .attr("y", d => d.y)
      })
    },
    dragstarted(event) {
      if (!event.active) this.simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    },
    dragged(event) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    },
    dragended(event) {
      if (!event.active) this.simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }
  },
  watch: {
    ontologyData: {
      handler(newVal) {
        if (newVal) {
          this.$nextTick(() => {
            this.initializeGraph()
          })
        }
      },
      deep: true
    }
  }
}
</script>

<style scoped>
#ontology-graph {
  background-color: #fff;
}
</style> 