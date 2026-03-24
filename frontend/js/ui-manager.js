/**
 * UI Manager Module
 * Handles UI state management and DOM manipulations
 */

class UIManager {
  constructor() {
    this.state = {
      isLoading: false,
      hasError: false,
      hasResult: false,
      jobId: null,
      startTime: null,
      elapsedTimer: null,
      statusTimer: null,
    };

    this.elements = {
      prompt: document.getElementById('prompt'),
      generateBtn: document.getElementById('generateBtn'),
      statusSection: document.getElementById('statusSection'),
      statusMsg: document.getElementById('statusMsg'),
      elapsed: document.getElementById('elapsed'),
      resultSection: document.getElementById('resultSection'),
      downloadBtn: document.getElementById('downloadBtn'),
      errorSection: document.getElementById('errorSection'),
      errorMsg: document.getElementById('errorMsg'),
      retryBtn: document.getElementById('retryBtn'),
      viewerPlaceholder: document.getElementById('viewerPlaceholder'),
      viewerControls: document.getElementById('viewerControls'),
      resetViewBtn: document.getElementById('resetViewBtn'),
      autoRotateBtn: document.getElementById('autoRotateBtn'),
    };

    this.initializeEventListeners();
  }

  /**
   * Initialize all event listeners
   */
  initializeEventListeners() {
    // Generate button
    this.elements.generateBtn.addEventListener('click', () => {
      const callbacks = window.uiCallbacks || {};
      if (callbacks.onGenerate) {
        callbacks.onGenerate();
      }
    });

    // Download button
    this.elements.downloadBtn.addEventListener('click', () => {
      const callbacks = window.uiCallbacks || {};
      if (callbacks.onDownload) {
        callbacks.onDownload();
      }
    });

    // Retry button
    this.elements.retryBtn.addEventListener('click', () => {
      this.clearError();
      this.elements.prompt.focus();
    });

    // Prompt textarea - Ctrl+Enter to submit
    this.elements.prompt.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.elements.generateBtn.click();
      }
    });

    // Viewer controls
    this.elements.resetViewBtn.addEventListener('click', () => {
      meshViewer.resetCamera();
    });

    this.elements.autoRotateBtn.addEventListener('click', () => {
      const isRotating = meshViewer.toggleAutoRotate();
      this.updateAutoRotateBtn(isRotating);
    });

    // Handle window resize
    window.addEventListener('resize', () => {
      this.adjustLayout();
    });
  }

  /**
   * Show loading state
   * @param {string} message - Initial status message
   */
  showLoading(message = 'Initializing...') {
    this.state.isLoading = true;
    this.state.hasResult = false;
    this.state.hasError = false;

    this.hideSection('resultSection');
    this.hideSection('errorSection');
    this.showSection('statusSection');

    this.elements.statusMsg.textContent = message;
    this.elements.elapsed.textContent = '';
    this.elements.generateBtn.disabled = true;

    // Start elapsed timer
    this.state.startTime = Date.now();
    this.updateElapsedTime();
    this.state.elapsedTimer = setInterval(() => this.updateElapsedTime(), 1000);

    // Hide viewer controls and placeholder
    this.hideSection('viewerControls');
  }

  /**
   * Update status message during loading
   * @param {string} message
   */
  updateStatus(message) {
    this.elements.statusMsg.textContent = message;
  }

  /**
   * Update elapsed time display
   */
  updateElapsedTime() {
    const elapsed = Math.floor((Date.now() - this.state.startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;

    if (minutes > 0) {
      this.elements.elapsed.textContent = `${minutes}m ${seconds}s elapsed`;
    } else {
      this.elements.elapsed.textContent = `${seconds}s elapsed`;
    }
  }

  /**
   * Show result state with mesh preview available
   */
  showResult() {
    this.state.isLoading = false;
    this.state.hasResult = true;
    this.state.hasError = false;

    this.clearTimers();
    this.hideSection('statusSection');
    this.hideSection('errorSection');
    this.showSection('resultSection');

    this.elements.generateBtn.disabled = false;

    // Show viewer controls and hide placeholder
    this.showSection('viewerControls');
    this.elements.viewerPlaceholder.classList.add('hidden');

    // Reset auto-rotate button state
    meshViewer.setAutoRotate(false);
    this.updateAutoRotateBtn(false);
  }

  /**
   * Show error state
   * @param {string} errorMessage
   */
  showError(errorMessage) {
    this.state.isLoading = false;
    this.state.hasError = true;

    this.clearTimers();
    this.hideSection('statusSection');
    this.hideSection('resultSection');
    this.showSection('errorSection');

    this.elements.errorMsg.textContent = errorMessage;
    this.elements.generateBtn.disabled = false;

    // Clear mesh viewer
    meshViewer.clear();
    this.elements.viewerPlaceholder.classList.remove('hidden');
    this.hideSection('viewerControls');
  }

  /**
   * Clear error state
   */
  clearError() {
    this.state.hasError = false;
    this.hideSection('errorSection');
    this.elements.errorMsg.textContent = '';
  }

  /**
   * Clear all timers
   */
  clearTimers() {
    if (this.state.elapsedTimer) {
      clearInterval(this.state.elapsedTimer);
      this.state.elapsedTimer = null;
    }

    if (this.state.statusTimer) {
      clearInterval(this.state.statusTimer);
      this.state.statusTimer = null;
    }
  }

  /**
   * Show section by ID
   * @param {string} sectionId
   */
  showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
      section.classList.remove('hidden');
    }
  }

  /**
   * Hide section by ID
   * @param {string} sectionId
   */
  hideSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
      section.classList.add('hidden');
    }
  }

  /**
   * Update auto-rotate button state
   * @param {boolean} isRotating
   */
  updateAutoRotateBtn(isRotating) {
    if (isRotating) {
      this.elements.autoRotateBtn.classList.add('active');
      this.elements.autoRotateBtn.textContent = '⟳ Rotating...';
    } else {
      this.elements.autoRotateBtn.classList.remove('active');
      this.elements.autoRotateBtn.textContent = '⟳ Auto Rotate';
    }
  }

  /**
   * Get prompt value
   * @returns {string}
   */
  getPrompt() {
    return this.elements.prompt.value.trim();
  }

  /**
   * Set prompt value
   * @param {string} value
   */
  setPrompt(value) {
    this.elements.prompt.value = value;
  }

  /**
   * Clear prompt
   */
  clearPrompt() {
    this.elements.prompt.value = '';
  }

  /**
   * Focus prompt textarea
   */
  focusPrompt() {
    this.elements.prompt.focus();
  }

  /**
   * Disable/enable generate button
   * @param {boolean} disabled
   */
  setGenerateButtonDisabled(disabled) {
    this.elements.generateBtn.disabled = disabled;
  }

  /**
   * Set status timer
   * @param {Function} callback
   * @param {number} interval
   */
  setStatusTimer(callback, interval = 2500) {
    if (this.state.statusTimer) {
      clearInterval(this.state.statusTimer);
    }
    this.state.statusTimer = setInterval(callback, interval);
  }

  /**
   * Store job ID
   * @param {string} jobId
   */
  setJobId(jobId) {
    this.state.jobId = jobId;
  }

  /**
   * Get stored job ID
   * @returns {string}
   */
  getJobId() {
    return this.state.jobId;
  }

  /**
   * Check if currently loading
   * @returns {boolean}
   */
  isLoading() {
    return this.state.isLoading;
  }

  /**
   * Check if has result
   * @returns {boolean}
   */
  hasResult() {
    return this.state.hasResult;
  }

  /**
   * Adjust layout for responsive design
   */
  adjustLayout() {
    const width = window.innerWidth;
    const container = document.querySelector('.container');

    if (width < 1024) {
      container.style.flexDirection = 'column';
    } else {
      container.style.flexDirection = 'row';
    }
  }

  /**
   * Reset UI to initial state
   */
  reset() {
    this.state.isLoading = false;
    this.state.hasError = false;
    this.state.hasResult = false;
    this.state.jobId = null;

    this.clearTimers();
    this.clearError();
    this.hideSection('statusSection');
    this.hideSection('resultSection');
    this.elements.generateBtn.disabled = false;
    this.elements.viewerPlaceholder.classList.remove('hidden');
    this.hideSection('viewerControls');

    meshViewer.clear();
  }
}

// Global instance
const uiManager = new UIManager();
