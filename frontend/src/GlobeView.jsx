import { useEffect, useRef } from 'react'
import * as THREE from 'three'

function createEarthTexture() {
  const canvas = document.createElement('canvas')
  canvas.width = 1024
  canvas.height = 512
  const context = canvas.getContext('2d')
  const gradient = context.createLinearGradient(0, 0, 0, canvas.height)
  gradient.addColorStop(0, '#90c7c0')
  gradient.addColorStop(0.48, '#d7ead9')
  gradient.addColorStop(1, '#6fa8a3')
  context.fillStyle = gradient
  context.fillRect(0, 0, canvas.width, canvas.height)

  context.fillStyle = '#739d78'
  const landMasses = [
    [[80, 128], [170, 92], [244, 126], [222, 200], [165, 238], [110, 205]],
    [[274, 82], [385, 74], [432, 148], [380, 214], [302, 188]],
    [[458, 103], [570, 88], [664, 131], [628, 202], [550, 223], [488, 177]],
    [[707, 76], [846, 102], [937, 168], [885, 224], [774, 196], [718, 146]],
    [[232, 275], [299, 278], [341, 354], [304, 435], [258, 380]],
    [[535, 258], [598, 280], [610, 400], [552, 454], [514, 370]],
    [[796, 282], [904, 290], [942, 352], [872, 392], [797, 359]],
  ]
  landMasses.forEach((points) => {
    context.beginPath()
    points.forEach(([x, y], index) => (index ? context.lineTo(x, y) : context.moveTo(x, y)))
    context.closePath()
    context.fill()
  })

  context.strokeStyle = 'rgba(255, 255, 255, 0.2)'
  context.lineWidth = 2
  for (let latitude = 0; latitude < canvas.height; latitude += 34) {
    context.beginPath()
    context.moveTo(0, latitude)
    context.lineTo(canvas.width, latitude)
    context.stroke()
  }
  return new THREE.CanvasTexture(canvas)
}

function createCloudTexture() {
  const canvas = document.createElement('canvas')
  canvas.width = 1024
  canvas.height = 512
  const context = canvas.getContext('2d')
  context.clearRect(0, 0, canvas.width, canvas.height)
  context.fillStyle = 'rgba(255, 255, 255, 0.58)'
  for (let index = 0; index < 75; index += 1) {
    const x = (index * 157) % canvas.width
    const y = (index * 83) % canvas.height
    context.beginPath()
    context.ellipse(x, y, 22 + (index % 5) * 9, 7 + (index % 3) * 4, 0, 0, Math.PI * 2)
    context.fill()
  }
  return new THREE.CanvasTexture(canvas)
}

function createHeatTexture() {
  const canvas = document.createElement('canvas')
  canvas.width = 128
  canvas.height = 128
  const context = canvas.getContext('2d')
  const gradient = context.createRadialGradient(64, 64, 2, 64, 64, 64)
  gradient.addColorStop(0, 'rgba(255, 255, 244, 1)')
  gradient.addColorStop(0.08, 'rgba(255, 230, 116, 1)')
  gradient.addColorStop(0.22, 'rgba(255, 128, 52, .92)')
  gradient.addColorStop(0.52, 'rgba(236, 65, 48, .44)')
  gradient.addColorStop(1, 'rgba(190, 35, 28, 0)')
  context.fillStyle = gradient
  context.fillRect(0, 0, 128, 128)
  return new THREE.CanvasTexture(canvas)
}

function latLonToVector(lat, lon, radius) {
  const phi = (90 - lat) * (Math.PI / 180)
  const theta = (lon + 180) * (Math.PI / 180)
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  )
}

