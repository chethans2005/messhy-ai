/**
 * Mesh Viewer Module
 * Handles Three.js scene setup, rendering, and mesh visualization
 */

class MeshViewer {
  constructor(canvasId = 'meshCanvas') {
    this.canvas = document.getElementById(canvasId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.mesh = null;
    this.controls = null;
    this.autoRotate = false;
    this.animationFrameId = null;
    this.boundingBox = null;

    this.initialize();
  }

  /**
   * Initialize Three.js scene, camera, and renderer
   */
  initialize() {
    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1a1a1a);
    this.scene.fog = new THREE.Fog(0x1a1a1a, 500, 1000);

    // Camera
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 10000);
    this.camera.position.z = 3;

    // Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      preserveDrawingBuffer: true,
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowShadowMap;

    // Lights
    this.setupLights();

    // Handle window resize
    window.addEventListener('resize', () => this.onWindowResize());

    // Start animation loop
    this.animate();
  }

  /**
   * Setup lighting for the scene
   */
  setupLights() {
    // Ambient light for base illumination
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);

    // Directional light 1 (key light)
    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(5, 5, 5);
    directionalLight1.castShadow = true;
    directionalLight1.shadow.camera.left = -10;
    directionalLight1.shadow.camera.right = 10;
    directionalLight1.shadow.camera.top = 10;
    directionalLight1.shadow.camera.bottom = -10;
    directionalLight1.shadow.mapSize.width = 2048;
    directionalLight1.shadow.mapSize.height = 2048;
    this.scene.add(directionalLight1);

    // Directional light 2 (fill light)
    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight2.position.set(-5, 3, -5);
    this.scene.add(directionalLight2);

    // Point light for additional highlights
    const pointLight = new THREE.PointLight(0xffffff, 0.3);
    pointLight.position.set(-5, 5, 5);
    this.scene.add(pointLight);
  }

  /**
   * Load and display a GLB mesh file from blob
   * @param {Blob} blob - The GLB file blob
   */
  async loadMeshFromBlob(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const arrayBuffer = e.target.result;
          this.loadMeshFromArrayBuffer(arrayBuffer);
          resolve();
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsArrayBuffer(blob);
    });
  }

  /**
   * Load mesh from ArrayBuffer using GLTFLoader
   * @param {ArrayBuffer} arrayBuffer - GLB file data
   */
  loadMeshFromArrayBuffer(arrayBuffer) {
    // Remove existing mesh
    if (this.mesh) {
      this.scene.remove(this.mesh);
      this.disposeMesh(this.mesh);
    }

    // Create GLTFLoader
    const loader = new THREE.GLTFLoader();

    // Load from ArrayBuffer
    loader.parse(
      arrayBuffer,
      '',
      (gltf) => {
        this.mesh = gltf.scene;

        // Set up shadows
        this.mesh.traverse((node) => {
          if (node instanceof THREE.Mesh) {
            node.castShadow = true;
            node.receiveShadow = true;

            // Set material properties for better rendering
            if (node.material) {
              if (Array.isArray(node.material)) {
                node.material.forEach((mat) => {
                  this.configureMaterial(mat);
                });
              } else {
                this.configureMaterial(node.material);
              }
            }
          }
        });

        this.scene.add(this.mesh);
        this.fitCameraToObject();
      },
      (error) => {
        console.error('Error loading mesh:', error);
        throw new Error('Failed to load mesh: ' + error.message);
      }
    );
  }

  /**
   * Configure material properties for better rendering
   * @param {THREE.Material} material
   */
  configureMaterial(material) {
    material.side = THREE.DoubleSide;
    if (material.roughness !== undefined) {
      material.roughness = 0.7;
    }
    if (material.metalness !== undefined) {
      material.metalness = 0.2;
    }
  }

  /**
   * Fit camera to show entire mesh
   */
  fitCameraToObject() {
    if (!this.mesh) return;

    const box = new THREE.Box3().setFromObject(this.mesh);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = this.camera.fov * (Math.PI / 180); // Convert vertical FOV to radians
    let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));

    cameraZ *= 1.5; // Add a bit of padding

    this.camera.position.z = cameraZ;
    this.camera.lookAt(box.getCenter(new THREE.Vector3()));

    // Update controls target if using orbit controls
    if (this.controls) {
      this.controls.target.copy(box.getCenter(new THREE.Vector3()));
      this.controls.autoRotateSpeed = 5;
      this.controls.update();
    }

    // Store camera settings for reset
    this.initialCameraPosition = this.camera.position.clone();
    this.initialCameraTarget = box.getCenter(new THREE.Vector3());
  }

  /**
   * Reset camera to initial position
   */
  resetCamera() {
    if (this.initialCameraPosition) {
      this.camera.position.copy(this.initialCameraPosition);
    }

    if (this.initialCameraTarget) {
      this.camera.lookAt(this.initialCameraTarget);
    }

    if (this.controls) {
      this.controls.target.copy(this.initialCameraTarget);
      this.controls.update();
    }
  }

  /**
   * Toggle auto-rotation
   */
  toggleAutoRotate() {
    this.autoRotate = !this.autoRotate;
    if (this.controls) {
      this.controls.autoRotate = this.autoRotate;
    }
    return this.autoRotate;
  }

  /**
   * Set auto-rotation state
   * @param {boolean} state
   */
  setAutoRotate(state) {
    this.autoRotate = state;
    if (this.controls) {
      this.controls.autoRotate = state;
    }
  }

  /**
   * Main animation loop
   */
  animate = () => {
    this.animationFrameId = requestAnimationFrame(this.animate);

    if (this.controls) {
      this.controls.update();
    }

    this.renderer.render(this.scene, this.camera);
  };

  /**
   * Handle window resize
   */
  onWindowResize() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  /**
   * Dispose of mesh resources
   * @param {THREE.Object3D} object
   */
  disposeMesh(object) {
    object.traverse((node) => {
      if (node instanceof THREE.Mesh) {
        if (node.geometry) {
          node.geometry.dispose();
        }
        if (node.material) {
          if (Array.isArray(node.material)) {
            node.material.forEach((mat) => mat.dispose());
          } else {
            node.material.dispose();
          }
        }
      }
    });
  }

  /**
   * Clear the scene
   */
  clear() {
    if (this.mesh) {
      this.scene.remove(this.mesh);
      this.disposeMesh(this.mesh);
      this.mesh = null;
    }
  }

  /**
   * Cleanup and destroy viewer
   */
  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }

    this.clear();

    if (this.renderer) {
      this.renderer.dispose();
    }

    window.removeEventListener('resize', () => this.onWindowResize());
  }

  /**
   * Check if a mesh is currently loaded
   * @returns {boolean}
   */
  hasMesh() {
    return this.mesh !== null;
  }

  /**
   * Get mesh bounding box
   * @returns {THREE.Box3|null}
   */
  getMeshBounds() {
    if (!this.mesh) return null;
    return new THREE.Box3().setFromObject(this.mesh);
  }
}

// Global instance
const meshViewer = new MeshViewer();
