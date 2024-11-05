<template>
  <div class="ontology">
    <h2>Ontology Management</h2>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="loading" class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <div v-else class="row">
      <div class="col-md-8">
        <div ref="graphContainer" id="ontology-graph"></div>
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
        <!-- Debug info -->
        <div class="card mt-3">
          <div class="card-body">
            <h5 class="card-title">Debug Info</h5>
            <pre>{{ JSON.stringify(ontologyData, null, 2) }}</pre>
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
      loading: true,
      selectedNode: null,
      simulation: null,
      svg: null,
      width: 800,
      height: 600
    }
  },
  computed: {
    ...mapGetters({
      ontologyData: 'getOntologyData',
      error: 'getError'
    })
  },
  async created() {
    try {
      await this.$store.dispatch('fetchOntology');
    } catch (error) {
      console.error('Error in created:', error);
    } finally {
      this.loading = false;
    }
  },
  mounted() {
    window.addEventListener('resize', this.handleResize);
    this.handleResize();
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    handleResize() {
      const container = this.$refs.graphContainer;
      if (container) {
        this.width = container.clientWidth;
        this.height = container.clientHeight || 600;
        if (this.svg) {
          this.svg
            .attr('width', this.width)
            .attr('height', this.height);
          
          if (this.simulation) {
            this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(1).restart();
          }
        }
      }
    },
    initializeGraph() {
      if (!this.ontologyData?.nodes?.length) return;
      
      const container = this.$refs.graphContainer;
      if (!container) return;

      // Clear existing SVG
      d3.select("#ontology-graph svg").remove();

      // Create SVG
      this.svg = d3.select("#ontology-graph")
        .append("svg")
        .attr("width", this.width)
        .attr("height", this.height);

      // Create force simulation
      this.simulation = d3.forceSimulation(this.ontologyData.nodes)
        .force("link", d3.forceLink()
          .id(d => d.id)
          .links(this.ontologyData.relationships))
        .force("charge", d3.forceManyBody().strength(-1000))
        .force("center", d3.forceCenter(this.width / 2, this.height / 2))
        .force("collision", d3.forceCollide().radius(50));

      // Create arrow marker
      this.svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "-0 -5 10 10")
        .attr("refX", 30)
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .append("path")
        .attr("d", "M 0,-5 L 10,0 L 0,5")
        .attr("fill", "#999");

      // Draw links
      const link = this.svg.append("g")
        .selectAll("line")
        .data(this.ontologyData.relationships)
        .join("line")
        .attr("stroke", "#999")
        .attr("stroke-width", 2)
        .attr("marker-end", "url(#arrowhead)");

      // Create node groups
      const node = this.svg.append("g")
        .selectAll("g")
        .data(this.ontologyData.nodes)
        .join("g")
        .call(d3.drag()
          .on("start", this.dragstarted)
          .on("drag", this.dragged)
          .on("end", this.dragended));

      // Add circles to nodes
      node.append("circle")
        .attr("r", 25)
        .attr("fill", "#69b3a2")
        .attr("stroke", "#fff")
        .attr("stroke-width", 2);

      // Add labels to nodes
      node.append("text")
        .text(d => d.name)
        .attr("text-anchor", "middle")
        .attr("dy", ".35em")
        .attr("fill", "#fff");

      // Update positions on simulation tick
      this.simulation.on("tick", () => {
        link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

        node
          .attr("transform", d => `translate(${d.x},${d.y})`);
      });

      // Add click handlers
      node.on("click", (event, d) => {
        event.stopPropagation();
        this.selectedNode = d;
      });

      this.svg.on("click", () => {
        this.selectedNode = null;
      });
    },
    dragstarted(event) {
      if (!event.active) this.simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    },
    dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    },
    dragended(event) {
      if (!event.active) this.simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
  },
  watch: {
    ontologyData: {
      handler(newVal) {
        if (newVal?.nodes?.length && !this.loading) {
          this.$nextTick(() => {
            this.initializeGraph();
          });
        }
      },
      immediate: true,
      deep: true
    }
  }
}
</script>

<style scoped>
#ontology-graph {
  width: 100%;
  height: 600px;
  border: 1px solid #ccc;
  background-color: #f8f9fa;
  overflow: hidden;
}

.node circle {
  cursor: pointer;
}

.node text {
  pointer-events: none;
  font-size: 12px;
}

line {
  stroke-opacity: 0.6;
}
</style> 