/**
 * API Client Module
 * Handles all communication with the backend server
 */

class APIClient {
  constructor(baseURL = '/') {
    this.baseURL = baseURL;
    this.currentJobId = null;
  }

  /**
   * Start mesh generation process
   * @param {string} prompt - The text description for mesh generation
   * @returns {Promise<string>} - Job ID
   */
  async generateMesh(prompt) {
    try {
      const response = await fetch(`${this.baseURL}generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to start mesh generation');
      }

      const data = await response.json();
      this.currentJobId = data.job_id;
      return data.job_id;
    } catch (error) {
      throw new Error(`Generation request failed: ${error.message}`);
    }
  }

  /**
   * Check the status of a mesh generation job
   * @param {string} jobId - Job ID to check
   * @returns {Promise<Object>} - Job status object {status, message, output_path}
   */
  async getJobStatus(jobId) {
    try {
      const response = await fetch(`${this.baseURL}status/${jobId}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Job not found');
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Status check failed: ${error.message}`);
    }
  }

  /**
   * Download the generated mesh file
   * @param {string} jobId - Job ID of the completed mesh
   * @param {string} filename - Optional custom filename for download
   */
  async downloadMesh(jobId, filename = 'mesh.glb') {
    try {
      const url = `${this.baseURL}download/${jobId}`;
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      throw new Error(`Download failed: ${error.message}`);
    }
  }

  /**
   * Get mesh file as blob for preview
   * @param {string} jobId - Job ID of the completed mesh
   * @returns {Promise<Blob>} - File blob data
   */
  async getMeshBlob(jobId) {
    try {
      const response = await fetch(`${this.baseURL}download/${jobId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch mesh file');
      }
      return await response.blob();
    } catch (error) {
      throw new Error(`Fetch mesh failed: ${error.message}`);
    }
  }

  /**
   * Cancel the current job (if backend supports it in future)
   * @param {string} jobId - Job ID to cancel
   */
  async cancelJob(jobId) {
    // Reserved for future use if cancel endpoint is added
    this.currentJobId = null;
  }
}

// Export or create global instance
const apiClient = new APIClient();
