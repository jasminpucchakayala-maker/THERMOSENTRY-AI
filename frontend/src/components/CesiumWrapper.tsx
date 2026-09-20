// C:/Users/jasmi/OneDrive/Desktop/THERMOSENTRY-AI/frontend/src/components/CesiumWrapper.tsx
import { useEffect, useRef } from 'react';
import { Viewer } from 'cesium';

export default function CesiumWrapper() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      new Viewer(containerRef.current, {
        animation: false,
        timeline: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        navigationHelpButton: false,
        sceneModePicker: false,
        // Add more Cesium options as needed later
      });
    }
  }, []);

  return <div ref={containerRef} className="h-full w-full" />;
}
