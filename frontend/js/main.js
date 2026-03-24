/**
 * Main Application Module
 * Orchestrates the entire application flow
 */

class MeshGenerationApp {
  constructor() {
    this.apiClient = apiClient;
    this.uiManager = uiManager;
    this.meshViewer = meshViewer;

    this.initialize();
  }

  /**
   * Initialize the application
   */
  initialize() {
    // Register event callbacks
    window.uiCallbacks = {
      onGenerate: () => this.handleGenerate(),
      onDownload: () => this.handleDownload(),
    };

    // Set initial state
    this.uiManager.reset();

    console.log('Mesh Generation App initialized');
  }

  /**
   * Handle mesh generation request
   */
  async handleGenerate() {
    // Get prompt from UI
    const prompt = this.uiManager.getPrompt();

    // Validate input
    if (!prompt) {
      this.uiManager.showError('Please describe an object to generate.');
      return;
    }

    if (prompt.length > 500) {
      this.uiManager.showError('Prompt must be 500 characters or fewer.');
      return;
    }

    // Reset UI and show loading state
    this.uiManager.reset();
    this.uiManager.showLoading('Starting mesh generation...');

    try {
      // Request mesh generation
      const jobId = await this.apiClient.generateMesh(prompt);
      this.uiManager.setJobId(jobId);

      // Start polling for job status
      this.startStatusPolling(jobId);
    } catch (error) {
      this.uiManager.showError(error.message);
    }
  }

  /**
   * Poll for job status updates
   * @param {string} jobId
   */
  startStatusPolling(jobId) {
    const pollFunction = async () => {
      try {
        const job = await this.apiClient.getJobStatus(jobId);

        // Update status message
        this.uiManager.updateStatus(job.message);

        // Check job status
        if (job.status === 'done') {
          // Job completed successfully
          this.uiManager.clearTimers();
          await this.loadMeshPreview(jobId);
          this.uiManager.showResult();
        } else if (job.status === 'error') {
          // Job failed
          this.uiManager.clearTimers();
          this.uiManager.showError(job.message);
        }
        // If status is 'running', keep polling
      } catch (error) {
        // Network error - continue polling
        console.error('Status check error:', error.message);
        // Keep polling on network errors
      }
    };

    // Set up polling interval
    this.uiManager.setStatusTimer(pollFunction, 2500);
  }

  /**
   * Load and display mesh preview
   * @param {string} jobId
   */
  async loadMeshPreview(jobId) {
    try {
      const blob = await this.apiClient.getMeshBlob(jobId);
      await this.meshViewer.loadMeshFromBlob(blob);
    } catch (error) {
      console.error('Mesh preview loading error:', error.message);
      // Don't show error to user - mesh is still available for download
      // but preview failed
    }
  }

  /**
   * Handle mesh download
   */
  async handleDownload() {
    const jobId = this.uiManager.getJobId();

    if (!jobId) {
      this.uiManager.showError('No mesh available for download.');
      return;
    }

    try {
      // Get a suitable filename
      const prompt = this.uiManager.getPrompt();
      let filename = 'mesh.glb';

      if (prompt && prompt.length > 0) {
        // Create filename from first 30 characters of prompt
        const sanitized = prompt
          .substring(0, 30)
          .replace(/[^a-zA-Z0-9\s]/g, '')
          .trim()
          .replace(/\s+/g, '_');

        if (sanitized) {
          filename = `mesh_${sanitized}.glb`;
        }
      }

      // Trigger download
      await this.apiClient.downloadMesh(jobId, filename);
    } catch (error) {
      this.uiManager.showError(`Download failed: ${error.message}`);
    }
  }

  /**
   * Public method to reset app state
   */
  reset() {
    this.uiManager.reset();
    this.meshViewer.clear();
  }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Create app instance (singleton)
  window.app = new MeshGenerationApp();

  console.log('Application ready');
});

// Handle visibility change (pause/resume rendering)
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    // Optional: pause animation when tab is hidden
  } else {
    // Resume when tab is visible
  }
});

// Handle unload cleanup
window.addEventListener('beforeunload', () => {
  if (window.app && window.app.meshViewer) {
    window.app.meshViewer.destroy();
  }
});
