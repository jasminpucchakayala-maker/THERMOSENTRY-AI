// C:/Users/jasmi/OneDrive/Desktop/THERMOSENTRY-AI/frontend/src/app/page.tsx
import CesiumWrapper from '@/components/CesiumWrapper';
import { motion } from 'framer-motion';

export default function HomePage() {
  return (
    <section className="relative h-full min-h-[600px] bg-bg-base rounded-lg overflow-hidden">
      {/* Cesium globe */}
      <div className="h-[500px]">
        <CesiumWrapper />
      </div>

      {/* Floating filter panel (glassmorphism) */}
      <div className="absolute top-4 left-4 bg-surface-1/60 backdrop-blur-md rounded-xl p-4 shadow-lg border border-border-muted">
        <h3 className="font-heading text-text-primary text-lg mb-2">Filters</h3>
        <div className="flex flex-col gap-2">
          <label className="flex items-center gap-2">
            <input type="checkbox" className="form-checkbox text-accent-primary" defaultChecked />
            <span className="text-sm">Industrial fire</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" className="form-checkbox text-accent-primary" />
            <span className="text-sm">Vegetation fire</span>
          </label>
        </div>
      </div>

      {/* Bottom‑left legend placeholder */}
      <div className="absolute bottom-4 left-4 bg-surface-1/80 backdrop-blur-sm rounded-md px-3 py-2 text-sm text-text-muted">
        <p>Risk gradient legend →</p>
      </div>

      {/* Bottom‑right live ticker placeholder */}
      <div className="absolute bottom-4 right-4 bg-surface-1/80 backdrop-blur-sm rounded-md px-3 py-2 text-sm text-text-muted animate-pulse">
        New event detected: <span className="font-mono">EVT‑00123</span>
      </div>
    </section>
  );
}