function GlobeView({ anomalies = [], rotationEnabled, thermalEnabled, satelliteEnabled, orbitalEnabled, cloudsEnabled, dayMode = false, zoomDelta = 0, resetSignal = 0, onMarkerSelect, onMarkerHover }) {
  const mountRef = useRef(null)
  const settingsRef = useRef({ rotationEnabled, thermalEnabled, satelliteEnabled, orbitalEnabled, cloudsEnabled, dayMode, zoomDelta, resetSignal, onMarkerSelect, onMarkerHover })

  useEffect(() => {
    settingsRef.current = { rotationEnabled, thermalEnabled, satelliteEnabled, orbitalEnabled, cloudsEnabled, dayMode, zoomDelta, resetSignal, onMarkerSelect, onMarkerHover }
  }, [rotationEnabled, thermalEnabled, satelliteEnabled, orbitalEnabled, cloudsEnabled, dayMode, zoomDelta, resetSignal, onMarkerSelect, onMarkerHover])

  useEffect(() => {
    const mount = mountRef.current
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100)
    camera.position.set(0, 0.15, 5)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    mount.appendChild(renderer.domElement)

    const ambientLight = new THREE.AmbientLight(settingsRef.current.dayMode ? '#b8d9d2' : '#6d9ca7', settingsRef.current.dayMode ? 2.4 : 1.7)
    const sunLight = new THREE.DirectionalLight('#fff7dc', settingsRef.current.dayMode ? 3.4 : 2.4)
    sunLight.position.set(4, 2, 5)
    scene.add(ambientLight, sunLight)

    const globeGroup = new THREE.Group()
    scene.add(globeGroup)

    const textureLoader = new THREE.TextureLoader()
    const earthMaterial = new THREE.MeshPhongMaterial({
      map: createEarthTexture(),
      normalMap: textureLoader.load('/textures/earth-normal.jpg'),
      specularMap: textureLoader.load('/textures/earth-specular.jpg'),
      specular: '#91b9bb',
      shininess: 18,
    })
    const earth = new THREE.Mesh(new THREE.SphereGeometry(1.38, 96, 96), earthMaterial)
    textureLoader.load('/textures/earth-day.jpg', (texture) => {
      texture.colorSpace = THREE.SRGBColorSpace
      earthMaterial.map = texture
      earthMaterial.needsUpdate = true
    })
    globeGroup.add(earth)

    const atmosphere = new THREE.Mesh(
      new THREE.SphereGeometry(1.44, 64, 64),
      new THREE.MeshBasicMaterial({ color: '#a2dad4', transparent: true, opacity: 0.2, side: THREE.BackSide }),
    )
    globeGroup.add(atmosphere)

    const cloudMaterial = new THREE.MeshLambertMaterial({ map: createCloudTexture(), transparent: true, opacity: 0.52, depthWrite: false })
    const cloudShell = new THREE.Mesh(new THREE.SphereGeometry(1.405, 64, 64), cloudMaterial)
    textureLoader.load('/textures/earth-clouds.png', (texture) => {
      texture.colorSpace = THREE.SRGBColorSpace
      cloudMaterial.map = texture
      cloudMaterial.needsUpdate = true
    })
    globeGroup.add(cloudShell)

    const markerGroup = new THREE.Group()
    const heatTexture = createHeatTexture()
    anomalies.forEach((point, index) => {
      const confidence = Number(point.confidence)
      const intensity = Number.isFinite(confidence) ? Math.min(1, Math.max(0.45, confidence / 100)) : 0.65
      const surfacePoint = latLonToVector(point.latitude, point.longitude, 1.405)
      const surfaceNormal = surfacePoint.clone().normalize()
      const marker = new THREE.Group()
      const patchSize = 0.28 + intensity * 0.18
      const createHeatSprite = (color, opacity, scale) => {
        const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: heatTexture, color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthTest: true, depthWrite: false, sizeAttenuation: true }))
        sprite.scale.set(scale, scale, 1)
        return sprite
      }
      const plume = createHeatSprite('#d9362d', 0.2 * intensity, patchSize * 2.5)
      const patch = createHeatSprite('#ff5032', 0.48 * intensity, patchSize * 1.45)
      const innerPatch = createHeatSprite('#ffb22e', 0.62 * intensity, patchSize * 0.7)
      const core = createHeatSprite('#fff4a8', 0.94, patchSize * 0.24)
      marker.position.copy(surfacePoint.clone().add(surfaceNormal.multiplyScalar(0.018)))
      marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), surfaceNormal)
      plume.position.z = -0.004
      innerPatch.position.z = 0.006
      core.position.z = 0.012
      marker.add(plume, patch, innerPatch, core)
      marker.userData = { plume, patch, innerPatch, core, plumeScale: plume.scale.x, patchScale: patch.scale.x, innerScale: innerPatch.scale.x, coreScale: core.scale.x, phase: index * 0.8, intensity, event: point }
      markerGroup.add(marker)
    })
    globeGroup.add(markerGroup)

    const orbitGroup = new THREE.Group()
    const orbitRadii = [1.76, 1.93, 2.08]
    orbitRadii.forEach((radius, index) => {
      const points = new THREE.EllipseCurve(0, 0, radius, radius * (index === 1 ? 0.92 : 0.82), 0, Math.PI * 2, false, 0).getPoints(160)
      const orbitGeometry = new THREE.BufferGeometry().setFromPoints(points.map(({ x, y }) => new THREE.Vector3(x, y, 0)))
      const orbit = new THREE.Line(
        orbitGeometry,
        new THREE.LineDashedMaterial({ color: index === 1 ? '#efaa6a' : '#28b9cd', transparent: true, opacity: index === 1 ? 0.8 : 0.58, dashSize: 0.075, gapSize: 0.055 }),
      )
      orbit.computeLineDistances()
      orbit.rotation.x = [0.92, 1.18, 0.68][index]
      orbit.rotation.z = [-0.28, 0.24, 0.7][index]
      orbitGroup.add(orbit)
    })
    scene.add(orbitGroup)

    const satelliteMetal = new THREE.MeshStandardMaterial({ color: '#b8c9ce', metalness: 0.82, roughness: 0.25 })
    const satelliteGold = new THREE.MeshStandardMaterial({ color: '#d99a3e', metalness: 0.68, roughness: 0.3 })
    const panelMaterial = new THREE.MeshStandardMaterial({ color: '#1d6492', metalness: 0.45, roughness: 0.35, emissive: '#0b4165', emissiveIntensity: 1.2 })
    const panelGridMaterial = new THREE.LineBasicMaterial({ color: '#59b8d3', transparent: true, opacity: 0.8 })
    const satelliteUnits = []
    const createSatelliteLabel = (name) => {
      const canvas = document.createElement('canvas')
      canvas.width = 280
      canvas.height = 64
      const context = canvas.getContext('2d')
      context.fillStyle = 'rgba(2, 19, 32, .9)'
      context.strokeStyle = '#20b6d1'
      context.lineWidth = 3
      context.roundRect(3, 3, 274, 58, 10)
      context.fill()
      context.stroke()
      context.fillStyle = '#73e7ef'
      context.font = '600 25px IBM Plex Mono, monospace'
      context.fillText(name, 14, 38)
      const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(canvas), transparent: true, depthTest: false }))
      label.scale.set(.34, .08, 1)
      label.position.set(0, .22, 0)
      return label
    }
    const createSatellite = (scale, phase, orbitIndex, name) => {
      const unit = new THREE.Group()
      const bus = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.11, 0.1), satelliteMetal)
      const goldBox = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.07, 0.105), satelliteGold)
      const boom = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.24, 10), satelliteMetal)
      boom.rotation.z = Math.PI / 2
      boom.position.x = 0.18
      const dish = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), satelliteMetal)
      dish.rotation.x = Math.PI
      dish.position.set(0, -0.09, 0)
      unit.add(bus, goldBox, boom, dish, createSatelliteLabel(name))
      ;[-0.3, 0.3].forEach((x) => {
        const panel = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.012, 0.16), panelMaterial)
        panel.position.x = x
        unit.add(panel)
        const grid = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(0.3, 0.014, 0.16)), panelGridMaterial)
        grid.position.copy(panel.position)
        unit.add(grid)
      })
      unit.scale.setScalar(scale)
      unit.userData = { phase, orbitIndex, baseScale: scale, orbitRotation: new THREE.Euler([0.92, 1.18, 0.68][orbitIndex], 0, [-0.28, 0.24, 0.7][orbitIndex]) }
      satelliteUnits.push(unit)
      scene.add(unit)
    }
    createSatellite(1.55, 0.2, 0, 'NOAA-20')
    createSatellite(1.25, 2.25, 1, 'NOAA-21')
    createSatellite(1.12, 4.3, 2, 'SUOMI-NPP')

    const resize = () => {
      const { width, height } = mount.getBoundingClientRect()
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height, false)
    }
    const observer = new ResizeObserver(resize)
    observer.observe(mount)
    resize()

    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2()
    const findMarker = (event) => {
      const bounds = renderer.domElement.getBoundingClientRect()
      pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1
      pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1
      raycaster.setFromCamera(pointer, camera)
      const hit = raycaster.intersectObjects(markerGroup.children, true)[0]
      return hit?.object.parent?.userData?.event || hit?.object.userData?.event || null
    }
    const handlePointerMove = (event) => settingsRef.current.onMarkerHover?.(findMarker(event))
    const handleClick = (event) => {
      const markerEvent = findMarker(event)
      if (markerEvent) settingsRef.current.onMarkerSelect?.(markerEvent)
    }
    renderer.domElement.addEventListener('pointermove', handlePointerMove)
    renderer.domElement.addEventListener('click', handleClick)
    renderer.domElement.style.cursor = 'crosshair'

    let frameId
    let appliedZoom = settingsRef.current.zoomDelta
    let appliedReset = settingsRef.current.resetSignal
    const animate = () => {
      const settings = settingsRef.current
      if (settings.rotationEnabled) globeGroup.rotation.y += 0.0018
      if (settings.zoomDelta !== appliedZoom) {
        camera.position.z = THREE.MathUtils.clamp(5 - settings.zoomDelta, 3.6, 6.3)
        appliedZoom = settings.zoomDelta
      }
      if (settings.resetSignal !== appliedReset) {
        camera.position.z = 5
        globeGroup.rotation.y = 0
        appliedReset = settings.resetSignal
      }
      cloudShell.visible = settings.cloudsEnabled
      markerGroup.visible = settings.thermalEnabled
      orbitGroup.visible = settings.orbitalEnabled
      satelliteUnits.forEach((unit) => { unit.visible = settings.satelliteEnabled })
      markerGroup.children.forEach((marker) => {
        const { plume, patch, innerPatch, core, plumeScale, patchScale, innerScale, coreScale, phase, intensity } = marker.userData
        const pulse = 1 + Math.sin(Date.now() * 0.002 + phase) * 0.06
        plume.scale.setScalar(plumeScale * (1 + Math.sin(Date.now() * 0.0016 + phase) * 0.08))
        patch.scale.setScalar(patchScale * pulse)
        innerPatch.scale.setScalar(innerScale * (1 + Math.sin(Date.now() * 0.0025 + phase) * 0.08))
        core.scale.setScalar(coreScale * (1 + Math.sin(Date.now() * 0.003 + phase) * 0.18))
        patch.material.opacity = (0.5 + Math.sin(Date.now() * 0.002 + phase) * 0.08) * intensity
      })
      if (settings.satelliteEnabled) {
        satelliteUnits.forEach((unit) => {
          const { phase, orbitIndex, orbitRotation } = unit.userData
          const time = Date.now() * (0.00016 + orbitIndex * 0.000035) + phase
          const radius = orbitRadii[orbitIndex]
          const width = radius * (orbitIndex === 1 ? 0.92 : 0.82)
          const orbitalPosition = new THREE.Vector3(Math.cos(time) * radius, Math.sin(time) * width, 0).applyEuler(orbitRotation)
          unit.position.copy(orbitalPosition)
          unit.rotation.y = -time + Math.PI / 2
          unit.rotation.z = Math.sin(time) * 0.12
        })
      }
      renderer.render(scene, camera)
      frameId = requestAnimationFrame(animate)
    }
    animate()

    return () => {
      cancelAnimationFrame(frameId)
      observer.disconnect()
      renderer.domElement.removeEventListener('pointermove', handlePointerMove)
      renderer.domElement.removeEventListener('click', handleClick)
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [anomalies])

  return <div className="globe-stage" ref={mountRef} aria-label="Interactive 3D Earth showing satellite thermal anomalies" />
}

export default GlobeView
